"""Transparent character-bigram retrieval for the teaching corpus; not vector embeddings."""
import json, math, re
from collections import Counter

def terms(text):
    text = re.sub(r'\s+', ' ', text.lower())
    result = []
    for word in re.findall(r'[가-힣a-z0-9]+', text):
        result.append(word)
        result.extend(word[i:i+2] for i in range(len(word)-1))
    return Counter(result)

def main(question: str, knowledge_json: str) -> dict:
    try:
        docs = json.loads(knowledge_json)
        if not isinstance(docs, list) or not docs:
            raise ValueError('empty corpus')
        ids = [d['id'] for d in docs]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate source id')
        bags = [terms(d['title'] + ' ' + d['text']) for d in docs]
        query = terms(question)
        df = Counter(t for bag in bags for t in bag)
        def vector(bag):
            return {t: (1+math.log(n))*(math.log((len(docs)+1)/(df[t]+1))+1)
                    for t,n in bag.items() if t in df}
        qv = vector(query)
        qnorm = math.sqrt(sum(v*v for v in qv.values()))
        scored = []
        for doc, bag in zip(docs, bags):
            dv = vector(bag)
            norm = math.sqrt(sum(v*v for v in dv.values()))
            score = sum(v*dv.get(t,0) for t,v in qv.items())/(qnorm*norm) if qnorm*norm else 0
            if score >= 0.06:
                scored.append(dict(doc, retrieval_score=round(score,4)))
        scored.sort(key=lambda d: (-d['retrieval_score'], d['id']))
        selected = scored[:4]
        # Applicability provisions are linked evidence, not extra similarity hits.
        linked = []
        if any('채용절차' in d['document'] for d in selected):
            linked.append('LAW-채용절차법_3조')
        if any('근로기준' in d['document'] or d['id'].startswith(('G26-', 'H23-')) for d in selected):
            linked.append('LAW-근로기준법_11조')
        by_id = {d['id']: d for d in docs}
        for source_id in linked:
            if source_id in by_id and source_id not in {d['id'] for d in selected}:
                selected.append(dict(by_id[source_id], retrieval_score=None,
                                     retrieval_reason='적용 범위 연결 조문'))
        return {'context': json.dumps(selected, ensure_ascii=False),
                'count': len(selected),
                'status': '검색 완료' if selected else '근거 없음'}
    except (ValueError, KeyError, TypeError):
        return {'context': '[]', 'count': 0, 'status': '자료 형식 확인 필요'}
