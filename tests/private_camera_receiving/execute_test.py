"""Pure plan and pre-payload entry refusals; no camera/native/lock acquisition."""
import copy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import execute


class Controls(unittest.TestCase):
    def plan(self):
        return {'schema':'unison-camera-receiving-plan/1','parameters':dict(execute.PARAMETERS),
                'execution_source_sha256':{},'workspace':'/private/tmp/u-cr-fixed-case',
                'source':{'path':str(execute.SOURCE),
                    'historical_sha256':'1a4f578ee6f23730afec8495c90b37f5272042331f3375d332a9065ce5bb3ee2',
                    'identity':dict(st_size=193851848,st_dev=1,st_ino=2,st_mtime_ns=3,st_ctime_ns=4,
                                   st_mode=0o100400,st_nlink=1,st_uid=os.getuid())},
                'binaries':{label:{'label':label,'path':'/inert/'+label,'sha256':'0'*64}
                            for label in ('stock','ox')}}
    def check(self,value):
        with patch.object(execute,'read_manifest',return_value=value),patch.object(execute,'sources',return_value={}):
            return execute.checked_plan('/private/tmp/unused-plan.json','0'*64)
    def test_exact_scope_accepts_metadata_only(self):
        self.assertEqual(self.check(self.plan())['parameters']['calls'],6)
    def test_scope_and_ancestry_mutations_refused(self):
        mutations=[lambda p:p['parameters'].update(calls=7),
                   lambda p:p['parameters'].update(io_budget_enforced=0),
                   lambda p:p.update(execution_source_sha256={'wrong':'pin'}),
                   lambda p:p['source'].update(path='/Photo/original.DNG'),
                   lambda p:p['source']['identity'].update(st_mode=0o100600),
                   lambda p:p['source']['identity'].update(st_nlink=True),
                   lambda p:p.update(workspace='/Users/not-private'),
                   lambda p:p['binaries'].pop('ox')]
        for mutate in mutations:
            value=self.plan();mutate(value)
            with self.assertRaises(ValueError):self.check(value)
    def test_no_cpu_only_camera_route(self):
        import shared_dispatch
        with patch.object(shared_dispatch.Pool,'read') as pool,self.assertRaises(ValueError):
            shared_dispatch.run('camera-receive',execute.child_argv('/plan','0'*64,'/workspace'),
                                Path('/uncreated'),8)
        pool.assert_not_called()
    def test_worker_parent_binding_refusal_before_payload(self):
        with tempfile.TemporaryDirectory() as name:
            plan=self.plan();plan['workspace']=name
            args=SimpleNamespace(workspace=name,plan='/plan',plan_sha256='0'*64)
            with patch.object(execute,'stable_sha',return_value='0'*64), \
                 patch.object(execute,'read_manifest',return_value={'owner_pid':-1}), \
                 patch.object(execute.worker,'execute') as payload:
                with self.assertRaises(ValueError):execute.worker_entry(args,plan)
            payload.assert_not_called()


if __name__=='__main__':unittest.main()
