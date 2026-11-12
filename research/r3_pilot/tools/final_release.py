"""Conditional release. Never supplies approval, registers, publishes or recruits.
prepare requires an actual completed investigator declaration; absent decisions
produce no research HTML. verify-served additionally requires exact-byte
prospective deployment approval and only performs a static GET.
"""
from pathlib import Path
import argparse,json,tempfile,shutil,urllib.request,urllib.parse
from datetime import datetime,timezone
from build_pilot import ROOT,P,authorization,build,sha,PUBLIC_FIELDS,has_actual_value
from verify_candidate import verify,require

def now():return datetime.now(timezone.utc).isoformat()
def missing(config):
 keys=PUBLIC_FIELDS+['approved_by','external_registration_reference','registered_at_utc','approved_at_utc','protocol_sha256']
 bad=[]
 for k in keys:
  v=config.get(k)
  if not has_actual_value(v):bad.append(k)
 for k in ['owner_authorizes_collection','approval_of_six_attempts_and_fourteen_days']:
  if config.get(k) is not True:bad.append(k)
 if config.get('status')!='OWNER_AUTHORIZED_PILOT':bad.append('status')
 return bad

def participant_materials(c,folder,url):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 text=(ROOT/'docs/R3_PARTICIPANT_INFORMATION.md').read_text()
 replacements=[('[À COMPLÉTER PAR L’INVESTIGATEUR]',c['controller_name']),('[CANAL À COMPLÉTER]',c['contact_and_withdrawal_channel']),('[À COMPLÉTER]',c['data_recipients']),('[CANAL ET DESTINATAIRE À COMPLÉTER]',c['data_recipients']),('[EMPLACEMENT ET ACCÈS À COMPLÉTER]',c['secure_storage_description']),('[DURÉE/RÈGLE À COMPLÉTER]',c['retention_policy']),('[À COMPLÉTER]',c['withdrawal_deadline_and_limits']),('[EXAMEN ET DÉCISION RÉELS À COMPLÉTER ; aucune approbation inventée]',c['ethics_and_data_protection_review'])]
 for old,new in replacements:require(old in text,'Participant information template changed');text=text.replace(old,new,1)
 text=text.replace('**Projet de document : ne pas envoyer avant validation de l’organisateur.**','Version renseignée à partir de la déclaration réelle de l’investigateur. Ne diffuser qu’après approbation du candidat exact et vérification de publication.')
 require('[À COMPLÉTER' not in text and '[NON RENSEIGNÉ' not in text,'Participant information incomplete')
 files={'PARTICIPANT_INFORMATION_FR.md':text,'PARTICIPANT_EXPORT_FR.md':(ROOT/'docs/R3_PARTICIPANT_EXPORT_INSTRUCTIONS.md').read_text(),'CONSENT_PROCEDURE_FR.md':(ROOT/'docs/R3_CONSENT_AND_PRIVACY.md').read_text()}
 message=(ROOT/'docs/R3_RECRUITMENT_MESSAGE.md').read_text()
 for old,new in [('[RESPONSABLE/CONTACT]',c['controller_name']+' / '+c['contact_and_withdrawal_channel']),('[LIEN HTTPS PILOTE VERROUILLÉ — PAS LE LIEN DE DÉMONSTRATION]',url),('[DESTINATAIRE/CANAL]',c['data_recipients']),('[RÈGLES APPROUVÉES]',c['retention_policy']+' / '+c['withdrawal_deadline_and_limits']),('[CONTACT RÉEL]',c['contact_and_withdrawal_channel'])]:message=message.replace(old,new)
 files['INVITATION_AFTER_DEPLOYMENT_APPROVAL_ONLY_FR.md']=message
 for name,content in files.items():(folder/name).write_bytes(content.encode('utf-8'))
 return {name:sha(content.encode()) for name,content in files.items()}

def prepare(config_path,base_url,output=None):
 config=json.loads(Path(config_path).read_text());pending=missing(config)
 if pending:return {'status':'PENDING_INVESTIGATOR_DECISIONS','remaining_fields':pending,'research_html_created':False,'human_study_authorization':'NOT_AUTHORIZED'}
 c=authorization(config_path) # Never bypassed or mocked by the engineering harness.
 u=urllib.parse.urlsplit(base_url);require(u.scheme=='https' and u.hostname and not u.username and not u.query and not u.fragment,'A direct HTTPS site base without identifiers/credentials is required')
 output=Path(output or P/'build/release-package');output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='r3-candidate-',dir=output) as temp:
  temp=Path(temp);identity=build(temp/'index.html',config_path);text=(temp/'index.html').read_bytes().decode();invariance=verify(text,identity)
  # This exact-byte positive workflow can only run after real owner declarations.
  # It uses a reserved technical code, no human observer or pilot admission.
  from post_authorization_smoke import run
  evidence=run(temp/'index.html',identity,config_path)
  require(evidence['status']=='PASS' and evidence['html_sha256']==identity['html_sha256'],'Exact candidate technical workflow did not pass')
  name='r3-pilot-'+identity['build_id'][:12];directory=output/name
  if directory.exists():require((directory/'index.html').read_bytes()==(temp/'index.html').read_bytes(),'Immutable release path already contains different bytes')
  else:directory.mkdir();shutil.copyfile(temp/'index.html',directory/'index.html')
  (directory/'BUILD_IDENTITY.json').write_text(json.dumps(identity,indent=2)+'\n')
  url=base_url.rstrip('/')+'/'+name+'/'
  materials=participant_materials(c,output/'participant-materials',url)
  from freeze_lock import freeze
  lock=freeze(directory/'BUILD_IDENTITY.json',config_path,url)
  lockpath=output/'BUILD_LOCK.json';lockpath.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n')
  evidencepath=output/'EXACT_CANDIDATE_TEST.json';evidencepath.write_text(json.dumps(evidence,indent=2)+'\n')
  review={'approved':False,'candidate_html_sha256':identity['html_sha256'],'direct_https_url':url,'approved_by':None,'approved_at_utc':None,'note':'Investigator must review this exact candidate before approving deployment. This generated file grants no permission.'}
  (output/'DEPLOYMENT_APPROVAL.template.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
  receipt={'status':'PREPARED_NOT_PUBLISHED_AWAITING_EXACT_DEPLOYMENT_APPROVAL','created_utc':now(),'directory':str(directory),'direct_https_url':url,'identity':identity,'participant_material_hashes':materials,'protocol_sha256':sha((ROOT/'docs/R3_PILOT_PROTOCOL.md').read_bytes()),'schema_sha256':sha((P/'PILOT_RESULT_SCHEMA.json').read_bytes()),'configuration_sha256':sha(Path(config_path).read_bytes()),'analysis_revision_sha256':lock['analysis_revision_sha256'],'invariance':invariance,'technical_test':str(evidencepath),'public_url_verified':False,'human_observations_admitted':False,'production_integration':'NONE'}
  (output/'PREPARED_RELEASE.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');return receipt

def check_deployment_approval(approval,receipt):
 require(approval.get('approved') is True,'Exact deployment approval missing')
 require(approval.get('candidate_html_sha256')==receipt['identity']['html_sha256'],'Approved HTML hash differs')
 require(approval.get('direct_https_url')==receipt['direct_https_url'],'Approved URL differs')
 require(isinstance(approval.get('approved_by'),str) and approval['approved_by'].strip(),'Approver missing')
 t=datetime.fromisoformat(approval['approved_at_utc'].replace('Z','+00:00'));created=datetime.fromisoformat(receipt['created_utc'].replace('Z','+00:00'));require(t.tzinfo is not None and created<=t<=datetime.now(timezone.utc),'Approval must follow candidate preparation and not be future-dated')

def served(receipt_path,approval_path):
 receipt=json.loads(Path(receipt_path).read_text());approval=json.loads(Path(approval_path).read_text());check_deployment_approval(approval,receipt)
 url=receipt['direct_https_url'];u=urllib.parse.urlsplit(url);require(u.scheme=='https' and u.hostname and not u.username and not u.query and not u.fragment,'Unsafe deployment URL')
 req=urllib.request.Request(url,headers={'User-Agent':'R3-static-release-verifier/1'})
 with urllib.request.urlopen(req,timeout=30) as response:
  data=response.read(8*1024*1024+1);require(len(data)<=8*1024*1024,'Unexpectedly large served artifact');resolved=response.url;status=response.status
 require(status==200 and urllib.parse.urlsplit(resolved).scheme=='https','HTTPS response not successful');require(sha(data)==receipt['identity']['html_sha256'],'Served bytes differ from approved candidate')
 return {'status':'PASS_SERVED_BYTES','requested_url':url,'resolved_url':resolved,'http_status':status,'html_sha256':sha(data),'checked_utc':now(),'human_observations_collected':False,'real_device_validation':'NOT_ESTABLISHED_BY_HTTP_GET'}
if __name__=='__main__':
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='command',required=True);a=sp.add_parser('prepare');a.add_argument('--config',type=Path,required=True);a.add_argument('--base-url',required=True);a.add_argument('--output',type=Path);a=sp.add_parser('verify-served');a.add_argument('--receipt',type=Path,required=True);a.add_argument('--approval',type=Path,required=True);a.add_argument('--output',type=Path)
 a=p.parse_args()
 try:
  out=prepare(a.config,a.base_url,a.output) if a.command=='prepare' else served(a.receipt,a.approval)
  if a.command=='verify-served' and a.output:a.output.write_text(json.dumps(out,indent=2)+'\n')
  print(json.dumps(out,indent=2,ensure_ascii=False));raise SystemExit(3 if out['status']=='PENDING_INVESTIGATOR_DECISIONS' else 0)
 except Exception as ex:print(json.dumps({'status':'REFUSED','reason':str(ex),'published':False},ensure_ascii=False));raise SystemExit(1)
