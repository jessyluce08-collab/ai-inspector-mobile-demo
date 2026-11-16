"""Offline schema+manifest+assignment validation. No authenticity or science claim."""
from pathlib import Path
import argparse,json,hashlib,sys,math
from datetime import datetime
ROOT=Path(__file__).resolve().parent
MAX_BYTES=2*1024*1024
class Invalid(ValueError):pass
def require(ok,message):
 if not ok:raise Invalid(message)
def unique_pairs(pairs):
 d={}
 for k,v in pairs:
  require(k not in d,'Duplicate JSON key');d[k]=v
 return d
def load(path):
 path=Path(path);require(path.stat().st_size<=MAX_BYTES,'File exceeds2MiB validation bound')
 return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique_pairs,parse_constant=lambda v:(_ for _ in ()).throw(Invalid('Nonfinite JSON number')))
def sha(b):return hashlib.sha256(b).hexdigest()
def plan(manifest,seed,mode):
 pairs=manifest['pairs'] if mode=='PILOT24' else [p for p in manifest['pairs'] if p['source_id']=='S01'][:5]
 arm=int(seed[-1],16)%2;out=[]
 for p in pairs:
  flip=bool(p['base_flip'])!=bool(arm)
  out.append({'pair':p,'A':p['higher_variant'] if flip else p['lower_variant'],'B':p['lower_variant'] if flip else p['higher_variant'],'key':sha(('R3|order|'+seed+'|'+p['pair_id']).encode())})
 return sorted(out,key=lambda x:(x['key'],x['pair']['pair_id']))
def validate(data,root=ROOT,purpose='technical'):
 import jsonschema
 schema=load(root/'RESULT_SCHEMA.json');errors=sorted(jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).iter_errors(data),key=lambda e:str(e.path))
 require(not errors,'Schema: '+('; '.join(str(list(e.path))+': '+e.message for e in errors[:5])))
 require(purpose=='technical','HUMAN_STUDY_NOT_AUTHORIZED: this release cannot admit research submissions')
 manifest_bytes=(root/'STIMULUS_MANIFEST.json').read_bytes();m=json.loads(manifest_bytes);identity=load(root/'BUILD_IDENTITY.json');e=data['experiment']
 require(e['manifest_sha256']==sha(manifest_bytes)==identity['manifest_sha256'],'Manifest SHA256 mismatch')
 require(e['stimulus_manifest_version']==m['manifest_version'],'Manifest version mismatch')
 require(e['application_build_id']==identity['build_id'] and e['application_code_sha256']==identity['application_code_sha256'],'Build/code identity mismatch')
 rows=data['trials'];expected=plan(m,data['session']['seed'],e['mode']);require(len(rows)==len(expected),'Wrong trial-slot count')
 for i,(r,p) in enumerate(zip(rows,expected),1):
  require(r['trial_id']==f'TR-{i:02d}' and r['order_index']==i,'Wrong/duplicate trial identity/order')
  require(r['pair_id']==p['pair']['pair_id']==r['manifest_reference'],'Pair join mismatch')
  require(r['source_id']==p['pair']['source_id'] and r['source_group_id']==p['pair']['group_id'],'Source/group mismatch')
  require(r['variant_a']==p['A'] and r['variant_b']==p['B'],'A/B assignment mismatch')
  require(r['completed']==(r['response'] is not None) and r['missing_response']==(r['response'] is None) and r['abstained']==(r['response']=='U'),'Response/missing/abstention contradiction')
  if r['completed']:
   require(r['attempted'] and r['response_utc'] is not None and r['display_geometry'] is not None,'Completed trial lacks observation metadata')
   g=r['display_geometry'];require(r['display_warnings']==g['flags'],'Display warnings differ')
   if r['response']!='U':
    require(r['inspection']=={'A':True,'B':True},'Judgment without both views')
    require(g['status'] in ['DISPLAY_GEOMETRY_DOCUMENTED','DOWNSAMPLING_EXPECTED'] and not any(x in g['flags'] for x in ['DISPLAY_GEOMETRY_UNCERTAIN','INSUFFICIENT_REGION_SUPPORT','UNSUPPORTED_LAYOUT']),'Judgment under restricted geometry')
    require(isinstance(g['dpr'],(int,float)) and 0<g['dpr']<=10 and isinstance(g['visual_scale'],(int,float)) and abs(g['visual_scale']-1)<=.01,'Unreliable scale/DPR judgment')
    w,h=g['css']['width'],g['css']['height'];require(isinstance(w,(int,float)) and isinstance(h,(int,float)) and min(w,h)>=160 and min(w,h)*g['dpr']>=240 and abs((w/h)/(384/288)-1)<.01,'Insufficient/distorted judgment support')
  else:require(r['response_utc'] is None and r['elapsed_ms'] is None,'Unanswered trial has fabricated response timing')
  require(not r['visibility_interrupted'] or 'VISIBILITY_INTERRUPTED' in r['technical_invalidation'],'Interruption flag not accounted for')
 n={'planned_trial_count':len(expected),'record_slot_count':len(rows),'recorded_trial_count':sum(r['attempted'] for r in rows),'completed_trial_count':sum(r['completed'] for r in rows),'missing_response_count':sum(r['response'] is None for r in rows),'abstention_count':sum(r['abstained'] for r in rows),'tie_count':sum(r['response']=='T' for r in rows)}
 for k,v in n.items():require(data['integrity'][k]==v,'Count mismatch: '+k)
 summary=[[r['trial_id'],r['variant_a'],r['variant_b'],r['response'],r['completed'],r['abstained']] for r in rows]
 require(data['integrity']['record_summary_sha256']==sha(json.dumps(summary,separators=(',',':'),ensure_ascii=True).encode()),'Record summary digest mismatch')
 status=data['session']['status'];require(status!='COMPLETE' or n['completed_trial_count']==len(rows),'Incomplete session labelled complete')
 require((status=='COMPLETE')==(data['session']['completed_utc'] is not None),'Completion timestamp/status mismatch')
 warnings=[]
 parse=lambda s:datetime.fromisoformat(s.replace('Z','+00:00'))
 if parse(data['session']['ended_utc'])<parse(data['session']['started_utc']):warnings.append('WALL_CLOCK_ORDER_INCONSISTENT')
 if any(r['technical_invalidation'] for r in rows):warnings.append('TECHNICALLY_FLAGGED_TRIALS_PRESENT')
 return {'status':'PASS_TECHNICAL_STRUCTURE_ONLY','human_reference_admission':'NOT_ADMITTED','purpose':purpose,'counts':n,'warnings':warnings,'authenticity':'NOT_ESTABLISHED; hashes do not prove human identity or absence of editing'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--purpose',choices=['technical','research'],default='technical');a=p.parse_args()
 try:r=validate(load(a.result),a.root,a.purpose);print(json.dumps(r,indent=2));sys.exit(0)
 except Exception as ex:print(json.dumps({'status':'FAIL','error':str(ex)},indent=2));sys.exit(1)
