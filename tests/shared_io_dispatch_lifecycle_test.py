"""Fake leases/owners only: no canonical IO, child process or payload dispatch."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import shared_dispatch as d
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership


class Retained(BaseException):
    pass


class Lease:
    def __init__(self, label, events, failure=None):
        self.label, self.events, self.failure = label, events, failure
        self.fds = (101,) if label == 'io' else (201, 202)
        self.closed = False
    def close_after_verified_settlement(self, **proof):
        if not all(v is True for v in proof.values()):
            raise UnresolvedOwnership('proof missing', retained_fds=self.fds)
        self.events.append('close:' + self.label)
        self.closed = True
        if self.failure:
            raise self.failure


class Lifecycle(unittest.TestCase):
    def test_bad_script_form_refuses_before_pool_read(self):
        for argv in ([sys.executable,'-m','unittest'],[sys.executable],
                     [sys.executable,'/outside/repository.py']):
            with patch.object(d.Pool,'read') as pool, self.assertRaises(ValueError):
                d.run('private-dng-local-clone',argv,Path('/never-created'),8)
            pool.assert_not_called()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unison-io-fake-dispatch-')
        self.output = Path(self.temp.name)
        self.events = []
        self.io, self.cpu = Lease('io', self.events), Lease('cpu', self.events)
        self.io_result, self.cpu_result = self.io, self.cpu
        self.io_error = self.cpu_error = self.settle_error = None
        self.check_calls = 0
        self.second_check_error = None
        self.closure = {'pid': 900001, 'returncode': 0, 'reaped': True,
                        'other_group_members_absent_before_reap': True, 'timed_out': False}
        self.passed_fds = None
        self.spawned = False
        self.held_record = None
    def tearDown(self):
        self.temp.cleanup()
    def acquire_io(self):
        self.events.append('acquire:io')
        if self.io_error: raise self.io_error
        return self.io_result
    def acquire_cpu(self, indexes):
        self.events.append('acquire:cpu')
        if self.cpu_error: raise self.cpu_error
        self.assertEqual(indexes, tuple(range(8)))
        return self.cpu_result
    def spawn(self, *args, **kw):
        self.events.append('spawn')
        self.spawned = True
        self.passed_fds = kw['pass_fds']
        self.assertFalse(self.io.closed or self.cpu.closed)
        class Owner:
            pid = 900001
            reaped = False
        return Owner()
    def settle(self, child, deadline):
        self.events.append('settle')
        self.assertFalse(self.io.closed or self.cpu.closed)
        if self.settle_error: raise self.settle_error
        child.reaped = True
        return self.closure
    def retain(self, record):
        record()
        self.held_record = json.loads((self.output/'SHARED-OWNERSHIP-RETAINED.json').read_text())
        raise Retained()
    def run_case(self, target='private-dng-local-clone'):
        class Pool:
            pass
        self.io_pool = Pool()
        self.io_pool.try_acquire = self.acquire_io
        cpu_pool = Pool()
        cpu_pool.try_acquire = self.acquire_cpu
        self.deadline = time.time()+60
        def checked(*args):
            self.check_calls += 1
            if self.check_calls == 2 and self.second_check_error:
                raise self.second_check_error
            return self.io_pool,self.deadline
        with ExitStack() as stack:
            stack.enter_context(patch.object(d.Pool,'read',return_value=cpu_pool))
            stack.enter_context(patch.object(d,'checked_io_request',side_effect=checked))
            stack.enter_context(patch.object(d,'OwnedGroup',side_effect=self.spawn))
            stack.enter_context(patch.object(d,'settle',side_effect=self.settle))
            stack.enter_context(patch.object(d,'retain_after_record',side_effect=self.retain))
            return d.run(target,[sys.executable,str(Path(__file__).resolve())],
                         self.output,8,io_admission={'path':'/never-read','sha256':'0'*64})

    def test_framing_input_parent_resource_order(self):
        self.assertEqual(self.run_case('private-dng-framing-input'),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn','settle','close:cpu','close:io'])
        self.assertEqual(set(self.passed_fds),set(self.io.fds+self.cpu.fds))

    def test_order_inheritance_and_settlement_before_reverse_close(self):
        self.assertEqual(self.run_case(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn','settle','close:cpu','close:io'])
        self.assertEqual(set(self.passed_fds),set(self.io.fds+self.cpu.fds))
        self.assertTrue(json.loads((self.output/'SHARED-CLOSED.json').read_text())['io_barrier_acquired_and_closed'])
    def test_io_contention_never_requests_cpu_or_child(self):
        self.io_result=None
        self.assertEqual(self.run_case(),2)
        self.assertEqual(self.events,['acquire:io'])
        self.assertFalse(self.spawned)
    def test_cpu_contention_releases_io_before_busy(self):
        self.cpu_result=None
        self.assertEqual(self.run_case(),2)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','close:io'])
    def test_prelaunch_refusal_rolls_back_without_child(self):
        self.second_check_error=ValueError('expired')
        self.assertEqual(self.run_case(),2)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','close:cpu','close:io'])
        self.assertFalse(self.spawned)
    def test_acquisition_uncertainty_records_all_close_identities(self):
        self.io_error=UnresolvedIOOwnership('two closes',retained_fds=(303,),
            uncertain_closes=({'fd':401,'role':'barrier'},{'fd':402,'role':'directory'}))
        with self.assertRaises(Retained): self.run_case()
        self.assertEqual(self.held_record['retained_fds'],[303])
        self.assertEqual([x['fd'] for x in self.held_record['uncertain_closes']],[401,402])
        self.assertNotIn('acquire:cpu',self.events)
    def test_settlement_unknown_does_not_close_either_lease(self):
        self.settle_error=RuntimeError('unknown group')
        with self.assertRaises(Retained): self.run_case()
        self.assertFalse(self.io.closed or self.cpu.closed)
        self.assertEqual(self.held_record['retained_io_fds'],[101])
        self.assertEqual(self.held_record['retained_cpu_fds'],[201,202])
    def test_cpu_close_unknown_retains_io(self):
        self.cpu.failure=UnresolvedOwnership('cpu close unknown',retained_fds=(201,),uncertain_fd=202)
        with self.assertRaises(Retained): self.run_case()
        self.assertFalse(self.io.closed)
        self.assertEqual(self.held_record['uncertain_fd'],202)
        self.assertEqual(self.held_record['retained_io_fds'],[101])
    def test_io_close_unknown_never_reports_closed(self):
        self.io.failure=UnresolvedOwnership('io close unknown',uncertain_fd=101)
        with self.assertRaises(Retained): self.run_case()
        self.assertEqual(self.held_record['uncertain_fd'],101)
        self.assertFalse((self.output/'SHARED-CLOSED.json').exists())
    def test_child_failure_still_settles_and_closes_both(self):
        self.closure['returncode']=7
        self.assertEqual(self.run_case(),7)
        self.assertTrue(self.io.closed and self.cpu.closed)
    def test_known_timeout_receipt_closes_both_and_returns124(self):
        self.closure.update(returncode=-9,timed_out=True)
        self.assertEqual(self.run_case(),124)
        self.assertTrue(self.io.closed and self.cpu.closed)
    def test_failed_group_proof_retains_both(self):
        self.closure['other_group_members_absent_before_reap']=False
        with self.assertRaises(Retained): self.run_case()
        self.assertFalse(self.cpu.closed or self.io.closed)

    def test_closed_receipt_write_failure_does_not_claim_live_ownership(self):
        original=d.write
        def fail_closed(path,value):
            if path.name=='SHARED-CLOSED.json':
                raise OSError('injected closed receipt write failure')
            return original(path,value)
        with patch.object(d,'write',side_effect=fail_closed):
            with self.assertRaises(OSError): self.run_case()
        self.assertTrue(self.cpu.closed and self.io.closed)
        self.assertIsNone(self.held_record)

    def test_prelaunch_closed_refusal_receipt_failure_is_not_unknown_hold(self):
        self.second_check_error=ValueError('expired')
        original=d.write
        def fail_closed(path,value):
            if path.name=='SHARED-NOT-STARTED.json':
                raise OSError('injected no-start receipt failure')
            return original(path,value)
        with patch.object(d,'write',side_effect=fail_closed):
            with self.assertRaises(OSError): self.run_case()
        self.assertFalse(self.spawned)
        self.assertTrue(self.cpu.closed and self.io.closed)
        self.assertIsNone(self.held_record)


if __name__=='__main__':
    unittest.main()
