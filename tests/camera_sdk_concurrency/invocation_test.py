import hashlib,os,tempfile,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import invocation as v
from shared_cpu_pool import UnresolvedOwnership
B=dict(path='/inert/current-unison',sha256='a'*64,label='stock')
T=dict(path='/inert/current-validator',sha256='b'*64,threads=1,build_id='synthetic')
class Calls(unittest.TestCase):
    def call(self,deadline=None):
        return v.Invoker('/private/tmp/u-concurrent',binary=B,tool=T,journal=Mock(),script_pins={n:'c'*64 for n in v.SCRIPT_NAMES},deadline=deadline or time.monotonic()+300)
    def sha(self,path):return 'a'*64 if str(path)==B['path'] else 'b'*64 if str(path)==T['path'] else 'c'*64
    def test_intent_precedes_measure_and_outcome_persisted(self):
        call=self.call();outcome={'returncode':0}
        def measure(argv,env,seconds,script,**kw):
            call.journal.begin.assert_called_once();call.journal.finish.assert_not_called()
            self.assertEqual(seconds,120);self.assertTrue(kw['strict_group_settlement']);return outcome
        with patch.object(v,'artifact_sha',side_effect=self.sha),patch.object(v,'measure_invocation',side_effect=measure) as measured:
            self.assertIs(call(),outcome)
            with self.assertRaises(ValueError):call()
        measured.assert_called_once();call.journal.finish.assert_called_once_with(outcome)
    def test_failure_outcome_persisted_and_no_retry(self):
        call=self.call();outcome={'returncode':1}
        with patch.object(v,'artifact_sha',side_effect=self.sha),patch.object(v,'measure_invocation',side_effect=v.InvocationFailure(outcome)):
            with self.assertRaises(v.InvocationFailure):call()
        call.journal.finish.assert_called_once_with(outcome)
        with self.assertRaises(ValueError):call()
    def test_refusal_before_intent_consumes_instance(self):
        call=self.call()
        with patch.object(v,'artifact_sha',return_value='d'*64),patch.object(v,'measure_invocation') as m:
            with self.assertRaises(ValueError):call()
            with self.assertRaises(ValueError):call()
        m.assert_not_called();call.journal.begin.assert_not_called()
    def test_deadline_before_artifacts(self):
        call=self.call(time.monotonic()+1)
        with patch.object(v,'artifact_sha') as hashed:
            with self.assertRaises(ValueError):call()
        hashed.assert_not_called()
    def test_journal_failure_prevents_dispatch(self):
        call=self.call();call.journal.begin.side_effect=OSError('injected persistence failure')
        with patch.object(v,'artifact_sha',side_effect=self.sha),patch.object(v,'measure_invocation') as m:
            with self.assertRaises(OSError):call()
        m.assert_not_called()
    def test_artifact_hash_and_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'artifact';p.write_bytes(b'original tiny execution artifact')
            self.assertEqual(v.artifact_sha(p),hashlib.sha256(p.read_bytes()).hexdigest())
            link=Path(tmp)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):v.artifact_sha(link)
    def test_close_uncertainty_preserves_original_and_no_retry(self):
        s=os.stat(__file__)
        with patch.object(v.os,'open',return_value=999999),patch.object(v.os,'fstat',return_value=s), \
             patch.object(v.os,'read',side_effect=OSError('injected artifact read')), \
             patch.object(v.os,'close',side_effect=OSError('injected uncertain close')) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:v.artifact_sha('/never/opened')
        close.assert_called_once_with(999999)
        self.assertIsInstance(caught.exception.original_failure,OSError)
        self.assertEqual(len(caught.exception.uncertain_closes),1)
if __name__=='__main__':unittest.main()
