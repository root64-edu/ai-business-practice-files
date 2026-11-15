"""Local-only teaching map. The Maps JavaScript key is client-visible by design.
Keep the key in an environment variable and restrict its allowed domains in Kakao.
No REST credential is delivered to the browser.
"""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import os,json
HERE=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/':body=(HERE/'index.html').read_bytes();kind='text/html; charset=utf-8'
  elif self.path=='/data':body=(HERE.parent/'completed/P8_지도와일정.json').read_bytes();kind='application/json; charset=utf-8'
  elif self.path=='/config':body=json.dumps({'javascript_key':os.environ.get('KAKAO_JAVASCRIPT_KEY','')}).encode();kind='application/json'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
if __name__=='__main__':
 if not os.environ.get('KAKAO_JAVASCRIPT_KEY'):raise SystemExit('KAKAO_JAVASCRIPT_KEY 환경 변수가 필요합니다.')
 port=int(os.environ.get('TEXTBOOK_MAP_PORT','8080'))
 if not 1024<=port<=65535:raise SystemExit('지도 포트 범위를 확인합니다.')
 print(f'관광 지도: http://127.0.0.1:{port}',flush=True)
 ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
