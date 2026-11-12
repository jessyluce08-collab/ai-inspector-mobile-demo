"""Reuse existing R3 browser helpers; no geometry development or human data.
Outputs and prospective-authorized scenario are explicitly synthetic fixtures.
"""
from pathlib import Path
import argparse,sys,importlib.util,tempfile,json,traceback
P=Path(__file__).resolve().parents[1];ROOT=P.parents[1];sys.path[:0]=[str(P/'tools'),str(P/'tests')]
import analyze as A
from build_pilot import build,sha
from playwright.sync_api import sync_playwright

def main(legacy,evidence_directory=None):
 spec=importlib.util.spec_from_file_location('existing_r3_harness',Path(legacy)/'harness.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);evidence=Path(evidence_directory or P/'evidence');h.E=evidence/'browser';h.E.mkdir(parents=True,exist_ok=True);rows=[]
 base=A.load(P/'frozen/BUILD_IDENTITY.json');preview=build(P/'build/technical-preview/index.html')
 with tempfile.TemporaryDirectory() as temp:
  cases=[('existing-five',ROOT/'r3-geometry-reliability-02/index.html',base,False,5),('existing-24',ROOT/'r3-geometry-reliability-02/index.html',base,False,24),('preview-24',P/'build/technical-preview/index.html',preview,False,24)]
  with sync_playwright() as pw:
   for engine in ['chromium','firefox']:
    for name,file,identity,pilot,n in cases:
     d=None;site=None;row={'case':name,'engine':engine,'html_sha256':sha(file.read_bytes()),'data_origin':'AUTOMATED_SYNTHETIC_INTERACTIONS_NOT_HUMAN_OBSERVATIONS','real_device':'NOT_RUN'}
     try:
      h.HTML=file.read_bytes();site=h.Site();d=h.Chrome(pw,site,390,844,3,True) if engine=='chromium' else h.Firefox(site,1024,768,1);d.open('/r3-smoke/');d.fill('#participant-id','INVALID');d.click('#start');assert d.eval('document.getElementById("start-error").textContent.length>0');d.fill('#participant-id',('PILOT-' if pilot else 'TEST-')+'SYN0001');d.click('#ack');d.click('#demo' if n==5 else '#start');assert d.snapshot()['phase']=='instructions';d.click('#begin');d.wait('R3Diagnostics.snapshot().ready')
      for i in range(n):
       h.inspect(d,'A');h.inspect(d,'B');assert d.eval('!document.querySelector("[data-response=T]").disabled');d.click('[data-response="'+['A','B','T','U'][i%4]+'"]');d.click('#next');d.wait('R3Diagnostics.snapshot().phase==="complete"||R3Diagnostics.snapshot().ready')
      assert d.snapshot()['phase']=='complete';out=d.download('#download','SYNTHETIC-'+engine+'-'+name+'-result.json');A.validate(out,identity,pilot);assert out['integrity']['completed_trial_count']==n;retry=d.download('#download','SYNTHETIC-'+engine+'-'+name+'-retry.json');assert retry['trials']==out['trials'] and retry['export']['attempt']==out['export']['attempt']+1;assert d.eval('localStorage.length===0&&sessionStorage.length===0&&document.cookie===""');assert out['participant']['research_consent']==pilot
      if engine=='chromium':assert not d.errors and not d.console and not d.failed;assert all(x['method']=='GET' and not x['body'] and 'SYN0001' not in x['url'] for x in d.requests);row.update(console_errors=d.console,uncaught_errors=d.errors,requests=d.requests)
      d.eval('(()=>{window.confirm=()=>true;return true;})()');d.click('#restart');assert d.snapshot()['phase']=='welcome' and not d.snapshot()['answered'];row.update(status='PASS',trials=n,export_validated=True,retry_identical_trials=True,restart=True)
     except Exception:row.update(status='FAIL',error=traceback.format_exc())
     finally:
      if d:d.close()
      if site:site.close()
      rows.append(row);print(engine,name,row['status'],flush=True);(evidence/'BROWSER_SMOKE.json').write_text(json.dumps({'fixture_label':'SYNTHETIC_SOFTWARE_TESTS_NOT_HUMAN_OBSERVATIONS','rows':rows,'real_android':'NOT_RUN','real_ios':'NOT_RUN','geometry_status':'Operationally closed; no new geometry development','public_pages':'NOT_DEPLOYED'},indent=2)+'\n')
 return any(x['status']=='FAIL' for x in rows)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--legacy-test-directory',type=Path,default=Path('/workspace/R3_GEOMETRY_RELIABILITY_02/tests'));a.add_argument('--evidence-directory',type=Path);x=a.parse_args();sys.exit(main(x.legacy_test_directory,x.evidence_directory))
