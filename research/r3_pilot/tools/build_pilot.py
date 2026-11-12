"""Distribution-only consent/export preparation; no experiment/geometry redesign.
Default produces a TECHNICAL preview. --authorization requires completed owner
information and prospective registration; never authorizes a study by itself.
"""
from pathlib import Path
import argparse,base64,hashlib,html,json,re
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'research/r3_pilot'
BASE='r3-geometry-reliability-02/index.html'
BASE_SHA='bfb17a546db9c4a108d8b3efeb0cd003558b6f36ea10f3eac25f94378fd1b708'
PUBLIC_FIELDS=['controller_name','contact_and_withdrawal_channel','data_recipients','secure_storage_description','retention_policy','withdrawal_deadline_and_limits','ethics_and_data_protection_review']
def participant_information(c):
 return {k:c.get(k) for k in PUBLIC_FIELDS} if c is not None else {k:None for k in PUBLIC_FIELDS}

FIELDS=['controller_name','contact_and_withdrawal_channel','data_recipients','secure_storage_description','retention_policy','withdrawal_deadline_and_limits','ethics_and_data_protection_review','approved_by','external_registration_reference']
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def utc(s):
 d=datetime.fromisoformat(s.replace('Z','+00:00'));require(d.tzinfo is not None,'Timezone required');return d

def has_actual_value(value):
 if not isinstance(value,str) or not value.strip():return False
 text=value.strip().casefold()
 return not text.startswith('[') and not any(marker in text for marker in ['to complete','à compléter','todo','non renseign','unknown','tbd'])

def authorization(path):
 c=json.loads(Path(path).read_text());require(not c.get('synthetic_fixture'),'Synthetic authorization cannot activate a real collection build');require(c['owner_authorizes_collection'] is True and c['status']=='OWNER_AUTHORIZED_PILOT','Explicit owner authorization missing')
 for name in FIELDS:require(has_actual_value(c.get(name)),'Investigator completion required: '+name)
 require(c['approval_of_six_attempts_and_fourteen_days'] is True,'Operational ceilings require approval')
 require(c['protocol_sha256']==sha((ROOT/'docs/R3_PILOT_PROTOCOL.md').read_bytes()),'Protocol changed after owner approval')
 require(c['participant_information_version']=='R3-PILOT-INFO-1' and c['consent_version']=='R3-PILOT-CONSENT-1','Unsupported information/consent version')
 require(utc(c['registered_at_utc'])<=utc(c['approved_at_utc'])<=datetime.now(timezone.utc),'Registration must precede authorization and neither may be future-dated')
 return c

def replace_once(text,old,new):
 require(text.count(old)==1,'Unexpected baseline source: '+old[:90]);return text.replace(old,new,1)

def build(output,auth=None,baseline=None,*,engineering_harness=False):
 source=Path(baseline or ROOT/BASE).read_bytes().decode('utf-8');require(sha(source.encode())==BASE_SHA,'Unreviewed baseline HTML')
 data_tag=re.search(r'<script id="study-data"[^>]*>(.*?)</script>',source,re.S);b=json.loads(data_tag[1]);original=json.loads(data_tag[1]);active=auth is not None;require(not engineering_harness or (auth is None and output is None),'Engineering harness is memory-only and cannot assert authorization');c=authorization(auth) if active else None;flow=active or engineering_harness
 s=b['settings'];s['pilot_information']={**participant_information(c),'owner_authorizes_collection':True} if active else None;s['pilot_ui_enabled']=flow
 if engineering_harness:s.update(collection_authorized=False,data_class='ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA',study_version='R3-ENGINEERING-HARNESS-1',result_schema_version='R3-CONSENT-HARNESS-1',technical_acknowledgement_version='R3-HARNESS-ACK-1',authorization_note='LOCAL_NONDEPLOYABLE_ENGINEERING_TEST; NO_HUMAN_STUDY_AUTHORIZATION')
 if active:s.update(collection_authorized=True,data_class='HUMAN_FEASIBILITY_PILOT',study_version='R3-FEASIBILITY-1',protocol_version='R3-FEASIBILITY-PROTOCOL-1',result_schema_version='R3-PILOT-RESULT-1',consent_version='R3-PILOT-CONSENT-1',retention_days_proposed=None,contact_mechanism=c['contact_and_withdrawal_channel'],authorization_note='OWNER_AUTHORIZATION_RECORDED_FOR_FEASIBILITY_PILOT; NOT_ETHICS_OR_LEGAL_CERTIFICATION')
 oldapp=(P/'frozen/app.js').read_text();require(oldapp in source,'Baseline app differs from audited frozen app');app=oldapp
 app=replace_once(app,"if(S.collection_authorized!==false||S.data_class!=='TECHNICAL_VALIDATION_NOT_HUMAN_DATA')throw Error('STUDY_NOT_AUTHORIZED');", "if(S.collection_authorized===false&&['TECHNICAL_VALIDATION_NOT_HUMAN_DATA','ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA'].includes(S.data_class))return;if(!(S.collection_authorized===true&&S.data_class==='HUMAN_FEASIBILITY_PILOT'&&S.pilot_information?.owner_authorizes_collection===true))throw Error('STUDY_NOT_AUTHORIZED');")
 app=replace_once(app,"'TEST-'+randomHex(4)","(S.pilot_ui_enabled?'':'TEST-'+randomHex(4))")
 app=replace_once(app,"!/^TEST-[A-Z0-9-]{4,18}$/.test", "!(S.pilot_ui_enabled?/^PILOT-[A-Z0-9-]{4,18}$/:/^TEST-[A-Z0-9-]{4,18}$/).test")
 app=app.replace('TEST- suivi de 4 à 18',('PILOT-' if flow else 'TEST-')+' suivi de 4 à 18').replace('TEST-TITI','PILOT-EXEMPLE' if flow else 'TEST-TITI')
 if flow:app=app.replace('Format du code accepté pour le test technique.','Format du code de pilote accepté.').replace('Veuillez confirmer que vous avez lu les informations du test technique.','Veuillez lire les informations puis indiquer votre consentement avant de démarrer.')
 app=replace_once(app,'research_consent:false,consent_version:S.technical_acknowledgement_version','research_consent:S.collection_authorized===true,consent_version:S.collection_authorized?S.consent_version:S.technical_acknowledgement_version')
 app=replace_once(app,"status:'LOCAL_STRUCTURE_CHECKED_TECHNICAL_ONLY',human_reference_admission:'NOT_ADMITTED',study_authorization:'NOT_AUTHORIZED'", "status:S.collection_authorized?'LOCAL_STRUCTURE_CHECKED_PILOT_NOT_QUALIFICATION':'LOCAL_STRUCTURE_CHECKED_TECHNICAL_ONLY',human_reference_admission:S.collection_authorized?'PENDING_OFFLINE_ADMISSION':'NOT_ADMITTED',study_authorization:S.collection_authorized?'OWNER_AUTHORIZED_PILOT':'NOT_AUTHORIZED'")
 app=replace_once(app,'collection_authorized:false,build_id:B?.build_id','collection_authorized:S?.collection_authorized===true,build_id:B?.build_id')

 if engineering_harness:
  app=replace_once(app,"(function(){'use strict';","(function(){'use strict';if(!['localhost','127.0.0.1','[::1]'].includes(location.hostname)){document.body.textContent='Banc d’essai local uniquement — aucune étude autorisée.';throw Error('HARNESS_LOCAL_ONLY');}")
 source=replace_once(source,oldapp,app)
 if flow:
  updates={
   'Version de validation technique — étude non autorisée.':'Pilote exploratoire sur la perception du flou.',
   "Ne recrutez pas de participants avec ce fichier. Vos interactions servent uniquement à vérifier l'interface et l'export, pas à produire des résultats humains de recherche.":"Votre participation est volontaire. Vous pouvez arrêter sans justification et choisir de ne pas remettre votre fichier. Ce pilote ne constitue pas une validation du détecteur.",
   'Code pseudonyme du test — sans nom':'Code pseudonyme du pilote — sans nom',
   "Ce code reste un identifiant de test technique, jamais une autorisation de recherche.":"N’utilisez ni nom ni adresse électronique. Conservez votre code pour demander le retrait de vos données.",
   "J'ai lu ces informations et je comprends qu'il s'agit d'un test technique, sans participation à une étude scientifique.":"Je suis majeur, j’ai lu les informations ci-dessus et celles remises par l’organisateur. Je participe volontairement et consens à l’export des données décrites, que je choisis ensuite de partager ou non.",
   'Commencer le test de 24 comparaisons':'Commencer les 24 comparaisons',
   "Aucun score de performance n'est calculé. Ce fichier de validation technique n'est pas un jeu de données humain admis.":"Merci. Aucun score personnel n’est calculé. Le fichier contient vos choix ; il sera vérifié hors ligne avant toute analyse du pilote.",
   "Dans cette version, les exports sont marqués « validation technique » et ne doivent pas être recueillis comme réponses d'une étude.":"Ne partagez votre fichier qu’avec le destinataire indiqué dans les informations du pilote.",
   'AI Inspector R3 · validation 1':'AI Inspector R3 · pilote exploratoire',
   'Résultats du test technique AI Inspector R3':'Résultats du pilote AI Inspector R3'
  }
  for old,new in updates.items():require(old in source,'Missing participant text: '+old[:60]);source=source.replace(old,new)
  source=source.replace('TEST- suivi de 4 à 18','PILOT- suivi de 4 à 18').replace('TEST-TITI','PILOT-EXEMPLE')
  old="Contact et suppression : contactez la personne qui vous a remis ce fichier, par le même canal. Aucune approbation éthique n'est revendiquée. Une information et un consentement distincts seront nécessaires avant une étude réelle."
  info='<strong>Informations du pilote · R3-PILOT-INFO-1</strong>'
  labels={'controller_name':'Responsable','contact_and_withdrawal_channel':'Questions et retrait','data_recipients':'Destinataires','secure_storage_description':'Conservation sécurisée','retention_policy':'Durée de conservation','withdrawal_deadline_and_limits':'Retrait et limites','ethics_and_data_protection_review':'Examen applicable'}
  for k,label in labels.items():info+='<br>\n'+label+' : '+html.escape(str(c[k]) if active else 'NON RENSEIGNÉ — aucune autorisation dans ce banc d’essai')
  source=replace_once(source,'<p class="small">'+old+'</p>','')
  source=replace_once(source,'<label class="check"><input id="ack"','<div id="pilot-info" class="notice">'+info+'</div><label class="check"><input id="ack"')
  source=source.replace('recording_enabled:enabled','recording_enabled:enabled') # diagnostics logic retained
  # The five-trial mode is retained as a technical demonstration, never admitted.
  source=source.replace('id="new-id" type="button"','id="new-id" type="button" hidden')
  source=source.replace('id="demo" class="secondary full" disabled','id="demo" class="secondary full" hidden disabled')
  source=source.replace('>VALIDATION TECHNIQUE<','>PILOTE EXPLORATOIRE<')
 if engineering_harness:
  source=source.replace('Pilote exploratoire sur la perception du flou.','SIMULATION TECHNIQUE LOCALE — aucune étude humaine autorisée.')
  source=source.replace('Votre participation est volontaire. Vous pouvez arrêter sans justification et choisir de ne pas remettre votre fichier. Ce pilote ne constitue pas une validation du détecteur.','Banc de vérification du formulaire uniquement. Aucune personne ne participe à une étude et aucun consentement réel n’est recueilli.')
  source=source.replace('Je suis majeur, j’ai lu les informations ci-dessus et celles remises par l’organisateur. Je participe volontairement et consens à l’export des données décrites, que je choisis ensuite de partager ou non.','SIMULATION : je coche le contrôle pour vérifier le formulaire. Ceci ne constitue pas un consentement à une recherche.')
  source=source.replace('>PILOTE EXPLORATOIRE<','>SIMULATION LOCALE<').replace('>Commencer les 24 comparaisons<','>Vérifier les 24 comparaisons<')
  source=source.replace('Le fichier contient vos choix ; il sera vérifié hors ligne avant toute analyse du pilote.','Fichier de test uniquement : ces réponses automatisées ne sont pas des observations humaines.')
 # Only welcome/completion copy and consent/export code differ. Trial DOM/CSS,
 # core scheduling and geometry modules must remain identical to baseline.
 for id_ in ['trial']:
  pattern=rf'<section id="{id_}".*?</section>';require(re.search(pattern,source,re.S)[0]==re.search(pattern,Path(baseline or ROOT/BASE).read_text(),re.S)[0],'Trial DOM changed')
 scripts=list(re.finditer(r'<script id="application">(.*?)</script>',source,re.S));require(len(scripts)==1,'Unexpected application script layout');script=scripts[0][1]
 styles=re.search(r'<style>(.*?)</style>',source,re.S)[1]
 b['app_code_sha256']=sha(script.encode());b['build_id']=sha(('R3-PILOT-READINESS-01|'+b['manifest_sha256']+'|'+b['app_code_sha256']+'|'+sha(source.encode())+'|'+json.dumps(s,sort_keys=True,ensure_ascii=False)).encode())
 raw='\n'+json.dumps(b,indent=2,ensure_ascii=False).replace('</','<\\/')+'\n'
 source=re.sub(r'(<script id="study-data"[^>]*>).*?(</script>)',lambda m:m[1]+raw+m[2],source,flags=re.S)
 source=re.sub(r'(id="study-data"[^>]*data-sha256=")[^"]+',lambda m:m[1]+sha(raw.encode()),source)
 oldscript_hash=base64.b64encode(hashlib.sha256(list(re.finditer(r'<script id="application">(.*?)</script>',Path(baseline or ROOT/BASE).read_text(),re.S))[0][1].encode()).digest()).decode();newscript_hash=base64.b64encode(hashlib.sha256(script.encode()).digest()).decode();source=source.replace('sha256-'+oldscript_hash,'sha256-'+newscript_hash)
 require(b['manifest']==original['manifest'] and b['assets']==original['assets'],'Stimulus change');require(re.search(r'<style>(.*?)</style>',source,re.S)[1]==styles,'CSS changed')
 ident={'build_id':b['build_id'],'application_code_sha256':b['app_code_sha256'],'manifest_sha256':b['manifest_sha256'],'html_sha256':sha(source.encode()),'baseline_html_sha256':BASE_SHA,'collection_authorized':active,'schema_version':s['result_schema_version'],'protocol_version':s['protocol_version'],'authorization_sha256':sha(Path(auth).read_bytes()) if active else None,'engineering_harness':engineering_harness}
 if engineering_harness:return {'html':source,'identity':ident,'human_study_authorization':'NOT_AUTHORIZED','nondeployable':True}
 out=Path(output);protected={ROOT/'index.html',ROOT/BASE,ROOT/'r3-ios-delivery-01-41212170385c/index.html'};require(out.resolve() not in {p.resolve() for p in protected},'Cannot overwrite a preserved public entrypoint');require(auth is None or out.resolve()!=Path(auth).resolve(),'Cannot overwrite investigator configuration');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(source.encode('utf-8'))
 (out.parent/'BUILD_IDENTITY.json').write_text(json.dumps(ident,indent=2)+'\n');return ident
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,default=P/'build/technical-preview/index.html');a.add_argument('--authorization',type=Path);x=a.parse_args();print(json.dumps(build(x.output,x.authorization),indent=2))
