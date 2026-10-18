"""Composed dispatcher control flow with inert owner and disposable FDs."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import shared_dispatch as D
from cached_benchmark import entry
from private_camera_receiving.close import close_descriptors


class Retained(BaseException):pass


class Lease:
    def __init__(self,count,events,label):
        self.fds=tuple(os.open('/dev/null',os.O_RDONLY|os.O_CLOEXEC) for _ in range(count))
        self.events=events;self.label=label;self.closed=False;self.error=None
    def close_after_verified_settlement(self,**proof):
        assert all(v is True for v in proof.values()) and not self.closed
        self.events.append('close:'+self.label)
        if self.error:raise self.error
        close_descriptors(self.fds);self.closed=True
    def dispose(self):
        # Injected errors occur before any OS close. Fixture disposal is not
        # a retry of an uncertain close or a live canonical token operation.
        if not self.closed:close_descriptors(self.fds);self.closed=True


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cached-dispatch-control-',dir='/private/tmp')
        self.w=Path(self.tmp.name);self.w.chmod(0o700);self.events=[]
        self.cpu=Lease(8,self.events,'cpu');self.io=Lease(1,self.events,'io')
        self.live=False;self.exit=0;self.audit_error=None;self.contended=False
        self.result=dict(complete=True)
    def tearDown(self):
        self.cpu.dispose();self.io.dispose();self.tmp.cleanup()
    def run_parent(self):
        (self.w/'RESULT.json').write_text(json.dumps(self.result));outer=self
        class CPU:
            def try_acquire(self,indexes):
                outer.events.append('acquire:cpu');assert tuple(indexes)==tuple(range(8))
                return None if outer.contended else outer.cpu
        class IO:
            def try_acquire(self):outer.events.append('acquire:io');return outer.io
        class Owner:
            pid=900001
            def __init__(self,*args,**kw):
                outer.events.append('spawn:inert')
                assert kw['pass_fds']==outer.cpu.fds+outer.io.fds
            def await_terminal(self,seconds):outer.events.append('await:inert');return not outer.live
        def settle(child,deadline):
            self.events.append('settle:inert');assert not self.cpu.closed and not self.io.closed
            return dict(pid=child.pid,returncode=self.exit,reaped=True,
                        other_group_members_absent_before_reap=True,timed_out=False)
        def retain(record):record();self.events.append('retain');raise Retained()
        def audit(*args,**kw):
            self.events.append('audit');assert not self.cpu.closed and not self.io.closed
            if self.audit_error:raise self.audit_error
            return dict(functional_status='PASSED' if self.result['complete'] else 'FAILED_PREFIX')
        io=IO();deadline=time.time()+60
        with ExitStack() as stack:
            stack.enter_context(patch.object(D.Pool,'read',return_value=CPU()))
            stack.enter_context(patch.object(D,'checked_io_request',return_value=(io,deadline)))
            stack.enter_context(patch.object(D,'OwnedGroup',Owner))
            stack.enter_context(patch.object(D,'settle',side_effect=settle))
            stack.enter_context(patch.object(D,'retain_after_record',side_effect=retain))
            stack.enter_context(patch.object(entry,'parent_audit',side_effect=audit))
            return D.run(D.CACHED_TARGET,[sys.executable,str(Path(entry.__file__).resolve()),
                '--worker','--plan','/inert/plan','--plan-sha256','a'*64,'--workspace',str(self.w)],
                self.w,8,io_admission=dict(path='/inert/admission',sha256='b'*64))
    def test_success_holds_until_audit_and_wait_then_reverse_close(self):
        self.assertEqual(self.run_parent(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn:inert','await:inert',
                                     'audit','settle:inert','close:cpu','close:io'])
    def test_failed_prefix_closes_without_passing(self):
        self.result['complete']=False;self.exit=1
        self.assertEqual(self.run_parent(),1)
        self.assertEqual(json.loads((self.w/'SHARED-SERVER-AUDIT.json').read_text())['functional_status'],
                         'FAILED_PREFIX')
    def test_live_timeout_retains_before_audit_or_reap(self):
        self.live=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('audit',self.events);self.assertNotIn('settle:inert',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_bad_audit_retains(self):
        self.audit_error=ValueError('raw sample mismatch')
        with self.assertRaises(Retained):self.run_parent()
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_complete_with_failed_worker_exit_retains(self):
        self.exit=1
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_cpu_contention_rolls_back_io_before_return(self):
        self.contended=True;self.assertEqual(self.run_parent(),2)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','close:io'])
        self.assertTrue(self.io.closed);self.assertFalse(self.cpu.closed)
    def test_io_close_error_retains_after_known_cpu_close(self):
        self.io.error=OSError('inert close failure before OS close')
        with self.assertRaises(Retained):self.run_parent()
        self.assertTrue(self.cpu.closed);self.assertFalse(self.io.closed)


if __name__=='__main__':unittest.main()
