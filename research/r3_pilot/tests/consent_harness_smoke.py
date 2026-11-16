"""RAM-only localhost consent-control verification. NO fake authorization.
Raw exports are ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA and consent=false.
"""
from pathlib import Path
import sys,importlib.util,json,copy,traceback
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from build_pilot import build,sha
from verify_candidate import verify
import analyze as A
import jsonschema
from playwright.sync_api import sync_playwright

def run():
 spec=importlib.util.spec_from_file_location('r3_existing_browser','/workspace/R3_GEOMETRY_RELIABILITY_02/tests/harness.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);e=P/'evidence/final02';h.E=e/'harness-downloads';h.E.mkdir(exist_ok=True,parents=True);ram=build(None,engineering_harness=True);h.HTML=ram['html'].encode();identity=ram['identity'];verify(ram['html'],identity);rows=[]
 with sync_playwright() as pw:
  for engine in ['chromium','firefox']:
   site=None;d=None;row={'engine':engine,'html_sha256':identity['html_sha256'],'mode':'MEMORY_ONLY_LOCALHOST_ENGINEERING_HARNESS','research_authorized':False,'actual_human_consent':False}
   try:
    site=h.Site();d=h.Chrome(pw,site,390,844,3,True) if engine=='chromium' else h.Firefox(site,1024,768,1);d.open('/consent-harness/');assert d.eval('document.getElementById("welcome").textContent.includes("SIMULATION TECHNIQUE LOCALE")');assert d.eval('document.getElementById("pilot-info").compareDocumentPosition(document.getElementById("ack"))&Node.DOCUMENT_POSITION_FOLLOWING');assert d.eval('document.getElementById("participant-id").value===""');d.fill('#participant-id','TEST-INVALID');d.click('#start');assert d.snapshot()['phase']=='welcome';d.fill('#participant-id','PILOT-TECH0001');d.click('#start');assert d.snapshot()['phase']=='welcome' and d.snapshot()['answered']==0;d.click('#ack');d.click('#start');assert d.snapshot()['phase']=='instructions';d.click('#begin')
    for i in range(24):
     d.wait('R3Diagnostics.snapshot().ready')
     for side in ['A','B']:h.inspect(d,side)
     d.click('[data-response="'+['A','B','T','U'][i%4]+'"]');d.click('#next')
    d.wait('R3Diagnostics.snapshot().phase==="complete"');raw=d.download('#download',engine+'-SYNTHETIC_ENGINEERING_HARNESS.json');schema=A.load(P/'HARNESS_RESULT_SCHEMA.json');jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(raw)
    assert raw['participant']['research_consent'] is False and raw['validation']['study_authorization']=='NOT_AUTHORIZED';assert raw['data_class']=='ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA';assert len(raw['trials'])==24 and len({r['trial_id'] for r in raw['trials']})==24;assert {r['response'] for r in raw['trials']}==set('ABTU')
    # Validation-only legacy projection checks unchanged 24-slot semantics;
    # it neither changes the raw file nor produces an admitted pilot record.
    x=copy.deepcopy(raw);x.update(schema_version='R3-RESULT-1',data_class='TECHNICAL_VALIDATION_NOT_HUMAN_DATA');x['experiment']['study_version']='R3-VALIDATION-1';x['participant']['pseudonymous_id']='TEST-'+x['participant']['pseudonymous_id'][6:];x['participant']['consent_version']='R3-TECH-ACK-1';A.validate(x,identity);assert x['trials']==raw['trials']
    refused=[]
    for purpose in ['technical','synthetic','pilot']:
     try:A.identity_for(raw,A.load(P/'BUILD_LOCK.json'),purpose);raise AssertionError('Harness admitted')
     except A.Invalid as ex:refused.append({'purpose':purpose,'reason':str(ex)})
    diag=d.download('#diag-download',engine+'-SYNTHETIC_HARNESS_DIAGNOSTIC.json');assert diag['human_study_authorization']=='NOT_AUTHORIZED' and diag['data_class']=='TECHNICAL_DIAGNOSTIC_NOT_HUMAN_OBSERVATIONS'
    assert d.eval('localStorage.length===0&&sessionStorage.length===0&&document.cookie===""')
    if engine=='chromium':
     assert not d.errors and not d.console and not d.failed;assert all(x['method']=='GET' and not x['body'] and 'TECH0001' not in x['url'] for x in d.requests);row['application_requests']=d.requests;row['console_errors']=list(d.errors)
     # Intercepted in-memory route: no connection to a remote service occurs.
     d.context.set_offline(False);seen=[];guard_errors=[];probe=d.context.new_page();probe.on('pageerror',lambda ex:guard_errors.append(str(ex)));probe.route('https://nondeployable.invalid/**',lambda route:(seen.append(True),route.fulfill(body=ram['html'],content_type='text/html')));probe.goto('https://nondeployable.invalid/');assert probe.locator('body').inner_text().startswith('Banc d’essai local uniquement');assert probe.locator('#start').count()==0 and seen;assert guard_errors==['HARNESS_LOCAL_ONLY'];row['expected_nondeployable_guard_errors']=guard_errors;probe.close();row['nonlocalhost_execution']='REFUSED_EXPECTED_HARNESS_LOCAL_ONLY';row['nonlocalhost_probe']='PLAYWRIGHT_IN_MEMORY_ROUTE_NO_EXTERNAL_CONNECTION'
    row.update(status='PASS',trial_slots=24,refusal_prevents_entry=True,information_before_consent=True,pilot_identifier_control=True,export_schema='PASS_HARNESS_ONLY',pilot_admission='REFUSED',refusals=refused,actual_authorized_release='NOT_RUN_REAL_AUTHORIZATION_MISSING')
   except Exception:row.update(status='FAIL',error=traceback.format_exc())
   finally:
    if d:d.close()
    if site:site.close()
    rows.append(row);print(engine,row['status'],flush=True);(e/'CONSENT_HARNESS.json').write_text(json.dumps({'rows':rows,'human_study_authorization':'NOT_AUTHORIZED','human_observations_collected':False,'activated_html_written_to_disk':False,'genuine_pilot_positive_admission':'PENDING_REAL_AUTHORIZATION_AND_REAL_CONSENT'},indent=2)+'\n')
 return any(x['status']=='FAIL' for x in rows)
if __name__=='__main__':raise SystemExit(run())
