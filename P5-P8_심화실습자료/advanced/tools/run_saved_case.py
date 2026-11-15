"""Run the supplied calculation/retrieval code locally, without network or model calls."""
from pathlib import Path
import argparse, json, runpy
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('project',choices=['P5','P6','P7','P8'])
p.add_argument('--input',type=Path,required=True)
p.add_argument('--question',default='')
p.add_argument('--action',type=Path)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.out.exists():raise SystemExit('출력 파일이 이미 있습니다. 다른 이름을 지정합니다.')
files={'P5':'p5_retrieval.py','P6':'p6_calculator.py','P7':'p7_calculator.py','P8':'p8_tools.py'}
main=runpy.run_path(str(ROOT/'workflows'/files[a.project]))['main']
raw=a.input.read_text(encoding='utf-8-sig')
if a.project=='P5':result=main(a.question,raw)
elif a.project=='P8':
 if not a.action:raise SystemExit('P8에는 --action 요청 JSON 파일이 필요합니다.')
 result=main(a.action.read_text(encoding='utf-8-sig'),raw)
else:result=main(raw)
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'project':a.project,'status':result['status'],'file':str(a.out)},ensure_ascii=False))
