import unittest,tempfile,json,copy,sys,re,hashlib
from pathlib import Path
from fixture_factory import *
class TestIntake(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name);self.lock=A.load(P/'BUILD_LOCK.json');self.d=record(self.lock['technical_identities'][0]);self.path=write_fixture(self.dir/'SYNTHETIC_valid.json',self.d)
 def tearDown(self):self.tmp.cleanup()
 def run_data(self,d=None,others=None):
  p=write_fixture(self.path,d or self.d);return A.analyze([p]+(others or []),self.lock)
 def test_complete(self):
  o=self.run_data();s=o['aggregate'];self.assertEqual(s['responses'],{'A':6,'B':6,'T':6,'U':6});self.assertEqual(s['control_planned'],4);self.assertEqual(s['missing'],0);self.assertFalse(o['human_observations_admitted']);self.assertEqual(s['completed'],24)
 def test_partial(self):
  o=self.run_data(record(self.lock['technical_identities'][0],completed=5));self.assertEqual(o['aggregate']['missing'],19);self.assertEqual(o['aggregate']['planned'],24)
 def test_exact_duplicate(self):
  q=write_fixture(self.dir/'SYNTHETIC_copy.json',self.d);o=self.run_data(others=[q]);self.assertEqual(len(o['participants']),1);self.assertEqual(sum(x['status']=='DUPLICATE' for x in o['ledger']),1)
 def test_export_retry(self):
  d=copy.deepcopy(self.d);d['export']['attempt']=2;q=write_fixture(self.dir/'SYNTHETIC_retry.json',d);o=self.run_data(others=[q]);self.assertEqual(len(o['participants']),1)
 def test_session_conflict(self):
  d=copy.deepcopy(self.d);d['trials'][0]['response']='B';rehash(d);q=write_fixture(self.dir/'SYNTHETIC_conflict.json',d);o=self.run_data(others=[q]);self.assertTrue(all(x['status']=='CONFLICT' for x in o['ledger']));self.assertFalse(o['participants'])
 def test_repeated_participant(self):
  d=copy.deepcopy(self.d);d['session']['session_id']='S-fedcba9876543210';d['session']['started_utc']='2000-01-02T00:01:01Z';q=write_fixture(self.dir/'SYNTHETIC_second.json',d);o=self.run_data(others=[q]);self.assertEqual(len(o['participants']),1);self.assertEqual(sum(x['status']=='EXCLUDED' for x in o['ledger']),1)
 def test_corrupt_and_incompatible_retained(self):
  bad=self.dir/'SYNTHETIC_corrupt.json';bad.write_text('{');d=copy.deepcopy(self.d);d['experiment']['application_build_id']='0'*64;q=write_fixture(self.dir/'SYNTHETIC_wrong.json',d);o=self.run_data(others=[bad,q]);self.assertEqual(sum(x['status']=='INVALID' for x in o['ledger']),2)
 def test_unknown_properties_rejected(self):
  d=copy.deepcopy(self.d);d['participant']['email']='SYNTHETIC_NOT_EMAIL';self.assertEqual(self.run_data(d)['ledger'][0]['reason'],'SCHEMA_INCOMPATIBLE')
 def test_nonfinite_and_duplicate_keys(self):
  for text in ['{"x":NaN}','{"x":1e999}','{"x":1,"x":2}']:
   self.path.write_text(text)
   with self.assertRaises(ValueError):A.load(self.path)
 def test_unsupported_geometry_AB_rejected(self):
  d=copy.deepcopy(self.d);d['trials'][0]['display_geometry']['status']='DISPLAY_GEOMETRY_UNCERTAIN';d['trials'][0]['display_warnings']=['DISPLAY_GEOMETRY_UNCERTAIN'];d['trials'][0]['display_geometry']['flags']=['DISPLAY_GEOMETRY_UNCERTAIN'];self.assertEqual(self.run_data(d)['ledger'][0]['status'],'INVALID')
 def test_U_with_unknown_geometry_retained(self):
  d=copy.deepcopy(self.d);r=d['trials'][3];r['display_geometry']['status']='DISPLAY_GEOMETRY_UNCERTAIN';r['display_warnings']=['DISPLAY_GEOMETRY_UNCERTAIN'];r['display_geometry']['flags']=['DISPLAY_GEOMETRY_UNCERTAIN'];o=self.run_data(d);self.assertEqual(o['aggregate']['responses']['U'],6)
 def test_flagged_responses_not_lost(self):
  d=copy.deepcopy(self.d);d['trials'][0]['technical_invalidation']=['VISIBILITY_INTERRUPTED'];d['trials'][0]['visibility_interrupted']=True;o=self.run_data(d);self.assertEqual(o['aggregate']['responses']['A'],6);self.assertEqual(o['aggregate']['technically_flagged'],1);self.assertEqual(o['aggregate']['analysis_eligible'],23)
 def test_identical_not_accuracy_filter(self):
  d=copy.deepcopy(self.d)
  manifest=A.load(P/'frozen/STIMULUS_MANIFEST.json');ids={x['pair_id'] for x in manifest['pairs'] if x['identity']}
  for r in d['trials']:
   if r['pair_id'] in ids:r.update(response='A',abstained=False)
  rehash(d);o=self.run_data(d);self.assertEqual(o['aggregate']['control_AB_reports'],4);self.assertEqual(len(o['participants']),1)
 def test_missing_not_transformed_to_U_or_T(self):
  o=self.run_data(record(self.lock['technical_identities'][0],completed=0));self.assertEqual(o['aggregate']['missing'],24);self.assertEqual(o['aggregate']['responses'],dict.fromkeys('ABTU',0))
 def test_order_and_digest_corruption(self):
  for field in ['trial_id','variant_a']:
   d=copy.deepcopy(self.d);d['trials'][0][field]='SYNTHETIC_INVALID';self.assertEqual(self.run_data(d)['ledger'][0]['status'],'INVALID')
 def test_no_promotion_of_technical(self):
  with self.assertRaises(A.Invalid):A.identity_for(self.d,self.lock,'pilot')
 def test_diagnostic_not_response(self):
  o=self.run_data({'diagnostic_schema_version':'R3-GEOMETRY-DIAGNOSTIC-2','data_class':'TECHNICAL_DIAGNOSTIC_NOT_HUMAN_OBSERVATIONS'});self.assertEqual(o['ledger'][0]['status'],'INVALID')
 def test_reproducible_summaries_and_raw_immutability(self):
  before=self.path.read_bytes();a=self.run_data();b=self.run_data();self.assertEqual(a,b);self.assertEqual(before,self.path.read_bytes());A.write(a,self.dir/'report');self.assertTrue((self.dir/'report/participants.csv').exists())
 def test_synthetic_catalog_required(self):
  with self.assertRaises(A.Invalid):A.analyze([self.path],self.lock,'synthetic')
 def test_output_cannot_overwrite_original(self):
  report=self.dir/'report.json';write_fixture(report,self.d);before=report.read_bytes();o=self.run_data()
  with self.assertRaises(A.Invalid):A.write(o,self.dir,[report])
  self.assertEqual(report.read_bytes(),before)
 def test_protocol_lock_detects_tampering(self):
  lock=copy.deepcopy(self.lock);key=next(iter(lock['source_hashes']));lock['source_hashes'][key]='0'*64
  with self.assertRaises(A.Invalid):A.analyze([self.path],lock)
class TestBuilder(unittest.TestCase):
 def test_incomplete_authorization_refused(self):
  from build_pilot import authorization
  with self.assertRaises(ValueError):authorization(P/'INVESTIGATOR_CONFIG.template.json')
 def test_preview_invariance_and_no_authority(self):
  with tempfile.TemporaryDirectory() as t:
   target=Path(t)/'preview/index.html';identity=build(target);self.assertFalse(identity['collection_authorized'])
   base=(P.parents[1]/'r3-geometry-reliability-02/index.html').read_text();newtext=target.read_text();old=json.loads(re.search(r'<script id="study-data"[^>]*>(.*?)</script>',base,re.S)[1]);new=json.loads(re.search(r'<script id="study-data"[^>]*>(.*?)</script>',newtext,re.S)[1]);self.assertEqual(old['assets'],new['assets']);self.assertEqual(old['manifest'],new['manifest']);self.assertEqual(re.search(r'<style>.*?</style>',base,re.S)[0],re.search(r'<style>.*?</style>',newtext,re.S)[0]);self.assertEqual(re.search(r'<section id="trial".*?</section>',base,re.S)[0],re.search(r'<section id="trial".*?</section>',newtext,re.S)[0]);prefix=lambda s:re.search(r'<script id="application">(.*?)/\* Explicitly activated',s,re.S)[1];self.assertEqual(prefix(base),prefix(newtext));self.assertFalse(new['settings']['collection_authorized']);self.assertIn("human_study_authorization:'NOT_AUTHORIZED'",newtext)
if __name__=='__main__':unittest.main()
