"""Compare lexical retrieval settings on a fixed small teaching question set."""
from pathlib import Path
from collections import Counter
import argparse,json,math,runpy
ROOT=Path(__file__).resolve().parents[1]
terms=runpy.run_path(str(ROOT/'workflows/p5_retrieval.py'))['terms']
def evaluate(top_k=4,threshold=0.06):
 if top_k<1 or not 0<=threshold<=1:raise ValueError('top_k는 양수, threshold는 0~1이어야 합니다.')
 docs=json.loads((ROOT/'input/P5_근거검색_자료.json').read_text(encoding='utf-8'))
 questions=json.loads((ROOT/'exercises/P5_추가검색평가_질문.json').read_text(encoding='utf-8'))
 bags=[terms(d['title']+' '+d['text']) for d in docs];df=Counter(t for bag in bags for t in bag)
 def vector(bag):return {t:(1+math.log(n))*(math.log((len(docs)+1)/(df[t]+1))+1) for t,n in bag.items() if t in df}
 def norm(v):return math.sqrt(sum(x*x for x in v.values()))
 vectors=[vector(b) for b in bags];rows=[]
 for q in questions:
  qv=vector(terms(q['question']));qn=norm(qv);ranked=[]
  for d,dv in zip(docs,vectors):
   dn=norm(dv);score=sum(v*dv.get(t,0) for t,v in qv.items())/(qn*dn) if qn*dn else 0
   if score>=threshold:ranked.append(dict(d,score=round(score,4)))
  ranked.sort(key=lambda d:(-d['score'],d['id']));selected=ranked[:top_k];ids=[d['id'] for d in selected]
  rows.append({'id':q['id'],'scope':q['scope'],'ids':ids,'scores':[d['score'] for d in selected],
               'hit':bool(set(ids)&set(q['expected_any'])) if q['scope']=='within' else None,
               'text_characters':sum(len(d['title'])+len(d['text']) for d in selected),
               'core_rank_before_top_k':next((i+1 for i,d in enumerate(ranked) if d['id'] in q['expected_any']),None)})
 return {'top_k':top_k,'threshold':threshold,'in_scope':10,'hits':sum(r['hit'] is True for r in rows),
         'outside_with_results':sum(r['scope']=='outside' and bool(r['ids']) for r in rows),
         'mean_selected_characters':round(sum(r['text_characters'] for r in rows)/len(rows),1),
         'note':'공통 단어·두 글자 조각 검색. 적용 범위 연결 조문은 이 순위 비교에서 제외. 글자 수는 토큰 수가 아님. 기대 근거 중 하나의 포함 여부이며 정밀도·답변 정확도가 아님.',
         'questions':rows}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--top-k',type=int,default=4);p.add_argument('--threshold',type=float,default=.06);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise SystemExit('출력 파일이 이미 있습니다.')
 r=evaluate(a.top_k,a.threshold);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='questions'},ensure_ascii=False))
if __name__=='__main__':main()
