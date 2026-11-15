"""Read-only itinerary tools over saved public API route data."""
import json,math

def evaluate_plan(plan_id, data):
    found=[p for p in data['plans'] if p['id']==plan_id]
    if len(found)!=1: raise ValueError('계획 ID 없음 또는 중복')
    p=found[0];order=p['order']
    if len(order)!=len(set(order)) or not order: raise ValueError('장소 누락 또는 중복')
    def minute(text):
        h,m=map(int,text.split(':'))
        if not 0<=h<24 or not 0<=m<60: raise ValueError('시각 형식 오류')
        return h*60+m
    start=minute(p['start']);deadline=minute(p['deadline']);t=start;travel=0;distance=0;rows=[]
    if deadline<=start: raise ValueError('종료 목표는 시작 이후여야 합니다')
    for i,code in enumerate(order):
        if code not in data['places']: raise ValueError('장소 ID 없음')
        stay=p['stays'][code]
        if isinstance(stay,bool) or not isinstance(stay,(int,float)) or not math.isfinite(stay) or stay<=0: raise ValueError('체류 시간 오류')
        t+=10;begin=t;t+=stay
        rows.append({'place':data['places'][code]['name'],'visit_start':f'{int(begin)//60:02}:{int(begin)%60:02}','visit_end':f'{int(t)//60:02}:{int(t)%60:02}','stay_minutes':stay})
        if i==1:t+=45
        if i<len(order)-1:
            key=code+'_'+order[i+1]
            if key not in data['routes']: raise ValueError('해당 방향의 경로 자료 없음')
            r=data['routes'][key]
            if r['mode']!='car': raise ValueError('자동차 경로 조건 불일치')
            sec=r['duration_sec'];dist=r['distance_m']
            if sec<=0 or dist<0 or not math.isfinite(sec) or not math.isfinite(dist):raise ValueError('경로 수치 오류')
            mins=math.ceil(sec/60);t+=mins;travel+=mins;distance+=dist
    return {'plan_id':plan_id,'order':order,'rows':rows,'finish':f'{int(t)//60:02}:{int(t)%60:02}','total_minutes':t-start,'travel_minutes':travel,'distance_m':distance,'within_time_budget':t<=deadline,'margin_minutes':deadline-t,'checks_not_completed':['방문일의 실제 운영·입장 마감·임시 휴관','대표점과 실제 주차장·보행 연결','차량 및 현장 상황·식사 장소'],'assumptions':'장소별 준비10분, 두 번째 방문 뒤 식사45분, 주어진 체류 시간. 저장된 자동차 경로 사용. 예약·실시간 조회 없음.'}

def main(action_json: str, data_json: str) -> dict:
    try:
        text=action_json.strip()
        if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
        action=json.loads(text);data=json.loads(data_json)
        tool=action['tool'];args=action['arguments']
        if tool=='inspect_plan':ids=[args['plan_id']]
        elif tool=='compare_plans':
            ids=args['plan_ids']
            if not isinstance(ids,list) or not 2<=len(ids)<=3 or len(ids)!=len(set(ids)):raise ValueError('비교 계획은 서로 다른 2~3개')
        else:raise ValueError('허용되지 않은 도구')
        results=[evaluate_plan(id,data) for id in ids]
        return {'status':'도구 실행 완료','observation':json.dumps({'tool':tool,'results':results},ensure_ascii=False)}
    except (ValueError,KeyError,TypeError,ArithmeticError) as e:
        return {'status':'도구 입력 확인 필요','observation':json.dumps({'error':str(e)},ensure_ascii=False)}
