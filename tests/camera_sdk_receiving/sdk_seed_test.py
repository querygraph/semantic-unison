"""One tiny generated file and fake invocation; never an SDK/clone proof."""
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import sdk_audit_test as audit_test
import sdk_seed as seed


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-sdk-seed-mock-')
        self.root=Path(self.temp.name)
        (self.root/'left').mkdir();(self.root/'right').mkdir()
        self.data=b'original inert synthetic SDK-seed fixture'
        self.source=self.root/'left/image.dng';self.source.write_bytes(self.data)
        self.source.chmod(0o600);self.target=self.root/'right/image.dng'
        self.sha=hashlib.sha256(self.data).hexdigest();self.calls=0;self.saved=[]
        self.text=None;self.returncode=0
    def tearDown(self):self.temp.cleanup()
    def invoke(self):
        self.calls+=1
        if not self.returncode:self.target.write_bytes(self.data)
        with patch.object(audit_test,'SHA',self.sha),patch.object(audit_test,'SIZE',len(self.data)):
            text=audit_test.log() if self.text is None else self.text
        return {'stdout':text,'stderr':'','supervisor_output':'',
                'returncode':self.returncode,'timed_out':False,'capture_truncated':False,
                'supervisor_capture_truncated':False}
    def run_case(self, deadline=None):
        return seed.exercise(self.root,expected_sha256=self.sha,expected_bytes=len(self.data),
            check_borrowed=lambda:None,invoke=self.invoke,save=self.saved.append,
            deadline_monotonic=time.monotonic()+200 if deadline is None else deadline)
    def test_exact_receiving_candidate_bound_to_single_fake_sdk(self):
        result=self.run_case()
        self.assertTrue(result['complete']);self.assertEqual(self.calls,1)
        self.assertEqual(self.target.read_bytes(),self.data)
        self.assertFalse(result['semantic_eligibility_claimed'])
    def test_absent_helper_proof_retains_and_never_known_failed_prefix(self):
        self.text=''
        with self.assertRaises(seed.UnresolvedOwnership):self.run_case()
        self.assertNotIn('failure',self.saved[-1]);self.assertFalse(self.saved[-1]['complete'])
        self.assertEqual(self.calls,1)
        self.assertIn('outcome',self.saved[-1])
    def test_bound_failed_sdk_is_known_failure_not_pass(self):
        with patch.object(audit_test,'SHA',self.sha),patch.object(audit_test,'SIZE',len(self.data)):
            self.text=audit_test.log(audit_test.report(**{'errors':'1'}))
        with self.assertRaises(ValueError):self.run_case()
        self.assertIn('helper_settlement',self.saved[-1])
        self.assertIn('failure',self.saved[-1]);self.assertEqual(self.calls,1)
    def test_close_uncertainty_bypasses_failed_result(self):
        with patch.object(seed.fallback,'sha',side_effect=[self.sha,seed.UnresolvedOwnership('fixture close unknown')]):
            with self.assertRaises(seed.UnresolvedOwnership):self.run_case()
        self.assertNotIn('failure',self.saved[-1]);self.assertFalse(self.saved[-1]['complete'])
    def test_expired_deadline_refuses_before_invocation(self):
        with self.assertRaises(ValueError):self.run_case(time.monotonic())
        self.assertEqual(self.calls,0)
    def test_existing_receiver_is_never_overwritten(self):
        self.target.write_bytes(b'preserve original fixture')
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.calls,0);self.assertEqual(self.target.read_bytes(),b'preserve original fixture')


if __name__=='__main__':unittest.main()
