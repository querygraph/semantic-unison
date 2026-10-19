"""Directed owner-boundary controls with inert fixtures; no canonical IO/transport."""
import argparse
import stat
from types import SimpleNamespace
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import cohort_entry as E
import shared_dispatch as D
from cohort_plan_test import fixture
from shared_cpu_pool import UnresolvedOwnership


class Entry(unittest.TestCase):
    def plan(self,workspace):
        p=fixture(1);p['workspace']=str(workspace);p['interpreter']=sys.executable
        return p

    def test_shared_route_refuses_borrow_and_missing_admission(self):
        for selector in (4,8,'auto'):
            with self.subTest(selector=selector),self.assertRaises(ValueError):E.require_shared8(fixture(selector))
        for selector in (1,2):E.require_shared8(fixture(selector))
        with patch.object(D.Pool,'read',side_effect=AssertionError('pool accessed')):
            with self.assertRaises(ValueError):
                D.run(E.TARGET,[sys.executable,str(E.ROOT/'tests/cohort_entry.py')],Path('/fake'),8)

    def test_worker_exact_argv(self):
        p=fixture(1)
        self.assertEqual(E.worker_argv(p,'/plan','a'*64),
            [p['interpreter'],str(E.ROOT/'tests/cohort_entry.py'),'--worker','--plan','/plan',
             '--plan-sha256','a'*64,'--workspace',p['workspace']])

    def test_inherited_binding_requires_exact_nine_and_actual_target(self):
        from sdk_host_matrix import shared_binding as B
        identities=tuple((1,100+i) for i in range(9))
        command=['/inert','--worker']
        start=dict(owner_pid=11,child_pid=22,target=E.TARGET,command=command,
            cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',
            inherited_resource_fds=[dict(fd=30+i,device=dev,inode=ino)
                for i,(dev,ino) in enumerate(identities)])
        def observe(fd):
            dev,ino=identities[fd-30]
            return SimpleNamespace(st_dev=dev,st_ino=ino,st_mode=stat.S_IFREG|0o600,
                                   st_uid=os.getuid(),st_nlink=1,st_size=0)
        with patch.object(B,'inventory',return_value=identities):
            proof=B.verify(start,command,parent_pid=11,worker_pid=22,observe=observe,target=E.TARGET)
            self.assertFalse(proof['resource_release_authorized'])
            for key,value in (('target','old'),('cpu_credits',18),('token_indexes',list(range(8,16))),
                              ('command',['different']),('owner_pid',12)):
                broken=copy.deepcopy(start);broken[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):
                    B.verify(broken,command,parent_pid=11,worker_pid=22,observe=observe,target=E.TARGET)

    def run_failed_worker(self,error,entered):
        with tempfile.TemporaryDirectory(prefix='cohort-entry-controls-') as temporary:
            workspace=Path(temporary).resolve();p=self.plan(workspace)
            (workspace/'SHARED-START.json').write_text('{}')
            args=argparse.Namespace(workspace=str(workspace),plan='/plan',plan_sha256='a'*64)
            with patch.object(E,'binding',return_value={'inherited_resource_fds':[]}), \
                 patch.object(E,'document',return_value={}), \
                 patch.object(E.C,'verify_build',side_effect=None if entered else error), \
                 patch.object(E.C,'verify_artifacts',return_value={}), \
                 patch.object(E.runpy,'run_path',side_effect=error), \
                 patch.dict(os.environ,os.environ.copy(),clear=True), \
                 patch.object(sys,'argv',sys.argv.copy()):
                with self.assertRaises(type(error)) as caught:E.worker(args,p)
                self.assertIs(caught.exception,error)
            if isinstance(error,UnresolvedOwnership):
                self.assertFalse((workspace/'COHORT-FAILURE.json').exists())
                self.assertFalse((workspace/'RESULT.json').exists())
            elif entered:
                self.assertFalse((workspace/'RESULT.json').exists())
                self.assertTrue(json.loads((workspace/'COHORT-FAILURE.json').read_text())['benchmark_entered'])
            else:
                result=json.loads((workspace/'RESULT.json').read_text())
                proof=E.audit_result(result,p)
                self.assertEqual(proof['attempted_cli_invocations'],0)
                self.assertEqual(proof['functional_status'],'PRE_BENCHMARK_FAILED')

    def test_known_metadata_failure_has_zero_external_calls(self):
        self.run_failed_worker(ValueError('generated stale artifact refusal'),False)

    def test_unknown_after_entry_never_fabricates_empty_prefix(self):
        self.run_failed_worker(RuntimeError('generated benchmark entry failure'),True)

    def test_uncertainty_bypasses_known_failure_reporting(self):
        self.run_failed_worker(UnresolvedOwnership('original injected carrier',retained_fds=(999,)),False)

    def test_empty_or_unknown_runtime_prefix_refuses(self):
        p=fixture(1)
        for value in ({'complete':False,'failure':'error','invocations':[]},
                      {'complete':False,'failure':'error','temporary_directory':'/Users/photo',
                       'invocations':[]}):
            with self.assertRaises(ValueError):E.audit_result(value,p)


if __name__=='__main__':unittest.main()
