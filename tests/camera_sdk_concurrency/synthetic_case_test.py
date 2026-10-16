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
    def outcome(self,*,overlap=True,corrupt=False,returncode=0):
        frames=[]
        for i,(name,data) in enumerate(c.FILES.items()):
            c.create_file(self.d/'right'/name,b'wrong' if corrupt and i==1 else data)
            digest=c.artifact_sha(self.d/'left'/name);pid=21+i;size=len(data)
            fields=[digest,str(size),c.BUILD,'valid','success','valid','0','0']
            receipt=('UNISON-DNG-VALIDATION 1\n'+''.join(k+' '+v+'\n' for k,v in zip(c.sdk_audit.FIELDS,fields))+'END\n').encode().hex()
            first,last=(1,3) if i==0 else (2,4) if overlap else (4,5)
            frames.append(f'[server: validation-process] Helper result v0 pid={pid} status=exit:0 outcome=completed candidate-sha256={digest} candidate-bytes={size} capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex={receipt} stderr-hex=\n'
              f'[server: validation-group] Retained group v0 pid={pid} candidate-sha256={digest} other-members=0\n'
              f'[server: validation-live] Live span v0 owner-pid=31 pid={pid} candidate-sha256={digest} candidate-bytes={size} clock=monotonic-seconds-v0 samples=3 valid=true first={first} last={last}\n')
        return dict(stdout=''.join(frames),stderr='',supervisor_output='',returncode=returncode,
                    timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,
                    proxy=dict(server_pid=31,fault=None))
    def test_positive_case_persists_outcome_before_verification(self):
        result=self.run_case(self.outcome)
        self.assertTrue(result['complete'])
        self.assertEqual(result['phase'],'VERIFIED_TWO_SYNTHETIC_CANDIDATES')
        self.assertTrue(result['validation']['overlap_observed'])
        self.assertFalse(result['sdk_validation_claimed'])
        states=[s for s in self.saved if 'outcome' in s]
        self.assertNotIn('helper_settlements',states[0])
        self.assertEqual(len(result['helper_settlements']),2)
    def test_serial_functional_result_does_not_claim_overlap(self):
        result=self.run_case(lambda:self.outcome(overlap=False))
        self.assertTrue(result['complete']);self.assertFalse(result['validation']['overlap_observed'])
    def test_corrupt_output_preserves_known_helpers_and_failure(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):self.run_case(lambda:self.outcome(corrupt=True))
        self.assertEqual(len(self.saved[-1]['helper_settlements']),2)
        self.assertFalse(self.saved[-1]['complete'])
    def test_failed_call_cannot_become_functional_success(self):
        with self.assertRaises(ValueError):self.run_case(lambda:self.outcome(returncode=1))
        self.assertEqual(len(self.saved[-1]['helper_settlements']),2)
        self.assertFalse(self.saved[-1]['complete'])
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
