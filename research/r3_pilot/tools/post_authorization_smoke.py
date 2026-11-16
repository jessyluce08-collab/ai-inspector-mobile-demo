"""Gated exact-candidate automation, NOT_EXECUTED without real authorization.
Nominal consent metadata tests a control only, not an actual observer's consent.
Raw scripted replies are ephemeral and use a reserved nonadmissible TECH code.
"""
from pathlib import Path
import json,tempfile,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from build_pilot import authorization,sha,P
from verify_candidate import verify,require

def run(html_path,identity,config_path):
 authorization(config_path) # actual investigator decision required; no simulation hook
 data=Path(html_path).read_bytes();verify(data.decode(),identity)
 from playwright.sync_api import sync_playwright
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(server.server_port)
 errors=[];requests=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=3,is_mobile=True,has_touch=True,accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append({'url':r.url,'method':r.method,'body':r.post_data}) if r.url.startswith(('http:','https:')) else None);page.goto(url);page.wait_for_function('document.documentElement.dataset.ready==="true"');context.set_offline(True)
   page.locator('#participant-id').fill('PILOT-TECH0001');page.locator('#start').tap();require(page.locator('#welcome').is_visible(),'Consent refusal did not prevent entry');page.locator('#ack').check();page.locator('#start').tap();page.locator('#begin').tap()
   for i in range(24):
    page.wait_for_function('R3Diagnostics.snapshot().ready')
    for side in ['A','B']:page.locator('#show-'+side.lower()).tap();page.wait_for_function('(s)=>R3Diagnostics.snapshot().settled&&R3Diagnostics.snapshot().inspection[s]',arg=side)
    page.locator('[data-response="'+['A','B','T','U'][i%4]+'"]').tap();page.locator('#next').tap()
   page.wait_for_function('R3Diagnostics.snapshot().phase==="complete"')
   with page.expect_download() as got:page.locator('#download').tap()
   raw=json.loads(Path(got.value.path()).read_text())
   import analyze
   analyze.validate(raw,identity,True);require(raw['participant']['pseudonymous_id']=='PILOT-TECH0001' and raw['integrity']['completed_trial_count']==24,'Technical test slot/identity mismatch');require(not errors and all(r['method']=='GET' and not r['body'] and 'TECH0001' not in r['url'] for r in requests),'Console/network failure')
   context.close();browser.close() # deletes ephemeral raw technical downloads
  return {'status':'PASS','html_sha256':sha(data),'trial_slots':24,'four_response_controls_exercised':True,'export_schema_and_semantics':'PASS','raw_scripted_export_retained':False,'test_code':'PILOT-TECH0001','actual_participant_consent_proven':False,'human_reference_admission':False,'purpose':'AUTOMATED_POSTAUTH_TECHNICAL_CONTROL_TEST_ONLY','requests':requests,'console_errors':errors,'real_device_validation':'NOT_RUN'}
 finally:server.shutdown();server.server_close()
