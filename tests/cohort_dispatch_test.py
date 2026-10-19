"""Original inert-owner/temporary-descriptor composition, no pool or CLI calls."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import cohort_entry as E
import shared_dispatch as D
from shared_cpu_pool import UnresolvedOwnership


class Retained(BaseException):
    pass


class Dispatcher(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='cohort-dispatch-controls-')
        self.output=Path(self.temporary.name).resolve();self.events=[]
        self.complete=True;self.worker_exit=0;self.live=False;self.unknown=False;self.close_error=False
        self.descriptors=[];outer=self
        class Lease:
            def __init__(self,label,count):
                self.label=label;self.closed=False
                self.fds=tuple(os.open(outer.output/(label+str(i)),os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600) for i in range(count))
                outer.descriptors.extend(self.fds)
            def close_after_verified_settlement(self,**proof):
                outer.assertTrue(all(value is True for value in proof.values()))
                outer.events.append('close:'+self.label)
                if self.label=='cpu' and outer.close_error:
                    raise UnresolvedOwnership('injected BEFORE OS close')
                for fd in self.fds:os.close(fd);outer.descriptors.remove(fd)
                self.closed=True
        self.cpu=Lease('cpu',8);self.io=Lease('io',1)
    def tearDown(self):
        # Only inert known-open test descriptors; injected error precedes OS close.
        for fd in self.descriptors:os.close(fd)
        self.temporary.cleanup()
    def run_parent(self):
        outer=self
        class Pool:
            def try_acquire(self,indexes):
                outer.assertEqual(indexes,tuple(range(8)));outer.events.append('acquire:cpu');return outer.cpu
        class IO:
            def try_acquire(self):outer.events.append('acquire:io');return outer.io
        class Owner:
            pid=900001
            def __init__(self,*args,**kw):
                outer.assertEqual(kw['pass_fds'],outer.cpu.fds+outer.io.fds)
                outer.events.append('spawn:inert')
            def await_terminal(self,seconds):
                outer.assertEqual(seconds,898);outer.events.append('await:inert');return not outer.live
        def audit(*args,**kw):
            outer.events.append('audit')
            outer.assertFalse(outer.cpu.closed or outer.io.closed)
            if outer.unknown:raise ValueError('unknown attempted group')
            return dict(functional_status='PASSED' if outer.complete else 'FAILED_PREFIX')
        def settle(child,deadline):
            outer.events.append('settle:inert');outer.assertFalse(outer.cpu.closed or outer.io.closed)
            return dict(pid=child.pid,returncode=outer.worker_exit,reaped=True,
                        other_group_members_absent_before_reap=True,timed_out=False)
        def retain(record):record();outer.events.append('retain');raise Retained()
        (self.output/'RESULT.json').write_text(json.dumps(dict(complete=self.complete)))
        io=IO();deadline=time.time()+60
        with ExitStack() as stack:
            stack.enter_context(patch.object(D.Pool,'read',return_value=Pool()))
            stack.enter_context(patch.object(D,'checked_io_request',return_value=(io,deadline)))
            stack.enter_context(patch.object(D,'OwnedGroup',Owner))
            stack.enter_context(patch.object(D,'settle',side_effect=settle))
            stack.enter_context(patch.object(D,'retain_after_record',side_effect=retain))
            stack.enter_context(patch.object(E,'parent_audit',side_effect=audit))
            return D.run(E.TARGET,[sys.executable,str(E.ROOT/'tests/cohort_entry.py'),'--worker',
                         '--plan','/inert','--plan-sha256','a'*64,'--workspace',str(self.output)],
                         self.output,8,io_admission=dict(path='/inert',sha256='b'*64))
    def test_success_orders_audit_reap_and_close(self):
        self.assertEqual(self.run_parent(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn:inert','await:inert',
                                     'audit','settle:inert','close:cpu','close:io'])
    def test_known_failed_prefix_closes_without_pass(self):
        self.complete=False;self.worker_exit=1
        self.assertEqual(self.run_parent(),1)
        self.assertEqual(json.loads((self.output/'SHARED-SERVER-AUDIT.json').read_text())['functional_status'],'FAILED_PREFIX')
    def test_unknown_group_retains_before_reap(self):
        self.unknown=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_live_worker_not_killed_or_reaped(self):
        self.live=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('audit',self.events);self.assertNotIn('settle:inert',self.events)
    def test_contradictory_worker_exit_retains(self):
        self.worker_exit=1
        with self.assertRaises(Retained):self.run_parent()
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_close_uncertainty_retains_io_without_retry(self):
        self.close_error=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertEqual(self.events.count('close:cpu'),1);self.assertNotIn('close:io',self.events)


if __name__=='__main__':unittest.main()
