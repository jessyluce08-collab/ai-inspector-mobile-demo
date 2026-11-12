"""Byte/contract verification only: never grants human-study authority."""
from pathlib import Path
import base64,hashlib,json,re
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'research/r3_pilot'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def bundle(text):return json.loads(re.search(r'<script id="study-data"[^>]*>(.*?)</script>',text,re.S)[1])
def verify(text,identity=None):
 original=(ROOT/'r3-geometry-reliability-02/index.html').read_bytes();require(sha(original)=='bfb17a546db9c4a108d8b3efeb0cd003558b6f36ea10f3eac25f94378fd1b708','Baseline mismatch');old=original.decode();a=bundle(old);b=bundle(text)
 require(a['manifest']==b['manifest'] and a['assets']==b['assets'],'Stimulus/manifest/variant mutation')
 m=(P/'frozen/STIMULUS_MANIFEST.json').read_bytes();require(sha(m)==b['manifest_sha256']=='384a740bf7294494eb91d5b7537ef7a77d7c0b6885b5ae64017742134a65a3cc','Manifest hash mismatch');require(json.loads(m)==b['manifest'],'Manifest object mismatch')
 for asset in b['assets'].values():require(sha(base64.b64decode(''.join(asset['chunks'])))==asset['sha256'],'PNG stream hash mismatch')
 require(len(b['assets'])==20 and len(b['manifest']['pairs'])==24 and sum(x['identity'] for x in b['manifest']['pairs'])==4,'Bank cardinality mismatch')
 extract=lambda pattern,s:re.search(pattern,s,re.S)[1]
 for pattern in [r'(<style>.*?</style>)',r'(<section id="trial".*?</section>)',r'<script id="application">(.*?)/\* Explicitly activated']:require(extract(pattern,old)==extract(pattern,text),'Frozen trial DOM/CSS/core/geometry changed')
 script=extract(r'<script id="application">(.*?)</script>',text);raw=extract(r'<script id="study-data"[^>]*>(.*?)</script>',text);declared=re.search(r'id="study-data"[^>]*data-sha256="([a-f0-9]+)"',text)[1]
 require(sha(raw.encode())==declared,'Bundle content digest mismatch');require(sha(script.encode())==b['app_code_sha256'],'Application digest mismatch');require('sha256-'+base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() in text,'CSP application hash mismatch');require("connect-src 'none'" in text,'Network safeguard changed')
 if identity:
  for k,v in [('html_sha256',sha(text.encode())),('build_id',b['build_id']),('application_code_sha256',b['app_code_sha256']),('manifest_sha256',b['manifest_sha256'])]:require(identity.get(k)==v,'Identity mismatch: '+k)
 return {'status':'PASS_FROZEN_SCIENTIFIC_INPUTS','html_sha256':sha(text.encode()),'manifest_sha256':b['manifest_sha256'],'png_streams':20,'trials':24,'identical_controls':4,'trial_dom_css_core_geometry_identical':True,'physical_display_validation':False,'authorization':'NOT_ESTABLISHED_BY_THIS_CHECK'}
