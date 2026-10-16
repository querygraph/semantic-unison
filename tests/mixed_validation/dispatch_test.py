"""Admission metadata controls with inert pools; zero acquisition or helpers."""
import hashlib
import sys
from pathlib import Path
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation.plan_test import fixture
from mixed_validation.boundary import worker_argv
from mixed_validation.inventory import paths
from mixed_validation import execute
import shared_dispatch as dispatch
import shared_io_pool as io


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.plan=fixture();self.workspace=Path(self.plan['workspace'])
        self.argv=worker_argv(self.plan,interpreter=sys.executable,plan_path='/prepared/plan.json',plan_sha256='a'*64)
        self.request=dict(path='/prepared/admission.json',sha256='b'*64)
        sources=set(paths())|{dispatch.ROOT/'tests/manual.py',dispatch.ROOT/'tests/shared_io_pool.py',
             dispatch.ROOT/'tests/shared_cpu_pool.py',dispatch.ROOT/'tests/shared_process_owner.py',
             dispatch.ROOT/'bench/sync/ownership.py',Path(dispatch.__file__),Path(self.argv[1])}
        self.admission=dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB',target=dispatch.MIXED_TARGET,
            command=self.argv,workspace=str(self.workspace),cpu_credits=8,
            io_manifest_sha256=io.CANONICAL_SHA256,start_deadline_unix=time.time()+60,
            execution_source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    def call(self):
        with patch.object(io,'read_manifest',return_value=self.admission),\
             patch.object(execute,'checked_plan',return_value=self.plan),\
             patch.object(io.GlobalPool,'read',return_value='inert-existing-pool'):
            return dispatch.checked_io_request(self.request,dispatch.MIXED_TARGET,self.argv,self.workspace,8)
    def test_exact_existing_admission_is_consumed_as_metadata_only(self):
        self.assertEqual(self.call()[0],'inert-existing-pool')
        self.assertEqual(len(self.argv),9);self.assertEqual(self.argv[1],str(Path(execute.__file__)))
    def test_stale_sources_expiry_and_target_refuse(self):
        original=dict(self.admission)
        for key,value in [('start_deadline_unix',0),('execution_source_sha256',{}),('target','old')]:
            self.admission=dict(original);self.admission[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.call()
    def test_no_cpu_only_route_or_token_acquisition(self):
        with patch.object(dispatch.Pool,'read') as pool:
            with self.assertRaises(ValueError):dispatch.run(dispatch.MIXED_TARGET,self.argv,self.workspace,8)
            pool.assert_not_called()


if __name__=='__main__':unittest.main()
