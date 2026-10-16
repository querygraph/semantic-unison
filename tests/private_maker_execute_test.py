"""Disposable metadata and injected worker boundary controls; zero camera IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent/'sdk_host_matrix'))
import shared_binding
import private_maker_execute as entry
from private_maker_plan_test import fixture
from private_maker_audit import audit_worker
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership


class Execute(unittest.TestCase):
    def test_metadata_digest_duplicate_and_exclusive_save(self):
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'metadata';entry.save(path,{'a':1})
            raw=path.read_bytes();self.assertEqual(entry.document(path,hashlib.sha256(raw).hexdigest()),{'a':1})
            with self.assertRaises(ValueError):entry.document(path,'0'*64)
            with self.assertRaises(FileExistsError):entry.save(path,{})
            path.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):entry.document(path)
    def test_combined_parse_and_close_failure_retains_identity_once(self):
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'tiny';path.write_text('{not JSON}')
            observed=os.lstat(path);raw=path.read_bytes();reads=iter((raw,b''));closed=[]
            def failed(fd):closed.append(fd);raise OSError('unknown close')
            with patch.object(entry.os,'open',return_value=900),patch.object(entry.os,'fstat',return_value=observed),\
                 patch.object(entry.os,'read',side_effect=lambda *a:next(reads)),patch('os.close',side_effect=failed):
                with self.assertRaises(UnresolvedIOOwnership) as caught:entry.document(path)
            self.assertEqual(closed,[900])
            self.assertIsInstance(caught.exception.original_failure,json.JSONDecodeError)
            self.assertEqual(caught.exception.uncertain_closes[0]['fd'],900)
    def call(self,*,error=None):
        plan=fixture();args=argparse.Namespace(workspace=plan['workspace'],plan='/plan',plan_sha256='b'*64)
        result={}
        with patch.object(entry,'document',return_value={}),\
             patch.object(shared_binding,'verify',return_value={'canonical_metadata_bound':True}),\
             patch.object(entry,'read_source',side_effect=error) as read,\
             patch.object(entry,'save',side_effect=lambda path,value:result.update(value)),\
             patch.object(entry,'audit'):
            read.return_value={'injected_fixture':True}
            code=entry.worker(args,plan)
        return code,result
    def test_bound_worker_known_failure_has_zero_external_children(self):
        code,result=self.call(error=OSError('injected source open refusal'))
        self.assertEqual(code,1)
        proof=audit_worker(result,fixture()['geometry'],parent_pid=os.getppid(),worker_pid=os.getpid())
        self.assertFalse(proof['worker_complete']);self.assertFalse(proof['resource_release_authorized'])
        result['worker_pid']+=1
        with self.assertRaises(ValueError):audit_worker(result,fixture()['geometry'],parent_pid=os.getppid(),worker_pid=os.getpid())
    def test_uncertainty_cannot_become_failed_result(self):
        with self.assertRaises(UnresolvedOwnership):
            self.call(error=UnresolvedIOOwnership('injected',uncertain_closes=[{'fd':900}]))
    def test_manual_requires_exact_shared8_admission_and_plan(self):
        import manual
        plan=fixture();environment=dict(SHARED_CPU_CREDITS='8',SHARED_IO_ADMISSION='/admission',
            SHARED_IO_ADMISSION_SHA256='b'*64,MAKER_SLICE_PLAN='/plan',MAKER_SLICE_PLAN_SHA256='c'*64)
        with patch.object(entry,'checked_plan',return_value=plan):
            command=manual.command('private-maker-slice',Path(plan['workspace']),environment)
            self.assertEqual(command[2:4],['--worker','--plan'])
            for changed in ({'SHARED_CPU_CREDITS':'4'},{'SHARED_IO_ADMISSION':''}):
                with self.assertRaises(ValueError):manual.command('private-maker-slice',Path(plan['workspace']),dict(environment,**changed))
    def test_manual_constructs_command_without_opening_metadata(self):
        import manual
        plan=fixture();environment=dict(SHARED_CPU_CREDITS='8',SHARED_IO_ADMISSION='/admission',
            SHARED_IO_ADMISSION_SHA256='b'*64,MAKER_SLICE_PLAN='/plan',MAKER_SLICE_PLAN_SHA256='c'*64)
        with patch.object(entry,'checked_plan') as opened:
            manual.command('private-maker-slice',Path(plan['workspace']),environment)
            opened.assert_not_called()


if __name__=='__main__':unittest.main()
