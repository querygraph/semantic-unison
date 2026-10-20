"""Original generated-state→merge-freezer composition, SDK replaced by Python doubles.

No executable/tool/media read by freezer, no actual SDK/IO grant or native plan.
"""
import hashlib,json,os,shutil,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from cached_benchmark.contract import read_bytes
import sdk_fixture_generation_test as generation_controls
import sdk_fixture_generation_owner as generator
from sdk_merge_receiving import freeze,metadata_test
from sdk_merge_receiving.admission_test import EXECUTION,PRODUCTION
from sdk_merge_receiving.entry import request_check
from sdk_merge_receiving.store import Store

class Join(unittest.TestCase):
 def generated(self,root):
  ancestry=Path(root)/'original-control-ancestry.json';ancestry.write_text('{"original_python_doubles_only":true}\n')
  ref=dict(path=str(ancestry),sha256=hashlib.sha256(ancestry.read_bytes()).hexdigest())
  original=generator.generate
  def generate(packet,*args,**kwargs):
   packet=dict(packet,prerequisites=[ref]);return original(packet,*args,**kwargs)
  suite=generation_controls.Composition(methodName='test_complete_one_writer_twelve_validators_and_manifest_ancestry')
  with patch.object(generator,'generate',side_effect=generate):result,seen,checks=suite.run_original(root)
  self.assertEqual((len(seen),len(result['reports']),len(checks)),(13,12,1))
  self.assertTrue(all(row['report']['raw_digest_verified'] is True for row in result['reports']))
  return result
 def prepare(self,root,*,damage=None):
  result=self.generated(root);manifest=Path(result['input_manifest']['path']);value=json.loads(manifest.read_bytes())
  ancestry={r['path'] for r in value['ancestry']}
  if damage:
   target=Path(value['ancestry'][-1]['path']);target.write_bytes(target.read_bytes()+b' ')
  fixture=metadata_test.Metadata();_,base_read,_,packet=fixture.prepare()
  output=Path(freeze.A.REPOSITORY)/'doc'/('current-sdk-merge-control-'+uuid.uuid4().hex[:16]);self.outputs.append(output)
  allowed={str(manifest),*ancestry};reads=[];observed=[]
  def read(name,limit):
   reads.append(name)
   if name.endswith('.dng') or name in {p['path'] for p in packet['binaries'].values()} or name==packet['tool']['path']:raise AssertionError('metadata freezer opened input/executable')
   if name in allowed:return read_bytes(name,limit)
   return base_read(name,limit)
  def observe(name):observed.append(name);return os.lstat(name)
  with patch.object(freeze.inventory,'execution',return_value=EXECUTION),patch.object(freeze.inventory,'production',return_value=PRODUCTION):
   frozen=freeze.prepare(str(manifest),packet['sdk_manifest']['path'],{label:packet['builds'][label]['receipt']['path'] for label in ('stock','ox')},output,read=read,observe=observe)
  self.assertEqual(set(observed),{r['path'] for c in value['cases'] for r in c['states'].values()})
  self.assertEqual(len(set(observed)),12);self.assertTrue(allowed<=set(reads))
  st=output.stat();store=Store(str(output),dict(device=st.st_dev,inode=st.st_ino))
  try:
   plan=store.read_json('PLAN.json',expected_sha256=frozen['plan']['sha256']);request=store.read_json('REQUEST.json',expected_sha256=frozen['request']['sha256'])
   request_check(request,plan,frozen['plan'])
   self.assertEqual(plan['cases'],value['cases']);self.assertEqual(len(plan['source_observations']),12)
   self.assertEqual([c['codec'] for c in plan['cases']],['uncompressed','jpeg','jxl'])
   self.assertFalse(frozen['runtime_admitted']);self.assertFalse(frozen['sdk_invoked']);self.assertFalse(Path(plan['workspace']).exists())
  finally:store.close()
  return frozen
 def setUp(self):self.outputs=[]
 def tearDown(self):
  for p in self.outputs:shutil.rmtree(p,ignore_errors=True)
 def test_original_generated_manifest_freezes_without_payload_or_artifact_read(self):
  with tempfile.TemporaryDirectory(prefix='unison-original-generation-join-',dir='/private/tmp') as root:self.prepare(root)
 def test_changed_generation_ancestry_refuses_before_request_creation(self):
  with tempfile.TemporaryDirectory(prefix='unison-original-generation-join-',dir='/private/tmp') as root:
   with self.assertRaisesRegex(ValueError,'generation ancestry changed'):self.prepare(root,damage=True)
   self.assertFalse((self.outputs[-1]/'REQUEST.json').exists())
if __name__=='__main__':unittest.main()
