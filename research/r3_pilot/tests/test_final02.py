"""Final bounded checks. All exercised states remain NOT_AUTHORIZED."""
from fixture_factory import *
import unittest,tempfile,re,json,copy
from unittest.mock import patch
from build_pilot import participant_information,has_actual_value
from verify_candidate import verify
from final_release import prepare,check_deployment_approval,install_immutable

class FinalChecks(unittest.TestCase):
 def test_missing_facts_are_not_treated_as_completion(self):
  for value in [None,'','NON RENSEIGNÉ','[À COMPLÉTER]','TODO','unknown']:
   self.assertFalse(has_actual_value(value))
 def test_immutable_metadata_cannot_be_overwritten(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);source=root/'source/index.html';identity=build(source);data=source.read_bytes();target=root/'immutable';install_immutable(target,data,identity);before=(target/'BUILD_IDENTITY.json').read_bytes();install_immutable(target,data,identity);altered=copy.deepcopy(identity);altered['authorization_sha256']='0'*64
   with self.assertRaises(ValueError):install_immutable(target,data,altered)
   self.assertEqual((target/'BUILD_IDENTITY.json').read_bytes(),before)
 def test_no_decisions_no_research_html(self):
  with tempfile.TemporaryDirectory() as t:
   output=Path(t)/'release';result=prepare(P/'INVESTIGATOR_CONFIG.template.json','https://example.invalid/',output);self.assertFalse(result['research_html_created']);self.assertEqual(result['human_study_authorization'],'NOT_AUTHORIZED');self.assertFalse(output.exists());self.assertIn('controller_name',result['remaining_fields'])
 def test_private_investigator_keys_not_embedded(self):
  data={k:None for k in ['controller_name','contact_and_withdrawal_channel']};data.update(private_notes='PRIVATE_NONPERSONAL_SENTINEL',participants=['MUST_NOT_BE_DISCLOSED'],approved_by='PRIVATE_APPROVER_SENTINEL')
  public=participant_information(data);self.assertNotIn('private_notes',public);self.assertNotIn('participants',public);self.assertNotIn('approved_by',public);self.assertNotIn('SENTINEL',json.dumps(public))
 def test_harness_is_memory_only_and_not_authorized(self):
  h=build(None,engineering_harness=True);b=json.loads(re.search(r'<script id="study-data"[^>]*>(.*?)</script>',h['html'],re.S)[1]);self.assertFalse(b['settings']['collection_authorized']);self.assertEqual(b['settings']['data_class'],'ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA');self.assertIsNone(b['settings']['pilot_information']);self.assertIn('HARNESS_LOCAL_ONLY',h['html']);self.assertIn("human_study_authorization:'NOT_AUTHORIZED'",h['html']);self.assertLess(h['html'].index('id="pilot-info"'),h['html'].index('id="ack"'));verify(h['html'],h['identity'])
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'index.html'
   with self.assertRaises(ValueError):build(p,engineering_harness=True)
   self.assertFalse(p.exists())
 def test_harness_cannot_enter_pilot_intake(self):
  lock=A.load(P/'BUILD_LOCK.json');h={'data_class':'ENGINEERING_CONSENT_HARNESS_NOT_HUMAN_DATA'}
  for purpose in ['technical','pilot','synthetic']:
   with self.assertRaises(A.Invalid):A.identity_for(h,lock,purpose)
 def test_no_deployment_without_actual_approval(self):
  with self.assertRaises(ValueError):check_deployment_approval({'approved':False},{})
 def test_actual_candidate_bytes_required(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'index.html';i=build(f);text=f.read_bytes().decode();verify(text,i)
   wrong=copy.deepcopy(i);wrong['html_sha256']='0'*64
   with self.assertRaises(ValueError):verify(text,wrong)
   changed=text.replace('Quelle image est plus floue ?','TEST_MUTATION',1)
   with self.assertRaises(ValueError):verify(changed)
 def test_build_does_not_overwrite_frozen_release(self):
  target=P.parents[1]/'r3-geometry-reliability-02/index.html';before=sha(target.read_bytes())
  with self.assertRaises(ValueError):build(target)
  self.assertEqual(sha(target.read_bytes()),before)
 def test_html_write_is_byte_deterministic(self):
  original=Path.write_text
  def windows_like(self,text,*a,**kw):
   if self.suffix=='.html':return self.write_bytes(text.replace('\n','\r\n').encode())
   return original(self,text,*a,**kw)
  with tempfile.TemporaryDirectory() as t,patch.object(Path,'write_text',windows_like):
   p=Path(t)/'index.html';identity=build(p);self.assertEqual(sha(p.read_bytes()),identity['html_sha256'])
 def test_pilot_metadata_contract_is_distinct_from_harness(self):
  pilot=A.load(P/'PILOT_RESULT_SCHEMA.json');harness=A.load(P/'HARNESS_RESULT_SCHEMA.json');self.assertEqual(pilot['properties']['participant']['properties']['research_consent'],{'const':True});self.assertEqual(harness['properties']['participant']['properties']['research_consent'],{'const':False});self.assertNotEqual(pilot['properties']['data_class'],harness['properties']['data_class']);self.assertEqual(pilot['properties']['trials'],harness['properties']['trials'])
 def test_positive_human_admission_requires_real_decisions(self):
  lock=A.load(P/'BUILD_LOCK.json')
  with tempfile.TemporaryDirectory() as t:
   p=write_fixture(Path(t)/'SYNTHETIC_TECHNICAL.json',record(lock['technical_identities'][0]));reg=P/'ADMISSION_REGISTER.template.json'
   with self.assertRaises(ValueError):A.analyze([p],lock,'pilot',reg,P/'INVESTIGATOR_CONFIG.template.json')
if __name__=='__main__':unittest.main()
