"""Load local map key, then run the localhost-only teaching map."""
from pathlib import Path
import os, runpy
read_env = runpy.run_path(str(Path(__file__).with_name("fetch_public_api.py")))["read_env"]
root = Path(__file__).resolve().parents[1]
values = read_env(root/'.env')
key = values.get('KAKAO_JAVASCRIPT_KEY', '')
if not key:
    raise SystemExit('advanced/.env에 KAKAO_JAVASCRIPT_KEY를 설정합니다.')
os.environ['KAKAO_JAVASCRIPT_KEY'] = key
runpy.run_path(str(root/'map/serve.py'), run_name='__main__')
