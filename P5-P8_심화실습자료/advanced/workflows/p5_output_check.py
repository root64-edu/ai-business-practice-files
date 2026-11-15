"""Narrow, conservative checks; never a legal correctness certificate."""
import json,re

def main(answer: str, context: str) -> dict:
    docs=json.loads(context);known={d['id'] for d in docs};issues=[]
    # IDs are deliberately machine-checkable. This does not validate the legal interpretation.
    cited=set(re.findall(r'(?:LAW-[가-힣]+_[0-9]+조(?:의[0-9]+)?|[GRH][0-9]{2}-p[0-9]{3}(?:-c[0-9]+)?)',answer))
    unknown=sorted(cited-known)
    if unknown:issues.append('자료에 없는 출처 ID: '+', '.join(unknown))
    if not cited:issues.append('확인 가능한 출처 ID 없음')
    if any('4조의3' in d['id'] for d in docs):
        for sentence in re.split(r'[\n.!?]',answer):
            if re.search(r'(비필수|선택\s*항목|선택표시)',sentence) and re.search(r'(변경|전환)',sentence):
                issues.append('금지 항목의 선택·비필수 전환 표현: 담당자가 원문 대조 필요')
                break
    if not docs:issues.append('검색 근거 없음')
    status='담당자 검토 필요' if issues else '형식 점검 통과·내용 검토 필요'
    note='\n'.join('- '+i for i in issues) if issues else '출처 ID와 제한 표현 검사만 통과했습니다. 법률상 정확성은 사람이 원문과 대조합니다.'
    return {'status':status,'checked_memo':status+'\n'+note+'\n\n검토 전 AI 초안:\n'+answer,'issues':json.dumps(issues,ensure_ascii=False)}
