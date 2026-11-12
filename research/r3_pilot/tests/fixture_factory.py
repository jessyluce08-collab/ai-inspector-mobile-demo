"""SYNTHETIC SOFTWARE FIXTURES. No human observations or actual authorization.
Generated claims/timestamps are artificial values used only for parser testing.
"""
from pathlib import Path
import sys,json,copy,hashlib
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
import analyze as A
from build_pilot import build,sha

def record(identity,completed=24):
 manifest=A.load(P/'frozen/STIMULUS_MANIFEST.json');seed='0123456789abcdef';plan=A.V.plan(manifest,seed,'PILOT24');rows=[]
 for i,p in enumerate(plan):
  done=i<completed;code=['A','B','T','U'][i%4] if done else None
  g={'mode':'SEQUENTIAL_FIXED_IMAGE','source':{'width':384,'height':288},'css':{'width':384,'height':288},'dpr':1,'visual_scale':1,'viewport':{'width':1024,'height':768},'layout_viewport':{'width':1024,'height':768},'visual_viewport':{'width':1024,'height':768,'offsetTop':0,'offsetLeft':0},'orientation':'landscape','estimated_render_pixels':{'width':384,'height':288},'sampling':'ESTIMATED_1_TO_1_NOT_VERIFIED','physical_pixel_pitch':'UNKNOWN','native_display_verified':False,'flags':[],'support_rule':'R3-WHOLE-IMAGE-HEURISTIC-1','status':'DISPLAY_GEOMETRY_DOCUMENTED'}
  rows.append({'trial_id':f'TR-{i+1:02d}','pair_id':p['pair']['pair_id'],'order_index':i+1,'source_id':p['pair']['source_id'],'source_group_id':p['pair']['group_id'],'variant_a':p['A'],'variant_b':p['B'],'manifest_reference':p['pair']['pair_id'],'attempted':done or i==completed,'completed':done,'response':code,'missing_response':not done,'abstained':code=='U','response_utc':f'2000-01-02T00:02:{i:02d}Z' if done else None,'elapsed_ms':1000 if done else None,'timing_status':'MONOTONIC' if done else 'NOT_STARTED','inspection':{'A':done,'B':done},'display_geometry':g if done else None,'display_warnings':[],'technical_invalidation':[],'visibility_interrupted':False,'geometry_events':[]})
 d={'schema_version':'R3-RESULT-1','data_class':'TECHNICAL_VALIDATION_NOT_HUMAN_DATA','experiment':{'study_id':'AI-INSPECTOR-R3-OFFLINE-HUMAN-BLUR-STUDY','study_version':'R3-VALIDATION-1','protocol_version':'R3-PILOT-1','stimulus_manifest_version':'R3-STIMULI-1','manifest_sha256':identity['manifest_sha256'],'application_build_id':identity['build_id'],'application_code_sha256':identity['application_code_sha256'],'artifact_checksum_location':'EXTERNAL_RELEASE_MANIFEST','mode':'PILOT24'},'participant':{'pseudonymous_id':'TEST-'+'SYN0001','technical_acknowledged':True,'research_consent':False,'consent_version':'R3-TECH-ACK-1','consent_utc':'2000-01-02T00:00:30Z'},'session':{'session_id':'S-0123456789abcdef','seed':seed,'started_utc':'2000-01-02T00:01:00Z','ended_utc':'2000-01-02T00:10:00Z','completed_utc':'2000-01-02T00:10:00Z' if completed==24 else None,'status':'COMPLETE' if completed==24 else 'STOPPED'},'device':{'browser_family':'UNKNOWN','os_family':'UNKNOWN'},'trials':rows,'integrity':{},'validation':{'status':'LOCAL_STRUCTURE_CHECKED_TECHNICAL_ONLY','human_reference_admission':'NOT_ADMITTED','study_authorization':'NOT_AUTHORIZED'},'export':{'exported_utc':'2000-01-02T00:11:00Z','attempt':1}}
 return rehash(d)
def rehash(d):
 rows=d['trials'];d['integrity'].update(planned_trial_count=len(rows),record_slot_count=len(rows),recorded_trial_count=sum(r['attempted'] for r in rows),completed_trial_count=sum(r['completed'] for r in rows),missing_response_count=sum(r['response'] is None for r in rows),abstention_count=sum(r['abstained'] for r in rows),tie_count=sum(r['response']=='T' for r in rows),record_summary_sha256=sha(json.dumps([[r[k] for k in ['trial_id','variant_a','variant_b','response','completed','abstained']] for r in rows],separators=(',',':')).encode()),digest_scope='JSON compact array of trial_id,variant_a,variant_b,response,completed,abstained; not entire payload or authenticity');return d

def write_fixture(path,d):path=Path(path);path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');return path

def catalog(paths,output):
 d={'data_class':'SYNTHETIC_TEST_FIXTURES_NOT_HUMAN_OBSERVATIONS','files':[{'filename':p.name,'sha256':sha(p.read_bytes()),'synthetic':True} for p in paths]};Path(output).write_text(json.dumps(d,indent=2)+'\n');return Path(output)
