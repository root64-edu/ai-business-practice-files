"""교육용 순차 거래 검토. 세금·기말평가·정산 뒤 반품은 지원하지 않습니다."""
import json
from decimal import Decimal as D, ROUND_HALF_UP
from datetime import datetime

def calculate(data):
    purchases, sales, returns, settlements, shipping = [data[k] for k in ('purchases','sales','returns','settlements','shipping')]
    rates = {}
    def decimal(v):
        n = D(str(v))
        if not n.is_finite(): raise ValueError('유한한 수치가 아닙니다')
        return n
    def date(v):
        datetime.strptime(v, '%Y%m%d')
        return v
    for r in data['rates']:
        date(r['date'])
        key = (r['date'], r['currency'])
        if key in rates: raise ValueError('환율 식별자 중복')
        expected = {'USD': ('USD',1), 'JPY': ('JPY(100)',100)}
        if r['currency'] not in expected or (r['source_unit'],r['unit']) != expected[r['currency']]:
            raise ValueError('환율 표시 통화와 단위 불일치')
        value = decimal(r['rate'])
        if value <= 0: raise ValueError('환율은 양수여야 합니다')
        rates[key] = value / decimal(r['unit'])
    def rate(day, cur):
        if cur == 'KRW': return D(1)
        if (day,cur) not in rates: raise ValueError('해당 날짜·통화의 환율 없음')
        return rates[(day,cur)]
    def won(x): return D(x).quantize(D(1),rounding=ROUND_HALF_UP)
    for rows, key in [(purchases,'batch_id'),(sales,'sale_id'),(returns,'return_id'),(settlements,'settlement_id'),(shipping,'sale_id')]:
        ids = [r[key] for r in rows]
        if any(not isinstance(x,str) or not x for x in ids) or len(ids) != len(set(ids)):
            raise ValueError('거래 식별자 누락 또는 중복: '+key)
        for r in rows: date(r['date'])
    batches_input = {r['batch_id']:r for r in purchases}
    sales_input = {r['sale_id']:r for r in sales}
    for rows in (purchases,sales,returns):
        for r in rows:
            q=decimal(r['quantity'])
            if q<=0 or q!=q.to_integral_value(): raise ValueError('수량은 양의 정수여야 합니다')
    for rows in (purchases,sales):
        for r in rows:
            if r['currency'] not in ('KRW','USD','JPY'): raise ValueError('필수 통화 누락 또는 지원하지 않는 통화')
            if decimal(r['unit_price'])<0: raise ValueError('단가 음수')
            rate(r['date'],r['currency'])
    for p in purchases:
        if decimal(p['inbound_krw'])<0: raise ValueError('매입 운임 음수')
    sold={}; returned={}
    for r in sales:
        if r['batch_id'] not in batches_input: raise ValueError('참조하는 매입 배치 없음')
        b=batches_input[r['batch_id']]
        if r['date']<b['date']: raise ValueError('입고 전 판매')
        sold[r['batch_id']]=sold.get(r['batch_id'],D(0))+decimal(r['quantity'])
        if sold[r['batch_id']]>decimal(b['quantity']): raise ValueError('매입 배치 재고 초과')
    for r in returns:
        if r['sale_id'] not in sales_input: raise ValueError('반품의 원판매 없음')
        sale=sales_input[r['sale_id']]
        if r['date']<sale['date']: raise ValueError('판매 전 반품')
        if r['restock'] is not True: raise ValueError('재입고 불가 반품은 별도 검토')
        returned[r['sale_id']]=returned.get(r['sale_id'],D(0))+decimal(r['quantity'])
        if returned[r['sale_id']]>decimal(sale['quantity']): raise ValueError('원판매 수량 초과 반품')
    paid={}
    for t in settlements:
        if t['kind'] not in ('지급','수취'): raise ValueError('정산 구분 오류')
        source=batches_input if t['kind']=='지급' else sales_input
        if t['reference'] not in source: raise ValueError('정산의 원거래 없음')
        original=source[t['reference']]
        if t['date']<original['date']: raise ValueError('원거래 전 정산')
        if t['kind']=='수취' and any(r['sale_id']==t['reference'] and r['date']>t['date'] for r in returns):
            raise ValueError('정산 뒤 반품은 별도 처리 필요')
        amount=decimal(t['amount']); fee=decimal(t['fee_krw'])
        if amount<=0 or fee<0: raise ValueError('정산 금액 또는 수수료 오류')
        rate(t['date'],original['currency'])
        limit=(decimal(original['quantity'])-(returned.get(t['reference'],D(0)) if t['kind']=='수취' else 0))*decimal(original['unit_price'])
        key=(t['kind'],t['reference']);paid[key]=paid.get(key,D(0))+amount
        if paid[key]>limit: raise ValueError('미결제 외화 잔액 초과')
    for r in shipping:
        if r['sale_id'] not in sales_input or decimal(r['outbound_krw'])<0: raise ValueError('판매 운임 참조 또는 금액 오류')
    journal=[]
    def entry(ref,date,lines):
     assert sum(v for _,v in lines)==0,(ref,lines)
     for account,amount in lines:
      if amount:journal.append({'reference':ref,'date':date,'account':account,'debit':str(max(amount,D(0))),'credit':str(max(-amount,D(0)))})
    batches={};transactions={}
    for p in purchases:
     q=D(p['quantity']);goods=won(q*D(p['unit_price'])*rate(p['date'],p['currency']));freight=D(p['inbound_krw']);cost=goods+freight
     batches[p['batch_id']]={**p,'goods_krw':goods,'total_cost':cost,'unit_cost':cost/q,'remaining_quantity':q,'cost_released':D(0),'payable_foreign':q*D(p['unit_price']),'payable_krw':goods}
     entry(p['batch_id'],p['date'],[('재고자산',cost),('매입채무',-goods),('현금',-freight)])
    for s in sales:
     b=batches[s['batch_id']];q=D(s['quantity']);amt=q*D(s['unit_price']);revenue=won(amt*rate(s['date'],s['currency']));cost=won(b['unit_cost']*q)
     b['remaining_quantity']-=q;b['cost_released']+=cost
     transactions[s['sale_id']]={**s,'revenue_krw':revenue,'cost_krw':cost,'receivable_foreign':amt,'receivable_krw':revenue,'returned':D(0)}
     entry(s['sale_id'],s['date'],[('매출채권',revenue),('매출',-revenue),('매출원가',cost),('재고자산',-cost)])
    for r in returns:
     s=transactions[r['sale_id']];b=batches[s['batch_id']];q=D(r['quantity']);amt=q*D(s['unit_price']);refund=won(amt*rate(s['date'],s['currency']));cost=won(b['unit_cost']*q)
     s['receivable_foreign']-=amt;s['receivable_krw']-=refund;s['returned']+=q;s['revenue_krw']-=refund;s['cost_krw']-=cost
     b['remaining_quantity']+=q;b['cost_released']-=cost
     entry(r['return_id'],r['date'],[('매출',refund),('매출채권',-refund),('재고자산',cost),('매출원가',-cost)])
    settled=[]
    for t in settlements:
     payable=t['kind']=='지급';ref=(batches if payable else transactions)[t['reference']];amount=D(t['amount']);field='payable' if payable else 'receivable';assert 0<amount<=ref[field+'_foreign']
     original=ref[field+'_krw'] if amount==ref[field+'_foreign'] else won(amount*rate(ref['date'],ref['currency']));cash=won(amount*rate(t['date'],ref['currency']));fee=D(t['fee_krw'])
     ref[field+'_foreign']-=amount;ref[field+'_krw']-=original
     # Gains are credit balances. Positive gain for cheaper settlement of payable.
     gain=original-cash if payable else cash-original
     lines=[('매입채무',original),('현금',-cash-fee),('외환차익',-gain),('지급수수료',fee)] if payable else [('현금',cash-fee),('매출채권',-original),('외환차익',-gain),('지급수수료',fee)]
     # Negative gain is recorded explicitly as an exchange loss.
     lines=[('외환차손',v) if a=='외환차익' and v>0 else (a,v) for a,v in lines]
     entry(t['settlement_id'],t['date'],lines);settled.append({**t,'currency':ref['currency'],'carrying_krw':str(original),'cash_before_fee':str(cash),'fx_gain_signed':str(gain)})
    for s in shipping:entry('SHIP_'+s['sale_id'],s['date'],[('판매운임',D(s['outbound_krw'])),('현금',-D(s['outbound_krw']))])
    balances={}
    for j in journal:balances[j['account']]=balances.get(j['account'],D(0))+D(j['debit'])-D(j['credit'])
    assert sum(balances.values())==0
    assert balances['재고자산']==sum(b['total_cost']-b['cost_released'] for b in batches.values())
    assert balances['매출채권']==sum(s['receivable_krw'] for s in transactions.values())
    assert -balances['매입채무']==sum(b['payable_krw'] for b in batches.values())
    summary={'data_kind':'매입·판매·반품·정산은 모두 가상 교육 데이터. 환율은 실제 API 조회 스냅숏.','assumptions':['수량·단가는 가상이며 모든 거래는 단기 실습 기간 안에서 발생한 것으로 설정','재고 입고일에 매입 인식, 고객 인도일에 매출 인식한 것으로 주어진 조건','매입 운임은 해당 배치 재고원가, 판매 운임과 송금·수취 수수료는 별도 비용','세금·관세는 이번 계산 범위에서 제외하며 면제 또는 세율 0을 의미하지 않음','결제 환율도 비교 학습을 위해 조회 매매기준율로 대체. 실제 은행 적용환율·회계환율과 같다는 뜻이 아님','기간말 외화채권·채무 재평가 이전의 거래·정산 검토표이며 결산 재무제표가 아님','반품은 최초 매출의 환산액과 배치원가를 되돌리고, 같은 상태로 재입고되는 것으로 가정','원 단위 반올림은 각 전표 금액에 적용. 남은 재고는 총원가에서 반영 원가를 차감해 잔여 오차 보존'], 'purchases':list(batches.values()),'sales':list(transactions.values()),'settlements':settled,'balances_debit_positive':balances,'net_sales':-balances['매출'],'cost_of_sales':balances['매출원가'],'gross_profit':-balances['매출']-balances['매출원가'],'inventory_quantity':sum(b['remaining_quantity'] for b in batches.values()),'inventory_value':balances['재고자산'],'receivables':balances['매출채권'],'payables':-balances['매입채무'],'net_cash_change':balances['현금'],'trial_balance_difference':sum(balances.values())}
    return summary, journal

def main(data_json: str) -> dict:
    try:
        result, journal=calculate(json.loads(data_json))
        view={k:result[k] for k in ['net_sales','cost_of_sales','gross_profit','inventory_quantity','inventory_value','receivables','payables','net_cash_change','assumptions']}
        balances=result['balances_debit_positive']
        view.update(fx_gain=-balances.get('외환차익',D(0)),fx_loss=balances.get('외환차손',D(0)),fees=balances.get('지급수수료',D(0)),outbound_shipping=balances.get('판매운임',D(0)),display_note='fx_gain은 양수 이익 금액. 수수료·판매운임은 매출총이익에 포함되지 않은 별도 비용이며 영업외로 일괄 분류하지 않음')
        return {'status':'계산 완료','report':json.dumps(result,ensure_ascii=False,default=str),
                'journal':json.dumps(journal,ensure_ascii=False),'llm_report':json.dumps(view,ensure_ascii=False,default=str)}
    except (ValueError,KeyError,TypeError,ArithmeticError,AssertionError) as e:
        return {'status':'입력 확인 필요','report':str(e) or '계산 검증 실패','journal':'[]','llm_report':str(e) or '계산 검증 실패'}
