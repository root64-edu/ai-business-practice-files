"""Teaching extension: currency-unit checks and a fictional purchase budget."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json


def main(quantity, unit_price, currency, rate, rate_unit, inbound, budget):
    try:
        def number(value, name, zero_allowed=False):
            if isinstance(value, bool) or value is None or str(value).strip() == '':
                raise ValueError(name + ' 입력이 필요합니다.')
            try:
                parsed = Decimal(str(value))
            except InvalidOperation:
                raise ValueError(name + ' 숫자 형식을 확인합니다.')
            if not parsed.is_finite() or parsed < 0 or (parsed == 0 and not zero_allowed):
                raise ValueError(name + ' 허용 범위를 확인합니다.')
            return parsed

        q = number(quantity, '수량')
        if q != q.to_integral_value():
            raise ValueError('수량은 정수여야 합니다.')
        price = number(unit_price, '외화 단가')
        fx = number(rate, '환율')
        unit = number(rate_unit, '환율 기준 단위')
        shipping = number(inbound, '매입 운임', True)
        limit = number(budget, '예산', True)
        currency = str(currency).strip().upper()
        expected_unit = {'USD': Decimal(1), 'JPY': Decimal(100)}
        if currency not in expected_unit:
            raise ValueError('이 예제는 USD와 JPY만 지원합니다.')
        if unit != expected_unit[currency]:
            raise ValueError('통화와 환율 기준 단위가 맞지 않습니다.')
        if shipping != shipping.to_integral_value() or limit != limit.to_integral_value():
            raise ValueError('운임과 예산은 정수 원으로 입력합니다.')
        goods = (q * price * fx / unit).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        total = goods + shipping
        within = total <= limit
        report = {'currency': currency, 'rate': str(fx), 'rate_unit': str(unit),
                  'quantity': str(q), 'unit_price': str(price), 'goods_krw': str(goods),
                  'inbound_krw': str(shipping), 'total_krw': str(total),
                  'budget_krw': str(limit), 'within_budget': within,
                  'remaining_budget_krw': str(limit - total),
                  'review': '예산 안·구매 조건 별도 확인' if within else '예산 초과·조건 재검토',
                  'scope': '교육용 상품대금과 매입운임만 계산. 세금·관세·기타 비용 제외. 구매 실행 없음.'}
        return {'status': '계산 완료', 'report': json.dumps(report, ensure_ascii=False)}
    except ValueError as exc:
        return {'status': '입력 확인 필요',
                'report': json.dumps({'error': str(exc)}, ensure_ascii=False)}
