"""Injected disposable parent lifecycle; no canonical IO or photo payload."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import shared_dispatch as d
import private_maker_execute as entry
import private_maker_audit_test as audit_fixture
from private_maker_plan_test import fixture
import shared_io_dispatch_lifecycle_test as lifecycle
Retained=lifecycle.Retained


class SliceParent(unittest.TestCase):
    setUp=lifecycle.Lifecycle.setUp
    tearDown=lifecycle.Lifecycle.tearDown
    acquire_io=lifecycle.Lifecycle.acquire_io
    acquire_cpu=lifecycle.Lifecycle.acquire_cpu
    spawn=lifecycle.Lifecycle.spawn
    settle=lifecycle.Lifecycle.settle
    retain=lifecycle.Lifecycle.retain
    # Reuse disposable lease/owner doubles, not their target-specific tests.
    def run_slice(self,*,complete=True):
        plan=fixture();plan['workspace']=str(self.output)
        diagnostic,geometry=audit_fixture.Audit().result();plan['geometry']=geometry
        source=self.output/'tiny-source';source.write_bytes(b'tiny');source.chmod(0o400)
        from private_maker_slice import stamp
        plan['source']=dict(path=str(source),identity=stamp(os.lstat(source)))
        result=dict(schema='unison-private-maker-worker/1',complete=complete,
            diagnostic=diagnostic if complete else None,failure=None if complete else 'injected refusal',
            parent_pid=os.getpid(),worker_pid=900001,canonical_metadata_bound=True,external_children_started=0)
        (self.output/'RESULT.json').write_text(json.dumps(result))
        io_pool=SimpleNamespace(try_acquire=self.acquire_io)
        cpu_pool=SimpleNamespace(try_acquire=self.acquire_cpu)
        command=[d.sys.executable,str(Path(entry.__file__).resolve()),'--worker','--plan','/inert',
                 '--plan-sha256','b'*64,'--workspace',str(self.output)]
        with ExitStack() as stack:
            stack.enter_context(patch.object(d.Pool,'read',return_value=cpu_pool))
            # Fresh-check test deadline is independent from mock admission validation.
            import time
            stack.enter_context(patch.object(d,'checked_io_request',return_value=(io_pool,time.time()+60)))
            stack.enter_context(patch.object(d,'OwnedGroup',side_effect=self.spawn))
            stack.enter_context(patch.object(d,'settle',side_effect=self.settle))
            stack.enter_context(patch.object(d,'retain_after_record',side_effect=self.retain))
            stack.enter_context(patch.object(entry,'checked_plan',return_value=plan))
            stack.enter_context(patch.object(d.os,'fstat',return_value=SimpleNamespace(st_dev=1,st_ino=2)))
            return d.run(d.SLICE_TARGET,command,self.output,8,
                         io_admission={'path':'/inert','sha256':'b'*64})
    def test_slice_success_audit_then_reap_then_release(self):
        self.assertEqual(self.run_slice(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn','await:worker','settle','close:cpu','close:io'])
        proof=json.loads((self.output/'SHARED-SERVER-AUDIT.json').read_text())
        self.assertTrue(proof['metadata_consistent']);self.assertFalse(proof['resource_release_authorized'])
    def test_slice_live_unknown_retains_without_settle(self):
        self.await_result=False
        with self.assertRaises(Retained):self.run_slice()
        self.assertNotIn('settle',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_slice_known_failed_worker_closes_after_exit(self):
        self.closure['returncode']=1
        self.assertEqual(self.run_slice(complete=False),1)
        self.assertTrue(self.cpu.closed and self.io.closed)
    def test_slice_complete_failed_exit_retains(self):
        self.closure['returncode']=1
        with self.assertRaises(Retained):self.run_slice()
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_preflight_close_uncertainty_retains_before_acquisition(self):
        from shared_io_pool import UnresolvedIOOwnership
        error=UnresolvedIOOwnership('injected metadata close',uncertain_closes=[{'fd':900}])
        command=[d.sys.executable,str(Path(entry.__file__).resolve())]
        def retained(record):record();raise Retained()
        with patch.object(d.Pool,'read') as pool,\
             patch.object(d,'checked_io_request',side_effect=error),\
             patch.object(d,'retain_after_record',side_effect=retained):
            with self.assertRaises(Retained):d.run(d.SLICE_TARGET,command,self.output,8,
                io_admission={'path':'/inert','sha256':'b'*64})
            pool.return_value.try_acquire.assert_not_called()
        record=json.loads((self.output/'SHARED-OWNERSHIP-RETAINED.json').read_text())
        self.assertEqual(record['stage'],'metadata_preflight_before_acquisition')
        self.assertEqual(record['uncertain_closes'],[{'fd':900}])


if __name__=='__main__':unittest.main()
