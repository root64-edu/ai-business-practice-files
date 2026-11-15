"""Fictional quote sensitivity exercise; not a forecast or accounting closing."""
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
import json,argparse,itertools
ROOT=Path(__file__).resolve().parents[1]
def won(value):return D(value).quantize(D('1'),rounding=ROUND_HALF_UP)
def compare(data):
 rows=[]
 for quote,sold,multiplier in itertools.product(data['quotes'],data['sales_quantities'],data['fx_multipliers']):
  row={'quote_id':quote['id'],'sold_quantity':sold,'fx_multiplier':multiplier}
  if sold>quote['quantity']:
   rows.append(dict(row,status='수량 조건 불충족',reason='판매 수량이 구매 수량을 초과합니다.'));continue
  rate=D(data['rates'][quote['currency']])*D(multiplier)
  goods=won(D(quote['quantity'])*D(quote['unit_price'])*rate)
  cost=goods+D(quote['inbound_krw']);unit=cost/D(quote['quantity']);cogs=won(unit*D(sold))
  revenue=D(sold)*D(data['sale_price_krw']);received=won(revenue*D(data['collection_ratio']))
  shipping=D(sold)*D(data['outbound_per_unit_krw']);fees=D(data['fees_krw']);setup=D(data['setup_krw'])
  contribution=revenue-cogs-shipping
  result=contribution-fees-setup
  cash=received-cost-shipping-fees-setup
  rows.append(dict(row,status='계산 완료',goods_krw=str(goods),total_cost=str(cost),
   unit_cost=str(unit),revenue=str(revenue),cogs=str(cogs),inventory_quantity=quote['quantity']-sold,
   inventory_value=str(cost-cogs),gross_profit=str(revenue-cogs),shipping=str(shipping),
   contribution=str(contribution),exercise_result=str(result),receivables=str(revenue-received),
   cash_change=str(cash),ending_cash=str(D(data['opening_cash_krw'])+cash)))
 return {'assumptions':data['assumptions'],'results':rows}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'exercises/P6_견적비교_입력.json');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise SystemExit('출력 파일이 이미 있습니다.')
 r=compare(json.loads(a.input.read_text(encoding='utf-8-sig')));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('계산 결과',len(r['results']),'개 저장')
if __name__=='__main__':main()
