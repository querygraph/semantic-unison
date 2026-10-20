"""Original fake descriptor/call controls: no real uncertain FD or native child."""
import json,types,unittest
from pathlib import Path
from unittest.mock import patch
import observe
from shared_cpu_pool import UnresolvedOwnership

class Ownership(unittest.TestCase):
 def setUp(self):
  self.stamp={'st_dev':1,'st_ino':2,'st_size':1,'st_mtime_ns':3,'st_ctime_ns':4,'st_mode':33024,'st_nlink':1,'st_uid':501}
  self.payload=dict(schema='unison-exiftool-rs-values/1',exiftool_version='13.59',maker_notes=[],warnings=[])
  self.outcome=dict(returncode=0,capture_truncated=False,stdout=json.dumps(self.payload))
  self.build=dict(schema='unison-exiftool-rs-build/1',complete=True,engine_revision=observe.REV,binary='/inert/helper',binary_sha256='a'*64,wrapper_sha256='a'*64)
 def run_case(self,invoke_error=None,close_error=None):
  with patch.object(observe,'load',return_value=self.build),patch.object(observe,'sha',return_value='a'*64),patch.object(observe,'identity',return_value=self.stamp),patch.object(observe.os,'open',return_value=777),patch.object(observe.os,'fstat',return_value=types.SimpleNamespace(**self.stamp)),patch.object(observe.os,'pread',return_value=b'x'),patch.object(observe,'invoke',return_value=self.outcome,side_effect=invoke_error),patch.object(observe,'close_descriptors',side_effect=close_error) as close:
   self.close=close
   return observe.observe(Path('/inert/source'),Path('/inert/build'))
 def test_success_closes_source_once(self):
  self.assertFalse(self.run_case()['interpretations'][0]['transfer_authority'])
  self.close.assert_called_once_with([777])
 def test_helper_unknown_retains_source_and_original_carrier(self):
  original=UnresolvedOwnership('unknown child',retained_fds=(999,))
  with self.assertRaises(UnresolvedOwnership) as error:self.run_case(invoke_error=original)
  self.assertIs(error.exception,original);self.assertIn(777,original.retained_fds);self.close.assert_not_called()
 def test_source_close_unknown_never_retried(self):
  original=UnresolvedOwnership('unknown close',uncertain_fd=777)
  with self.assertRaises(UnresolvedOwnership) as error:self.run_case(close_error=original)
  self.assertIs(error.exception,original);self.close.assert_called_once_with([777])
  self.assertTrue(hasattr(original,'exiftool_observation'))
 def test_known_helper_failure_keeps_call_evidence(self):
  self.outcome['returncode']=2
  with self.assertRaises(ValueError) as error:self.run_case()
  self.assertEqual(error.exception.exiftool_calls[0]['returncode'],2)
  self.close.assert_called_once_with([777])
 def test_truncated_output_refuses(self):
  self.outcome['capture_truncated']=True
  with self.assertRaises(ValueError):self.run_case()
  self.close.assert_called_once_with([777])
if __name__=='__main__':unittest.main()
