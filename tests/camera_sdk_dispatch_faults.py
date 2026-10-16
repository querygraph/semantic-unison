"""Mock parent/leases plus original four-byte worker; no SDK/native/EX IO.

External to the frozen SDK execution closure: adds qualification evidence without
rewriting a reviewed plan. Fake process observations are never actual terminals.
"""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests/camera_sdk_receiving'))
import sdk_worker_test
import sdk_execute
import shared_dispatch as dispatch


class Retained(BaseException):
    pass


class Lease:
    def __init__(self,count,events,label):
        self.fds=tuple(os.open('/dev/null',os.O_RDONLY) for _ in range(count))
        self.events=events;self.label=label;self.closed=False
    def close_after_verified_settlement(self,**proof):
        assert all(value is True for value in proof.values())
        self.events.append('close:'+self.label)
        assert not self.closed
        self.closed=True
        for fd in self.fds:os.close(fd)
    def dispose_fixture(self):
        # Only original /dev/null fixtures, no child or SDK was created. This
        # is not a process-settlement proof or a production retention recovery.
        if not self.closed:
            for fd in self.fds:os.close(fd)
            self.closed=True


class Controls(unittest.TestCase):
    def setUp(self):
        self.worker=sdk_worker_test.Controls();self.worker.setUp()
        self.events=[];self.cpu=Lease(8,self.events,'cpu');self.io=Lease(1,self.events,'io')
        self.live=False;self.worker_exit=0;self.held=None
    def tearDown(self):
        self.cpu.dispose_fixture();self.io.dispose_fixture();self.worker.tearDown()
    def prepare(self,*,invalid=False):
        self.worker.invalid=invalid
        if invalid:
            with self.assertRaises(ValueError):self.worker.execute()
        else:self.worker.execute()
        return json.loads((self.worker.workspace/'RESULT.json').read_text())
    def run_parent(self):
        outer=self
        class CPU:
            def try_acquire(self,indexes):
                outer.events.append('acquire:cpu');return outer.cpu
        class IO:
            def try_acquire(self):
                outer.events.append('acquire:io');return outer.io
        class Owner:
            pid=900001;reaped=False
            def __init__(self,*args,**kwargs):
                outer.events.append('spawn:fake-worker')
                assert set(kwargs['pass_fds'])==set(outer.cpu.fds+outer.io.fds)
            def await_terminal(self,seconds):
                outer.events.append('await:fake-worker');return not outer.live
        def settle(child,deadline):
            self.events.append('settle:fake-worker')
            self.assertFalse(self.cpu.closed or self.io.closed)
            child.reaped=True
            return {'pid':child.pid,'returncode':self.worker_exit,'reaped':True,
                    'other_group_members_absent_before_reap':True,'timed_out':False}
        def retain(record):
            record();self.events.append('retain')
            self.held=json.loads((self.worker.workspace/'SHARED-OWNERSHIP-RETAINED.json').read_text())
            raise Retained()
        io_pool=IO();deadline=time.time()+60
        def checked(*args):return io_pool,deadline
        argv=sdk_execute.child_argv('/inert/plan.json','0'*64,self.worker.workspace)
        import sdk_result_audit
        original=sdk_result_audit.audit
        def audit(*args,**kwargs):
            self.events.append('audit:cli-sdk')
            self.assertFalse(self.cpu.closed or self.io.closed)
            return original(*args,**kwargs)
        # Dynamic module import uses the same pinned audit source but a separate
        # module object; patch its loader just to observe ordering around it.
        import importlib.util
        original_exec=importlib.util.spec_from_file_location
        def spec(name,path):
            result=original_exec(name,path)
            if name=='camera_receiving_result_audit':
                original_load=result.loader.exec_module
                def load(module):
                    original_load(module);module.audit=audit
                result.loader.exec_module=load
            return result
        with ExitStack() as stack:
            stack.enter_context(patch.object(dispatch.Pool,'read',return_value=CPU()))
            stack.enter_context(patch.object(dispatch,'checked_io_request',side_effect=checked))
            stack.enter_context(patch.object(dispatch,'OwnedGroup',Owner))
            stack.enter_context(patch.object(dispatch,'settle',side_effect=settle))
            stack.enter_context(patch.object(dispatch,'retain_after_record',side_effect=retain))
            stack.enter_context(patch('shared_io_pool.read_manifest',return_value=self.worker.plan))
            stack.enter_context(patch('importlib.util.spec_from_file_location',side_effect=spec))
            code=dispatch.run('camera-sdk-receive',argv,self.worker.workspace,8,
                io_admission={'path':'/inert/no-admission','sha256':'0'*64})
            assert code!=2, self.events
            return code
    def test_sdk_audit_precedes_reap_and_reverse_close(self):
        self.prepare()
        self.assertEqual(self.run_parent(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn:fake-worker',
            'await:fake-worker','audit:cli-sdk','settle:fake-worker','close:cpu','close:io'])
    def test_missing_sdk_group_retains_without_reap_or_lease_release(self):
        result=self.prepare();result['invocations'][0]['outcome']['stdout']=''
        (self.worker.workspace/'RESULT.json').write_text(json.dumps(result))
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('audit:cli-sdk',self.events)
        self.assertNotIn('settle:fake-worker',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_settled_invalid_sdk_finding_returns_failure_after_close(self):
        self.prepare(invalid=True);self.worker_exit=7
        self.assertEqual(self.run_parent(),7)
        self.assertTrue(self.cpu.closed and self.io.closed)
        proof=json.loads((self.worker.workspace/'SHARED-SERVER-AUDIT.json').read_text())
        self.assertEqual(proof['functional_status'],'FAILED')
        self.assertEqual(proof['helper_invocations'],1)
    def test_failed_finding_with_successful_worker_exit_retains(self):
        self.prepare(invalid=True)
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('settle:fake-worker',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_live_worker_observation_retains_without_settle(self):
        self.prepare();self.live=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('audit:cli-sdk',self.events)
        self.assertNotIn('settle:fake-worker',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_borrowed_metadata_change_retains_before_worker_reap(self):
        self.prepare();self.worker.source.chmod(0o600)
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('audit:cli-sdk',self.events)
        self.assertNotIn('settle:fake-worker',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)


if __name__=='__main__':unittest.main()
