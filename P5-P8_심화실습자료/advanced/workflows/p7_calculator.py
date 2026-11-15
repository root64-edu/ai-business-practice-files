"""DART snapshot comparison with explicit scope, uniqueness and units."""
import json
from decimal import Decimal as D, ROUND_HALF_UP
ACCOUNTS=['매출액','영업이익','자산총계','부채총계','자본총계','유동자산','유동부채']
def analyze(records):
    out=[]; identities=set()
    for record in records:
        data=record['data']
        if data.get('status')!='000': raise ValueError('DART 응답 성공 아님: '+str(data.get('status')))
        rows=[r for r in data['list'] if r['fs_div']=='CFS']
        if not rows: raise ValueError('연결재무제표 CFS 자료 없음')
        scopes={(r['corp_code'],r['bsns_year'],r['reprt_code'],r.get('currency'),r['rcept_no']) for r in rows}
        if len(scopes)!=1: raise ValueError('기업·연도·보고서·통화·접수번호 혼합')
        corp,year,report,currency,receipt=next(iter(scopes))
        if (year,report,currency)!=('2025','11011','KRW'): raise ValueError('2025년 연간 원화 비교 조건 불일치')
        if corp in identities: raise ValueError('기업 중복')
        identities.add(corp)
        def val(name,period='thstrm_amount'):
            found=[r for r in rows if r['account_nm']==name]
            if len(found)!=1: raise ValueError(name+' 누락 또는 중복')
            text=found[0].get(period,'').strip().replace(',','')
            if not text: raise ValueError(name+' 금액 누락')
            n=D(text)
            if not n.is_finite(): raise ValueError('유한한 금액 아님')
            return n
        amounts={name:val(name) for name in ACCOUNTS}
        if amounts['자산총계']!=amounts['부채총계']+amounts['자본총계']: raise ValueError('자산 등식 불일치')
        def pct(a,b):
            if b<=0: return None
            return str((a/b*100).quantize(D('.01'),rounding=ROUND_HALF_UP))
        prior_sales=val('매출액','frmtrm_amount')
        out.append({'corp_code':corp,'company':record.get('company',corp),'fs_div':'CFS','year':year,'report_code':report,'currency':currency,'receipt':receipt,'retrieved_at':record.get('retrieved_at'),'source_url':'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='+receipt,'amounts':{k:str(v) for k,v in amounts.items()},'prior_sales':str(prior_sales),'sales_growth_pct':pct(amounts['매출액']-prior_sales,prior_sales),'operating_margin_pct':pct(amounts['영업이익'],amounts['매출액']),'prior_operating_margin_pct':pct(val('영업이익','frmtrm_amount'),prior_sales),'liabilities_to_equity_pct':pct(amounts['부채총계'],amounts['자본총계']),'current_ratio_pct':pct(amounts['유동자산'],amounts['유동부채']),'notes':['분모 0 또는 음수의 비율은 null로 보류','CFS 선택 후 항목별 유일성 검사','당기순이익은 중복 항목을 임의 선택하지 않고 이번 지표에서 제외','API 저장 시점의 수치이며 정정 공시 재확인 필요']})
    if len(out)!=2: raise ValueError('비교 기업 두 곳 필요')
    return out

def main(data_json: str) -> dict:
    try:
        result=analyze(json.loads(data_json))
        return {'status':'계산 완료','report':json.dumps(result,ensure_ascii=False)}
    except (ValueError,KeyError,TypeError,ArithmeticError) as e:
        return {'status':'기준 확인 필요','report':str(e)}
