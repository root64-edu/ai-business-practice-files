"""Read-only classroom API collector. Standard library only; never prints keys."""
from pathlib import Path
import argparse, datetime, json, os, re
import urllib.error, urllib.parse, urllib.request


def read_env(path):
    values = dict(os.environ)
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
                values.setdefault(key, value)
    return values


def request_spec(a):
    if a.service == 'fx':
        datetime.datetime.strptime(a.date, '%Y%m%d')
        return ('https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON',
                {'searchdate': a.date, 'data': 'AP01'}, 'EXIM_API_KEY', 'authkey')
    if a.service == 'dart':
        if not re.fullmatch(r'\d{8}', a.corp) or not re.fullmatch(r'\d{4}', a.year):
            raise ValueError('기업 고유번호 8자리·연도 4자리를 확인합니다.')
        return ('https://opendart.fss.or.kr/api/fnlttSinglAcnt.json',
                {'corp_code': a.corp, 'bsns_year': a.year, 'reprt_code': '11011'},
                'OPENDART_API_KEY', 'crtfc_key')
    if a.service in ('tour-search', 'tour-detail'):
        params = {'MobileOS': 'ETC', 'MobileApp': 'VocationalTextbook', '_type': 'json'}
        if a.service == 'tour-search':
            params.update(keyword=a.query, numOfRows='10', pageNo=str(a.page))
            endpoint = 'searchKeyword2'
        else:
            params.update(contentId=a.content_id, contentTypeId=a.content_type)
            endpoint = 'detailIntro2'
        return ('https://apis.data.go.kr/B551011/KorService2/'+endpoint,
                params, 'KNTO_API_KEY', 'serviceKey')
    if a.service == 'local':
        return ('https://dapi.kakao.com/v2/local/search/keyword.json',
                {'query': a.query, 'size': '5', 'page': str(a.page)}, 'KAKAO_REST_API_KEY', None)
    for value in (a.origin, a.destination):
        pair = [float(x) for x in value.split(',')]
        if len(pair) != 2 or not -180 <= pair[0] <= 180 or not -90 <= pair[1] <= 90:
            raise ValueError('좌표는 경도,위도 순서입니다.')
    return ('https://apis-navi.kakaomobility.com/v1/directions',
            {'origin': a.origin, 'destination': a.destination, 'priority': 'RECOMMEND',
             'alternatives': 'false', 'road_details': 'true'}, 'KAKAO_REST_API_KEY', None)


def fetch(spec, keys):
    url, safe_params, key_name, key_param = spec
    key = keys.get(key_name, '')
    if not key:
        raise ValueError(key_name+' 설정이 필요합니다.')
    params = dict(safe_params)
    headers = {'User-Agent': 'VocationalTextbook-Learning/1.0'}
    if key_param:
        params[key_param] = urllib.parse.unquote(key)
    else:
        headers['Authorization'] = 'KakaoAK '+key
    record = {'source': url, 'parameters': safe_params,
              'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        request = urllib.request.Request(url+'?'+urllib.parse.urlencode(params), headers=headers)
        with urllib.request.urlopen(request, timeout=40) as response:
            record.update(http_status=response.status, data=json.load(response))
    except urllib.error.HTTPError as error:
        record.update(http_status=error.code, error='HTTPError')
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        record['error'] = type(error).__name__
    # Redact even if an upstream service unexpectedly echoes a credential.
    serialized = json.dumps(record, ensure_ascii=False, indent=2)
    for name in ('EXIM_API_KEY', 'OPENDART_API_KEY', 'KNTO_API_KEY', 'KAKAO_REST_API_KEY'):
        value = keys.get(name, '')
        if value:
            for representation in (value, urllib.parse.unquote(value), urllib.parse.quote(value)):
                serialized = serialized.replace(representation, '[REDACTED]')
    return json.loads(serialized)


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument('--env', type=Path, default=Path('.env'))
    root.add_argument('--out', type=Path, required=True)
    sub = root.add_subparsers(dest='service', required=True)
    sub.add_parser('fx').add_argument('--date', required=True)
    dart = sub.add_parser('dart'); dart.add_argument('--corp', required=True); dart.add_argument('--year', required=True)
    for name in ('local', 'tour-search'):
        part = sub.add_parser(name); part.add_argument('--query', required=True); part.add_argument('--page', type=int, default=1)
    detail = sub.add_parser('tour-detail'); detail.add_argument('--content-id', required=True); detail.add_argument('--content-type', required=True)
    route = sub.add_parser('route'); route.add_argument('--origin', required=True); route.add_argument('--destination', required=True)
    return root


def main():
    a = parser().parse_args()
    if a.out.exists():
        raise SystemExit('출력 파일이 이미 있습니다. 새 파일 이름을 지정합니다.')
    try:
        result = fetch(request_spec(a), read_env(a.env))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'file': str(a.out), 'http_status': result.get('http_status'),
                      'error': result.get('error')}, ensure_ascii=False))
    if result.get('error'):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
