"""Offline, schema-checked intake and descriptive feasibility summaries.
No network, inference, detector, probabilities or automatic research admission.
Never rewrites input bytes. Pilot admission needs a separately approved lock,
owner configuration and prospective consent register. Technical runs stay out.
"""
from pathlib import Path
import argparse,csv,copy,hashlib,importlib.util,json,math,sys
from datetime import datetime
P=Path(__file__).resolve().parents[1];ROOT=P.parents[1]
spec=importlib.util.spec_from_file_location('r3_frozen_validator',P/'frozen/validate_results.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
MAX=2*1024*1024
class Invalid(ValueError):pass
def need(ok,code):
 if not ok:raise Invalid(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def number(s):
 v=float(s);need(math.isfinite(v),'NONFINITE_NUMBER');return v
def load(path,with_bytes=False):
 path=Path(path);need(not path.is_symlink(),'SYMLINK_INPUT');need(path.stat().st_size<=MAX,'INPUT_TOO_LARGE');
 with path.open('rb') as f:raw=f.read(MAX+1)
 need(len(raw)<=MAX,'INPUT_TOO_LARGE')
 try:d=json.loads(raw.decode('utf-8'),object_pairs_hook=V.unique_pairs,parse_float=number,parse_constant=lambda x:(_ for _ in ()).throw(Invalid('NONFINITE_NUMBER')))
 except (UnicodeError,json.JSONDecodeError,RecursionError):raise Invalid('MALFORMED_JSON')
 def walk(x,depth=0):
  need(depth<=80,'EXCESSIVE_NESTING')
  if isinstance(x,dict):
   for v in x.values():walk(v,depth+1)
  elif isinstance(x,list):
   for v in x:walk(v,depth+1)
  elif isinstance(x,float):need(math.isfinite(x),'NONFINITE_NUMBER')
 walk(d);need(isinstance(d,dict),'ROOT_NOT_OBJECT');return (d,raw) if with_bytes else d

def date(s):
 d=datetime.fromisoformat(s.replace('Z','+00:00'));need(d.tzinfo is not None,'TIMEZONE_MISSING');return d

def validate(d,identity,pilot=False):
 import jsonschema
 schema=load(P/('PILOT_RESULT_SCHEMA.json' if pilot else 'frozen/RESULT_SCHEMA.json'))
 errors=list(jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).iter_errors(d));need(not errors,'SCHEMA_INCOMPATIBLE')
 e=d['experiment'];need(e['application_build_id']==identity['build_id'] and e['application_code_sha256']==identity['application_code_sha256'],'BUILD_INCOMPATIBLE');need(e['manifest_sha256']==identity['manifest_sha256']==sha((P/'frozen/STIMULUS_MANIFEST.json').read_bytes()),'MANIFEST_INCOMPATIBLE')
 # Validation-only projection reuses the frozen structural, assignment and
 # geometry checks. It is never exported/admitted, and cannot turn a technical
 # file into a pilot observation: pilot schema and purpose are checked first.
 x=copy.deepcopy(d);base=load(P/'frozen/BUILD_IDENTITY.json')
 if pilot:
  x['schema_version']='R3-RESULT-1';x['data_class']='TECHNICAL_VALIDATION_NOT_HUMAN_DATA';x['experiment'].update(study_version='R3-VALIDATION-1',protocol_version='R3-PILOT-1');x['participant'].update(pseudonymous_id='TEST-'+d['participant']['pseudonymous_id'][6:],research_consent=False,consent_version='R3-TECH-ACK-1');x['validation'].update(status='LOCAL_STRUCTURE_CHECKED_TECHNICAL_ONLY',human_reference_admission='NOT_ADMITTED',study_authorization='NOT_AUTHORIZED')
 x['experiment'].update(application_build_id=base['build_id'],application_code_sha256=base['application_code_sha256'])
 try:checks=V.validate(x,P/'frozen')
 except Exception as ex:raise Invalid('STRUCTURE_OR_ASSIGNMENT_INVALID') from ex
 # Original validator accepts a sparse completed sequence. The UI can only
 # produce a completed prefix, with at most one attempted next trial.
 rows=d['trials'];done=[r['completed'] for r in rows];n=sum(done);need(done==[True]*n+[False]*(len(rows)-n),'NONPREFIX_COMPLETION');need(all(not r['attempted'] for r in rows[n+1:]),'IMPOSSIBLE_ATTEMPT_SEQUENCE')
 return checks

def identity_for(d,lock,purpose):
 if d.get('data_class')=='ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA':raise Invalid('ENGINEERING_HARNESS_NOT_PILOT')
 if purpose=='pilot':
  need(d.get('data_class')=='HUMAN_FEASIBILITY_PILOT','TECHNICAL_OR_UNKNOWN_NOT_PILOT');i=lock.get('pilot_identity');need(i and i.get('collection_authorized') is True,'PILOT_LOCK_NOT_AUTHORIZED');return i,True
 pilot=d.get('data_class')=='HUMAN_FEASIBILITY_PILOT'
 need(not pilot or purpose=='synthetic','HUMAN_FILE_REQUIRES_PILOT_ADMISSION')
 candidates=lock.get('synthetic_identities',[]) if purpose=='synthetic' else lock['technical_identities']
 candidates=candidates+lock['technical_identities'] if purpose=='synthetic' else candidates
 i=next((i for i in candidates if i['build_id']==d.get('experiment',{}).get('application_build_id')),None);need(i is not None,'BUILD_INCOMPATIBLE');return i,pilot

def trial_rows(d,input_id):
 m=load(P/'frozen/STIMULUS_MANIFEST.json');pairs={r['pair_id']:r for r in m['pairs']};out=[]
 for r in d['trials']:
  p=pairs[r['pair_id']];flags=r['technical_invalidation'];eligible=r['completed'] and not flags
  direction=None
  if eligible and not p['identity'] and r['response'] in ['A','B']:
   selected=r['variant_a'] if r['response']=='A' else r['variant_b'];direction='HIGHER_IMPOSED_BLUR_REPORTED' if selected==p['higher_variant'] else 'LOWER_IMPOSED_BLUR_REPORTED'
  out.append({'input_id':input_id,'participant_id':d['participant']['pseudonymous_id'],'session_id':d['session']['session_id'],'trial_id':r['trial_id'],'source_id':r['source_id'],'pair_id':r['pair_id'],'condition':p['condition'],'identical_control':p['identity'],'response':r['response'],'completed':r['completed'],'abstained':r['abstained'],'missing':r['missing_response'],'technically_flagged':bool(flags),'analysis_eligible':eligible,'transformation_direction':direction,'display_status':r['display_geometry']['status'] if r['display_geometry'] else 'UNAVAILABLE','downsampling_expected':'DOWNSAMPLING_EXPECTED' in r['display_warnings']})
 return out

def summarize(rows):
 n=len(rows);counts={k:sum(r['response']==k for r in rows) for k in ['A','B','T','U']};missing=sum(r['missing'] for r in rows);flags=sum(r['technically_flagged'] for r in rows);eligible=[r for r in rows if r['analysis_eligible']];controls=[r for r in rows if r['identical_control']];non=[r for r in rows if not r['identical_control']];comparable=[r for r in eligible if r['response'] in ['A','B','T']];ab=[r for r in comparable if not r['identical_control'] and r['response'] in ['A','B']]
 return {'planned':n,'responses':counts,'missing':missing,'completed':sum(r['completed'] for r in rows),'technically_flagged':flags,'analysis_eligible':len(eligible),'eligible_ABT':len(comparable),'abstention_rate_planned':counts['U']/n if n else None,'missing_rate_planned':missing/n if n else None,'control_response_counts':{k:sum(r['response']==k for r in controls) for k in ['A','B','T','U']},'control_missing':sum(r['missing'] for r in controls),'control_AB_reports':sum(r['response'] in ['A','B'] for r in controls),'control_planned':len(controls),'higher_imposed_report_count':sum(r['transformation_direction']=='HIGHER_IMPOSED_BLUR_REPORTED' for r in non),'nonidentity_planned':len(non),'higher_imposed_fraction_planned_nonidentity':sum(r['transformation_direction']=='HIGHER_IMPOSED_BLUR_REPORTED' for r in non)/len(non) if non else None,'higher_imposed_fraction_conditional_AB':sum(r['transformation_direction']=='HIGHER_IMPOSED_BLUR_REPORTED' for r in ab)/len(ab) if ab else None,'control_AB_fraction_planned':sum(r['response'] in ['A','B'] for r in controls)/len(controls) if controls else None,'nonidentity_eligible_AB_denominator':len(ab),'tie_eligible':sum(r['response']=='T' for r in eligible),'downsampling_records':sum(r['downsampling_expected'] for r in rows),'restricted_display_records':sum(r['display_status'] in ['UNSUPPORTED_LAYOUT','DISPLAY_GEOMETRY_UNCERTAIN','INSUFFICIENT_REGION_SUPPORT'] for r in rows)}

def verify_lock(lock):
 for field in ['source_hashes','document_hashes','preserved_entrypoints']:
  for name,digest in lock[field].items():
   path=Path(name);need(not path.is_absolute() and '..' not in path.parts,'UNSAFE_LOCK_PATH');need(sha((ROOT/path).read_bytes())==digest,'VERSION_LOCK_MISMATCH:'+name)
 need(sha(json.dumps(lock['source_hashes'],sort_keys=True,separators=(',',':')).encode())==lock['analysis_revision_sha256'],'ANALYSIS_REVISION_MISMATCH')

def analyze(paths,lock,purpose='technical',register=None,authorization=None,catalog=None):
 verify_lock(lock);need(purpose in ['technical','pilot','synthetic'],'UNKNOWN_PURPOSE');need(len(paths)<=500,'TOO_MANY_FILES');ledger=[];candidates=[];participants={}
 if purpose=='pilot':
  from build_pilot import authorization as approve
  need(authorization is not None and register is not None,'PILOT_AUTHORIZATION_AND_REGISTER_REQUIRED');a=approve(authorization);reg=load(register);need(reg['purpose']=='PILOT_ADMISSION' and reg['authorization_file_sha256']==sha(Path(authorization).read_bytes())==lock['pilot_identity']['authorization_sha256'],'AUTHORIZATION_MISMATCH');need(reg['protocol_version']=='R3-FEASIBILITY-PROTOCOL-1','REGISTER_PROTOCOL_MISMATCH')
  need(len(reg['participants'])<=6,'REGISTER_EXCEEDS_APPROVED_CEILING')
  for p in reg['participants']:
   need(isinstance(p.get('eligible'),bool) and isinstance(p.get('withdrawn'),bool) and p.get('consent_version')=='R3-PILOT-CONSENT-1','REGISTER_FIELDS_UNRESOLVED');date(p['consent_documented_at']);need(p['participant_id'] not in participants,'REGISTER_DUPLICATE_PARTICIPANT');participants[p['participant_id']]=p
  approved=date(a['approved_at_utc']);registered=date(a['registered_at_utc'])
 synthetic=load(catalog) if purpose=='synthetic' and catalog else None
 if purpose=='synthetic':need(synthetic and synthetic['data_class']=='SYNTHETIC_TEST_FIXTURES_NOT_HUMAN_OBSERVATIONS','SYNTHETIC_CATALOG_REQUIRED')
 for index,path in enumerate(sorted(map(Path,paths),key=lambda p:str(p)),1):
  row={'input_id':f'input_{index:03d}','filename':path.name,'status':'INVALID','reason':None};ledger.append(row)
  try:
   d,raw=load(path,with_bytes=True);digest=sha(raw);row['sha256']=digest
   if purpose=='synthetic':need(any(x['sha256']==digest and x['synthetic'] is True for x in synthetic['files']),'NOT_A_CATALOGUED_SYNTHETIC_FIXTURE')
   i,pilot=identity_for(d,lock,purpose);checks=validate(d,i,pilot);row['warnings']=checks['warnings'];row['participant_id']=d['participant']['pseudonymous_id'];row['session_id']=d['session']['session_id'];row['session_status']=d['session']['status'];row['raw_summary']=summarize(trial_rows(d,row['input_id']))
   need(d['experiment']['mode']=='PILOT24','DEMO_NOT_PILOT_PANEL')
   if purpose=='pilot':
    need(not row['participant_id'].startswith('PILOT-TECH'),'TECHNICAL_TEST_CODE_NOT_PILOT');p=participants.get(row['participant_id']);need(p and p['eligible'] is True and p['withdrawn'] is False and p['consent_version']=='R3-PILOT-CONSENT-1','CONSENT_ELIGIBILITY_OR_WITHDRAWAL');need(registered<=approved<=date(d['session']['started_utc']) and date(p['consent_documented_at'])<=date(d['session']['started_utc']),'PROSPECTIVE_CONSENT_OR_START_UNVERIFIED')
   body=copy.deepcopy(d);body.pop('export',None);fingerprint=sha(json.dumps(body,sort_keys=True,separators=(',',':')).encode());candidates.append((row,d,fingerprint));row.update(status='CANDIDATE',reason=None)
  except (Exception,) as ex:
   row['reason']=str(ex) if isinstance(ex,Invalid) else ('INVALID_JSON_OR_RECORD:'+type(ex).__name__)
   if row.get('participant_id') and row['reason'] in ['TECHNICAL_TEST_CODE_NOT_PILOT','DEMO_NOT_PILOT_PANEL','CONSENT_ELIGIBILITY_OR_WITHDRAWAL','PROSPECTIVE_CONSENT_OR_START_UNVERIFIED']:row['status']='EXCLUDED'
 # Contradictory files claiming the same session are all quarantined; retries
 # differing only in export metadata retain one deterministic representative.
 sessions={}
 for item in candidates:sessions.setdefault(item[1]['session']['session_id'],[]).append(item)
 representatives=[]
 for group in sessions.values():
  if len({x[2] for x in group})>1:
   for row,_,_ in group:row.update(status='CONFLICT',reason='SAME_SESSION_CONFLICT_ALL_QUARANTINED')
   continue
  group.sort(key=lambda x:(x[1]['export']['attempt'],x[0]['filename'],x[0]['input_id']));representatives.append(group[0])
  for row,d,_ in group[1:]:row.update(status='DUPLICATE',reason='EXACT_COPY_OR_EXPORT_RETRY',representative=group[0][0]['input_id'])
 by_pid={}
 for x in representatives:by_pid.setdefault(x[1]['participant']['pseudonymous_id'],[]).append(x)
 included=[]
 for group in by_pid.values():
  group.sort(key=lambda x:(date(x[1]['session']['started_utc']),x[1]['session']['session_id']))
  included.append(group[0]);group[0][0]['status']='INCLUDED'
  for row,_,_ in group[1:]:row.update(status='EXCLUDED',reason='REPEATED_PARTICIPANT_FIRST_ELIGIBLE_SESSION_RETAINED')
 trials=[];summaries=[]
 for row,d,_ in included:
  t=trial_rows(d,row['input_id']);trials+=t;summaries.append({'participant_id':d['participant']['pseudonymous_id'],'session_id':d['session']['session_id'],'session_status':d['session']['status'],**summarize(t)})
 aggregate=summarize(trials);aggregate['participant_count']=len(included);aggregate['complete_sessions']=sum(x['session_status']=='COMPLETE' for x in summaries);aggregate['participant_mean_abstention_rate']=sum(x['abstention_rate_planned'] for x in summaries)/len(summaries) if summaries else None;aggregate['participant_mean_missing_rate']=sum(x['missing_rate_planned'] for x in summaries)/len(summaries) if summaries else None
 aggregate['nonwithdrawn_eligible_codes_from_register']=sum(p.get('eligible') is True and p.get('withdrawn') is False for p in participants.values()) if purpose=='pilot' else None
 aggregate['withdrawn_codes_from_register']=sum(p.get('withdrawn') is True for p in participants.values()) if purpose=='pilot' else None
 denominator=aggregate['nonwithdrawn_eligible_codes_from_register'];aggregate['valid_complete_export_fraction_registered_codes']=aggregate['complete_sessions']/denominator if denominator else None
 aggregate['all_file_return_fraction']='UNAVAILABLE_WITHOUT_SEPARATE_ORGANIZER_RECEIPT_COUNTS'
 conditions=sorted({r['condition'] for r in trials});aggregate['conditions']={c:summarize([r for r in trials if r['condition']==c]) for c in conditions};aggregate['sources']={c:summarize([r for r in trials if r['source_id']==c]) for c in sorted({r['source_id'] for r in trials})}
 return {'report_version':'R3-PILOT-ANALYSIS-1','purpose':purpose,'human_observations_admitted':purpose=='pilot' and bool(included),'interpretation':'Descriptive feasibility only; no population CI, p-value, accuracy, optical calibration or analyzer qualification','ledger':ledger,'participants':summaries,'aggregate':aggregate,'trial_rows':trials,'denominators':{'planned':'24 per included session; missing and U retained','conditional':'eligible A/B/T and nonidentity A/B explicitly separate','screening':'all received file attempts retained in ledger; source portraits and observer repetitions are not independent observations'}}

def write(out,folder,inputs=()):
 folder=Path(folder);targets=[folder/n for n in ['report.json','trials.csv','participants.csv','README.txt']];originals={Path(p).resolve() for p in inputs};need(not any(p.is_symlink() or p.resolve() in originals for p in targets),'OUTPUT_WOULD_OVERWRITE_INPUT');folder.mkdir(parents=True,exist_ok=True);(folder/'report.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 for name,rows in [('trials',out['trial_rows']),('participants',out['participants'])]:
  fields=list(rows[0]) if rows else (['input_id','trial_id','response'] if name=='trials' else ['participant_id','session_id'])
  with (folder/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
   for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
 (folder/'README.txt').write_text('PRIVATE INTAKE REPORT. '+out['purpose'].upper()+' ONLY. Raw inputs untouched. Never publish participant rows or the intake ledger. No inferential or detector-performance claim.\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('inputs',nargs='+',type=Path);p.add_argument('--lock',type=Path,default=P/'BUILD_LOCK.json');p.add_argument('--purpose',choices=['technical','pilot','synthetic'],default='technical');p.add_argument('--register',type=Path);p.add_argument('--authorization',type=Path);p.add_argument('--catalog',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  result=analyze(a.inputs,load(a.lock),a.purpose,a.register,a.authorization,a.catalog);write(result,a.output,a.inputs);print(json.dumps({'purpose':a.purpose,'files':len(result['ledger']),'included_sessions':len(result['participants']),'statuses':{s:sum(r['status']==s for r in result['ledger']) for s in sorted({r['status'] for r in result['ledger']})},'output':str(a.output)}));sys.exit(2 if any(r['status'] in ['INVALID','CONFLICT'] for r in result['ledger']) else 0)
 except Exception as e:print(json.dumps({'status':'REFUSED','reason':str(e) if isinstance(e,Invalid) else type(e).__name__}));sys.exit(1)
