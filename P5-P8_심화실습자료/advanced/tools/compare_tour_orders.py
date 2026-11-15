"""Enumerate four-place orders using the saved second-round route matrix.
This is an offline comparison of stated assumptions, not live trip approval.
"""
from pathlib import Path
import argparse, itertools, json, math
ROOT=Path(__file__).resolve().parents[1]
PROFILES={'standard':{'C':25,'B':70,'M':60,'D':35},
          'museum':{'C':25,'B':70,'M':90,'D':35},
          'heritage':{'C':40,'B':100,'M':60,'D':50}}

def compare(profile='standard',first=None,last=None):
    stays=PROFILES[profile];routes={}
    for file in (ROOT/'exercises/P8_경로행렬').glob('*.json'):
        raw=json.loads(file.read_text(encoding='utf-8'));r=raw['data']['routes'][0]
        if r['result_code']!=0:raise ValueError('경로 성공 여부 확인 필요')
        routes[file.stem]={'seconds':r['summary']['duration'],'meters':r['summary']['distance'],
                           'retrieved_at':raw['retrieved_at']}
    rows=[]
    for order in itertools.permutations(stays):
        if first and order[0]!=first:continue
        if last and order[-1]!=last:continue
        legs=[routes[a+'_'+b] for a,b in zip(order,order[1:])]
        seconds=sum(r['seconds'] for r in legs)
        travel=sum(math.ceil(r['seconds']/60) for r in legs)
        total=40+45+sum(stays.values())+travel
        finish=600+total
        rows.append({'order':list(order),'route_seconds':seconds,'travel_minutes':travel,
                     'distance_m':sum(r['meters'] for r in legs),'stay_minutes':sum(stays.values()),
                     'total_minutes':total,'finish':f'{finish//60:02}:{finish%60:02}',
                     'margin_minutes':360-total,'within_budget':total<=360})
    rows.sort(key=lambda r:(r['total_minutes'],r['distance_m'],r['order']))
    return {'profile':profile,'first':first,'last':last,'candidate_count':len(rows),
            'assumptions':'10:00 시작·16:00 목표. 장소별 준비10분·식사45분·가상 체류. 첫 장소 이전 및 마지막 이후 이동 제외. 운영·예약·현장 확인 미완료.',
            'sort_rule':'총시간 오름차순, 같으면 거리 오름차순, 같으면 장소 코드순',
            'route_times':{k:r['retrieved_at'] for k,r in routes.items()},'results':rows}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',choices=PROFILES,default='standard')
    p.add_argument('--first',choices=['C','B','M','D']);p.add_argument('--last',choices=['C','B','M','D']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('출력 파일이 이미 있습니다.')
    result=compare(a.profile,a.first,a.last);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_count':result['candidate_count'],'first_result':result['results'][:1]},ensure_ascii=False))
if __name__=='__main__':main()
