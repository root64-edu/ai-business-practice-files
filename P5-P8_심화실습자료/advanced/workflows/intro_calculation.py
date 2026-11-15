from decimal import Decimal, ROUND_HALF_UP

def main(quantity: float, unit_price: float, rate: float, rate_unit: float) -> dict:
    q, p, r, u = [Decimal(str(v)) for v in (quantity, unit_price, rate, rate_unit)]
    if q <= 0 or q != q.to_integral_value() or p < 0 or r <= 0 or u <= 0:
        return {"status": "확인 필요", "report": "수량은 양의 정수, 단가는 0 이상, 환율과 표시 단위는 양수여야 합니다."}
    foreign = q * p
    krw = (foreign / u * r).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return {"status": "계산 완료", "report": f"외화 상품 대금: {foreign}\n원화 상품 대금: {krw}원\n계산: {q} × {p} ÷ {u} × {r}\n원 단위 반올림. 운임·수수료·세금은 포함하지 않았습니다."}
