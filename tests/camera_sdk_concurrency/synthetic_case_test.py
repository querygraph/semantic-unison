import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import synthetic_case as c
from shared_cpu_pool import UnresolvedOwnership
class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        for name in ('left','right'):(self.d/name).mkdir()
        self.saved=[]
    def tearDown(self):self.tmp.cleanup()
    def run_case(self,invoke,build=c.BUILD):
        return c.execute(self.d,tool_build_id=build,invoke=invoke,persist=lambda x:self.saved.append(copy.deepcopy(x)))
    def test_forbids_real_sdk_mode_before_creation(self):
        with self.assertRaises(ValueError):self.run_case(lambda:None,'unison-sdk171-2724-v1-single')
        self.assertFalse(any((self.d/'left').iterdir()))
    def test_call_marker_and_outcome_precede_audit(self):
        outcome=dict(stdout='',stderr='',supervisor_output='')
        def invoke():
            self.assertEqual(self.saved[-1]['phase'],'CALL_MAY_HAVE_STARTED');return outcome
        with self.assertRaises(UnresolvedOwnership):self.run_case(invoke)
        self.assertEqual(self.saved[-1]['outcome'],outcome)
        self.assertNotIn('failure',self.saved[-1])
    def test_malformed_post_call_log_retains_unknown(self):
        with self.assertRaises(UnresolvedOwnership):
            self.run_case(lambda:dict(stdout='[server: validation-process] malformed',stderr='',supervisor_output=''))
        self.assertNotIn('failure',self.saved[-1])
    def test_one_use_namespace_refused(self):
        (self.d/'left/occupied').write_bytes(b'original')
        with self.assertRaises(ValueError):self.run_case(lambda:None)
    def test_write_close_uncertainty_not_ordinary_failure(self):
        with patch.object(c,'create_file',side_effect=UnresolvedOwnership('injected unknown')):
            with self.assertRaises(UnresolvedOwnership):self.run_case(lambda:None)
        self.assertNotIn('failure',self.saved[-1])
    def test_known_preparation_error_preserved(self):
        with patch.object(c,'create_file',side_effect=OSError('injected create refusal')):
            with self.assertRaises(OSError):self.run_case(lambda:None)
        self.assertIn('injected create refusal',self.saved[-1]['failure'])
    def test_two_generated_inputs_and_no_borrowed_source(self):
        def invoke():
            self.assertEqual({p.name:p.read_bytes() for p in (self.d/'left').iterdir()},c.FILES)
            raise OSError('injected pre-call refusal')
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_case(invoke)
        self.assertIsInstance(caught.exception.__cause__,OSError)
        self.assertNotIn('failure',self.saved[-1])
        self.assertEqual(len(self.saved[-1]['sources']),2)
if __name__=='__main__':unittest.main()
