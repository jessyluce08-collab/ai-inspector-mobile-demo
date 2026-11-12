"""Version identity only. No external registration, recruitment or approval."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from build_pilot import P,ROOT,BASE,BASE_SHA,authorization,build,sha

def freeze(pilot_identity=None,authorization_file=None,pilot_url=None):
 preview=build(P/'build/technical-preview/index.html');base=json.loads((P/'frozen/BUILD_IDENTITY.json').read_text());base.update(html_sha256=BASE_SHA,collection_authorized=False)
 identity=None
 if pilot_identity:
  if not authorization_file or not pilot_url or not pilot_url.startswith('https://'):raise ValueError('Approved configuration and actual direct HTTPS URL required')
  c=authorization(authorization_file);identity=json.loads(Path(pilot_identity).read_text());assert identity['collection_authorized'] is True and identity['authorization_sha256']==sha(Path(authorization_file).read_bytes())
 source={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((P/'tools').glob('*.py'))};source.update({str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [P/'PILOT_RESULT_SCHEMA.json',P/'frozen/validate_results.py',P/'frozen/RESULT_SCHEMA.json']});documents={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'docs').glob('R3_*.md'))}
 tracked={name:sha((ROOT/name).read_bytes()) for name in ['index.html','r3-geometry-reliability-02/index.html','r3-ios-delivery-01-41212170385c/index.html']}
 lock={'lock_version':'R3-PILOT-LOCK-1','status':'PILOT_VERSION_LOCKED_OWNER_AUTHORIZATION_RECORDED' if identity else 'DRAFT_PREPARATION_NOT_AUTHORIZED','upstream_commit':'8168e3de292b3c284834fb61956b8ac2a57d0a2a','current_candidate_path':BASE,'current_candidate_html_sha256':BASE_SHA,'manifest_sha256':preview['manifest_sha256'],'technical_identities':[base,preview],'pilot_identity':identity,'pilot_url':pilot_url,'analysis_revision_sha256':sha(json.dumps(source,sort_keys=True,separators=(',',':')).encode()),'source_hashes':source,'document_hashes':documents,'preserved_entrypoints':tracked,'external_preregistration':'NOT_PERFORMED' if not identity else c['external_registration_reference'],'external_registration_timestamp':None if not identity else c['registered_at_utc'],'human_study_authorization':'NOT_AUTHORIZED' if not identity else 'OWNER_AUTHORIZATION_RECORDED_NOT_LEGAL_CERTIFICATION','real_device_evidence':'Successful Android/iOS runs owner-reported; no instrumented geometry evidence supplied; no additional geometry campaign required absent a critical reproducible defect'}
 (P/'BUILD_LOCK.json').write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n');return lock
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--pilot-identity',type=Path);a.add_argument('--authorization',type=Path);a.add_argument('--pilot-url');x=a.parse_args();l=freeze(x.pilot_identity,x.authorization,x.pilot_url);print(json.dumps({k:l[k] for k in ['status','current_candidate_html_sha256','manifest_sha256','analysis_revision_sha256','human_study_authorization']},indent=2))
