"""Fake resource/child entry controls; original disposable metadata only."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from mixed_peer_compatibility import entry as e
from shared_cpu_pool import UnresolvedOwnership

class Held(BaseException):pass
class Lease:
    def __init__(self,fds):self.fds=fds;self.closed=False
    def close_after_verified_settlement(self,**proof):
        assert all(proof.values());self.closed=True

class Entry(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-mixed-entry-control-')
        self.root=Path(self.temp.name)/'unused'
        self.cpu=Lease(tuple(range(10000,10008)));self.io=Lease((9999,));self.child=None
        self.plan=dict(workspace=str(self.root),artifacts={k:{'path':'/inert/'+k} for k in ('stock','ox','old-stock')})
        self.admission=dict(state='ROOT_ADMITTED_ONE_MIXED_PEER_JOB',plan_sha256='a'*64,workspace=str(self.root),start_deadline_unix=time.time()+60)
    def tearDown(self):self.temp.cleanup()
    def spawn(self,*args,**kw):
        self.assertEqual(kw['pass_fds'],self.io.fds+self.cpu.fds)
        self.child=types.SimpleNamespace(pid=123)
        return self.child
    def run_owner(self,*,busy=False,unknown=False,source_failure=False):
        original=e.os.fstat
        def fstat(fd):return types.SimpleNamespace(st_dev=1,st_ino=fd) if fd>=9999 else original(fd)
        with ExitStack() as stack:
            stack.enter_context(patch.object(e,'require_ownership_support'))
            check=stack.enter_context(patch.object(e,'checked_plan',return_value=self.plan))
            if source_failure:check.side_effect=[self.plan,ValueError('source changed')]
            stack.enter_context(patch.object(e,'read_manifest',return_value=self.admission))
            stack.enter_context(patch.object(e.Pool,'read',return_value=object()))
            stack.enter_context(patch.object(e.GlobalPool,'read',return_value=object()))
            stack.enter_context(patch.object(e,'authorized_unison_tokens',return_value=tuple(range(8))))
            stack.enter_context(patch.object(e,'read',return_value=b'inert'))
            stack.enter_context(patch.object(e,'try_io_cpu_bundle',return_value=None if busy else (self.io,self.cpu)))
            stack.enter_context(patch.object(e.os,'fstat',side_effect=fstat))
            stack.enter_context(patch.object(e,'OwnedGroup',side_effect=self.spawn))
            observe=stack.enter_context(patch.object(e,'observe_and_reap',return_value={'functional_pass':True}))
            if unknown:observe.side_effect=UnresolvedOwnership('unknown group',retained_fds=(999,))
            stack.enter_context(patch.object(e,'retain',side_effect=Held))
            return e.owner('/inert/plan','a'*64,'/inert/admission','b'*64)
    def test_success_closed(self):
        self.assertEqual(self.run_owner(),0);self.assertTrue(self.cpu.closed and self.io.closed)
        self.assertTrue((self.root/'CLOSED.json').exists())
    def test_contention_no_launch(self):
        self.assertEqual(self.run_owner(busy=True),2);self.assertIsNone(self.child)
        self.assertTrue((self.root/'NOT-STARTED.json').exists())
    def test_unknown_retains(self):
        with self.assertRaises(Held):self.run_owner(unknown=True)
        self.assertFalse(self.cpu.closed or self.io.closed)
        self.assertFalse((self.root/'CLOSED.json').exists())
    def test_prelaunch_source_refusal_closes_bundle(self):
        self.assertEqual(self.run_owner(source_failure=True),2)
        self.assertTrue(self.cpu.closed and self.io.closed);self.assertIsNone(self.child)
class ArtifactBinding(unittest.TestCase):
    def setUp(self):
        self.plan={'current_builds':{label:{'path':'/inert/'+label+'.json','sha256':'a'*64} for label in ('stock','ox')},
                   'artifacts':{label:{'path':'/inert/'+label,'sha256':'b'*64} for label in ('stock','ox','old-stock')}}
        self.mutate=lambda build:None
    def check(self):
        def receipt(path,sha):
            label=Path(path).stem
            build=dict(complete=True,build_exit=0,selftest_exit=0,binary='/inert/'+label,binary_sha256='b'*64,
                       compiler='/inert/compiler',compiler_sha256='b'*64,source_sha256={'src/copy.ml':'b'*64})
            self.mutate(build);return build
        with patch.object(e,'read_manifest',side_effect=receipt),patch.object(e,'digest',return_value='b'*64):
            e.verify_artifacts(self.plan)
    def test_build_binding(self):self.check()
    def test_failed_selftest(self):
        self.mutate=lambda build:build.update(selftest_exit=1)
        with self.assertRaises(ValueError):self.check()
    def test_wrong_binary(self):
        self.mutate=lambda build:build.update(binary='/inert/other')
        with self.assertRaises(ValueError):self.check()
    def test_parent_source_escape(self):
        self.mutate=lambda build:build.update(source_sha256={'src/../escape':'b'*64})
        with self.assertRaises(ValueError):self.check()
class WorkerPreflight(unittest.TestCase):
    def test_ordinary_refusal_emits_no_calls(self):
        with tempfile.TemporaryDirectory(prefix='unison-mixed-refusal-') as temp:
            packet=Path(temp)/'WORKER-PACKET.json'
            with patch.object(e,'load',side_effect=ValueError('bad packet')),patch.object(e,'execute') as execute:
                self.assertEqual(e.worker(packet),1)
                execute.assert_not_called()
            import json
            result=json.loads((Path(temp)/'WORKER-RESULT.json').read_text())
            self.assertTrue(result['no_calls_started']);self.assertEqual(result['invocations'],[])
    def test_uncertain_packet_close_is_not_no_calls_release(self):
        with tempfile.TemporaryDirectory(prefix='unison-mixed-refusal-') as temp:
            original=UnresolvedOwnership('packet close uncertain',uncertain_fd=999)
            with patch.object(e,'load',side_effect=original),patch.object(e,'retain',side_effect=Held) as held:
                with self.assertRaises(Held):e.worker(Path(temp)/'WORKER-PACKET.json')
            self.assertIs(held.call_args.args[1],original)
            self.assertFalse((Path(temp)/'WORKER-RESULT.json').exists())
if __name__=='__main__':unittest.main()
