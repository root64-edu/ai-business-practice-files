"""Fictional four-month cash/inventory exercise; no tax or real payment execution."""
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
import argparse
import json

def won(v):
    return D(v).quantize(D('1'), rounding=ROUND_HALF_UP)

def calculate(data):
    months = data['months']
    if len(months) != len(set(months)) or months != sorted(months):
        raise ValueError('월은 중복 없이 오름차순이어야 합니다.')
    if len(data['sales_quantities']) != len(months):
        raise ValueError('월별 판매 수량 개수가 맞지 않습니다.')
    quantity = data['purchase_quantity']
    sales = data['sales_quantities']
    if quantity <= 0 or any(not isinstance(v, int) or v < 0 for v in sales):
        raise ValueError('구매는 양수, 판매는 0 이상의 정수여야 합니다.')
    if sum(sales) > quantity:
        raise ValueError('판매 수량이 구매 수량을 초과합니다.')
    collect = D(data['current_collection_ratio'])
    pay = D(data['first_month_payment_ratio'])
    if not (0 <= collect <= 1 and 0 <= pay <= 1):
        raise ValueError('회수·지급 비율은 0~1이어야 합니다.')
    cost = D(data['purchase_cost_krw'])
    price = D(data['sale_price_krw'])
    opening = D(data['opening_cash_krw'])
    floor = D(data['cash_floor_krw'])
    unit = cost / quantity
    cash, ar, ap, inv, cumulative_result, cumulative_sold = opening, D(0), D(0), cost, D(0), 0
    rows = []
    for i, (month, sold) in enumerate(zip(months, sales)):
        revenue = price * sold
        previous_ar = ar
        receipts = previous_ar + won(revenue * collect)
        ar = revenue - won(revenue * collect)
        payment = won(cost * pay) if i == 0 else (ap if i == 1 else D(0))
        ap = cost - payment if i == 0 else ap - payment
        cumulative_sold += sold
        # Cumulative allocation prevents one-won drift across month boundaries.
        remaining = cost - won(unit * cumulative_sold)
        cogs = inv - remaining
        inv = remaining
        shipping = D(data['outbound_per_unit_krw']) * sold
        fixed = D(data['first_month_fixed_krw']) if i == 0 else D(0)
        result = revenue - cogs - shipping - fixed
        cash_start = cash
        cash += receipts - payment - shipping - fixed
        cumulative_result += result
        bridge = opening + cumulative_result - inv - ar + ap
        if bridge != cash:
            raise AssertionError('현금 연결식 불일치')
        rows.append({'month': month, 'sold_quantity': sold,
                     'inventory_quantity': quantity - cumulative_sold,
                     **{k: str(v) for k, v in dict(revenue=revenue, cogs=cogs,
                         shipping=shipping, fixed=fixed, exercise_result=result,
                         cumulative_result=cumulative_result, receipts=receipts,
                         payment=payment, cash_start=cash_start, cash_end=cash,
                         receivables=ar, payables=ap, inventory_value=inv,
                         cash_floor=floor, floor_shortfall=max(D(0), floor-cash)).items()},
                     'cash_bridge_matches': True})
    return {'scenario': data['scenario'], 'fictional': True,
            'assumptions': data['assumptions'], 'results': rows,
            'note': '첫 월 전량 입고, 매출 미수분 다음 월 전액 회수, 매입 미지급분 둘째 월 전액 지급. 월 중 현금 부족은 별도 검토.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise SystemExit('출력 파일이 이미 있습니다.')
    result = calculate(json.loads(a.input.read_text(encoding='utf-8-sig')))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('월별 계획', len(result['results']), '행 저장')

if __name__ == '__main__':
    main()
