"""Offline exercise with explicitly fictional visiting windows and reservations."""
from pathlib import Path
import argparse
import copy
import itertools
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def minute(value):
    h, m = map(int, value.split(':'))
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError('시각 범위 오류')
    return h * 60 + m


def clock(value):
    return f'{value // 60:02}:{value % 60:02}'


def evaluate(data):
    places = data['places']
    if set(places) != {'C', 'B', 'M', 'D'}:
        raise ValueError('장소 코드 C/B/M/D 네 개가 필요합니다.')
    if data['traffic_multiplier'] <= 0:
        raise ValueError('이동시간 배율은 양수여야 합니다.')
    routes = {}
    for f in (ROOT / 'exercises/P8_경로행렬').glob('*.json'):
        raw = json.loads(f.read_text(encoding='utf-8'))
        route = raw['data']['routes'][0]
        if route['result_code'] != 0:
            raise ValueError('성공한 경로 응답이 필요합니다.')
        routes[f.stem] = route['summary']['duration']
    rows = []
    for order in itertools.permutations(places):
        if data.get('first') and order[0] != data['first']:
            continue
        if data.get('last') and order[-1] != data['last']:
            continue
        now = minute(data['start'])
        events, failures, travel, waiting = [], [], 0, 0
        for i, place in enumerate(order):
            cfg = places[place]
            if cfg['stay'] <= 0 or cfg['prep'] < 0:
                raise ValueError('체류·준비 시간 범위를 확인합니다.')
            leg = 0 if i == 0 else math.ceil(
                routes[order[i - 1] + '_' + place] * data['traffic_multiplier'] / 60)
            now += leg
            arrival = now
            ready = now + cfg['prep']
            start = max(ready, minute(cfg['open']))
            slot = cfg.get('reservation')
            if slot:
                reserved = minute(slot)
                if start > reserved:
                    failures.append(place + ': 예약 시작 시각에 준비 미완료')
                start = max(start, reserved)
            wait = start - ready
            end = start + cfg['stay']
            if start > minute(cfg['last_entry']):
                failures.append(place + ': 마지막 입장 시각 초과')
            if end > minute(cfg['close']):
                failures.append(place + ': 관람 종료가 이용 종료 시각 초과')
            events.append({'place': place, 'travel_minutes': leg,
                           'arrival': clock(arrival), 'ready': clock(ready),
                           'wait_minutes': wait, 'visit_start': clock(start),
                           'visit_end': clock(end), 'stay_minutes': cfg['stay'],
                           'prep_minutes': cfg['prep']})
            travel += leg
            waiting += wait
            now = end
            if i + 1 == data['meal_after_visit']:
                events.append({'event': 'meal', 'start': clock(now),
                               'end': clock(now + data['meal_minutes']),
                               'minutes': data['meal_minutes']})
                now += data['meal_minutes']
        if now > minute(data['deadline']):
            failures.append('전체: 목표 종료 시각 초과')
        rows.append({'order': list(order), 'finish': clock(now),
                     'elapsed': now - minute(data['start']),
                     'margin': minute(data['deadline']) - now,
                     'travel': travel, 'waiting': waiting,
                     'feasible_under_assumptions': not failures,
                     'failures': failures, 'events': events})
    rows.sort(key=lambda r: (not r['feasible_under_assumptions'], r['elapsed'], r['order']))
    return {'scenario': data['scenario'], 'fictional_conditions': True,
            'note': '운영·예약 조건은 모두 가상입니다. 실제 장소의 운영시간이 아닙니다. 외부 이동·주차·식당 위치는 제외합니다.',
            'candidate_count': len(rows),
            'feasible_count': sum(r['feasible_under_assumptions'] for r in rows),
            'conditions': copy.deepcopy(data), 'results': rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise SystemExit('출력 파일이 이미 있습니다.')
    result = evaluate(json.loads(a.input.read_text(encoding='utf-8-sig')))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['scenario', 'candidate_count', 'feasible_count']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
