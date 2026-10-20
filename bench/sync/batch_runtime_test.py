"""Original runtime composition seams; no actual payload, transport or locks."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from contextlib import ExitStack
from batch_artifacts_test import MemoryStore
from batch_runtime import run
from corpus_workloads import plan


class RuntimeTests(unittest.TestCase):
    def exercise(self, fail=False):
        with tempfile.TemporaryDirectory(prefix='unison-batch-runtime-source-') as temp, ExitStack() as stack:
            root=Path(temp);store=MemoryStore();store.root=str(root);store.identity=dict(device=1,inode=2)
            store.closed=False;store.fd=999;store.fence=lambda:None
            stack.enter_context(patch('batch_runtime.descriptors',return_value=dict(inherited_fds=tuple(range(100,109)))))
            sha=hashlib.sha256(b'shim').hexdigest()
            stack.enter_context(patch('batch_runtime.program',side_effect=lambda p,t:dict(path=str(p),sha256=sha)))
            stack.enter_context(patch('batch_runtime.read_bytes',return_value=b'shim'))
            calls=[]
            def invoke(command, env, **kwargs):
                calls.append(kwargs['name'])
                self.assertEqual(kwargs['pass_fds'],tuple(range(100,109)))
                self.assertEqual(command[command.index('-adobevalidate')+1],'off')
                if fail and len(calls)==2: raise RuntimeError('failed update transport')
                return dict(name=kwargs['name']+'-pair.json',bytes=1,sha256='a'*64)
            stack.enter_context(patch('batch_runtime.invoke',side_effect=invoke))
            def sample(corpus,left,right,*,invoke,record):
                record(dict(stage='seed-intent',planned_files=0));record(dict(stage='seed-inventory',files=[]))
                invoke('seed');record(dict(stage='seed-verified',files=0))
                record(dict(stage='update-inventory',files=[]));invoke('update')
                record(dict(stage='update-verified',observations=[]));invoke('noop')
                record(dict(stage='noop-verified',observations=[]))
                return dict(resource_release_authorized=False)
            stack.enter_context(patch('batch_runtime.sample',side_effect=sample))
            artifact=Mock()
            try:
                pin=run(plan('new-files',count=1024),dict(client='/stock',server='/ox'),str(root),
                        repository='/repository',mode='semantic',workers=3,store=store,
                        resource_rows=[],deadline=__import__('time').monotonic()+100,artifact_check=artifact,sample_runner=sample)
            except BaseException as error:
                error.test_calls=calls;error.test_store=store;raise
            result=store.read_json(pin['name'],expected_sha256=pin['sha256'])
            return result,calls,artifact.call_count

    def test_exact_three_calls_six_events_no_release(self):
        result,calls,checks=self.exercise()
        self.assertEqual(calls,['seed','update','noop']);self.assertEqual(checks,4)
        self.assertEqual(len(result['events']),6);self.assertEqual(len(result['pairs']),3)
        self.assertFalse(result['resource_release_authorized'])
        self.assertFalse(result['per_class_path_audit_complete'])

    def test_update_failure_retains_context_and_starts_no_noop(self):
        from shared_cpu_pool import UnresolvedOwnership
        with self.assertRaises(UnresolvedOwnership) as got:self.exercise(fail=True)
        error=got.exception
        self.assertEqual(error.test_calls,['seed','update'])
        self.assertIn(999,error.retained_fds)
        self.assertTrue(set(range(100,109)).issubset(error.retained_fds))
        self.assertIs(error.batch_runtime['store'],error.test_store)
        self.assertNotIn('BATCH-RESULT.json',error.test_store.files)


if __name__ == '__main__':unittest.main()
