"""New target metadata guards only; canonical acquisition and launch are mocked."""
import os,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
import execute as entry
import shared_dispatch as d
import shared_io_pool as io
class Dispatch(unittest.TestCase):
    def args(self):
        w=Path('/private/tmp/u-crs-inert-test')
        return w,entry.child_argv('/private/tmp/inert-plan.json','a'*64,w)
    def test_no_cpu_only_route_or_partial_credit_grant(self):
        w,argv=self.args()
        with patch.object(d.Pool,'read',side_effect=AssertionError('must not acquire/read pool')):
            with self.assertRaises(ValueError):d.run(entry.TARGET,argv,w,8)
            with self.assertRaises(ValueError):d.run(entry.TARGET,argv,w,4,io_admission={'inert':'not read'})
    def test_exact_target_source_closure(self):
        w,argv=self.args();pins=entry.sources()
        value=dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB',target=entry.TARGET,command=argv,
            workspace=str(w),cpu_credits=8,io_manifest_sha256=io.CANONICAL_SHA256,
            start_deadline_unix=time.time()+300,execution_source_sha256=pins)
        def manifest(path,digest):return value if str(path)=='/private/tmp/inert-admission.json' else {'workspace':str(w)}
        with patch.object(io,'read_manifest',side_effect=manifest),patch.object(io.GlobalPool,'read',return_value='unacquired-inert-pool'):
            pool,deadline=d.checked_io_request(dict(path='/private/tmp/inert-admission.json',sha256='b'*64),entry.TARGET,argv,w,8)
        self.assertEqual(pool,'unacquired-inert-pool');self.assertEqual(deadline,value['start_deadline_unix'])
    def test_wrong_worker_shape_refuses_before_pool(self):
        w,argv=self.args();value=dict(state='ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB',target=entry.TARGET,
            command=argv[:-1],workspace=str(w),cpu_credits=8,io_manifest_sha256=io.CANONICAL_SHA256,
            start_deadline_unix=time.time()+300)
        with patch.object(io,'read_manifest',return_value=value),patch.object(io.GlobalPool,'read',side_effect=AssertionError('pool not reached')):
            with self.assertRaises(ValueError):d.checked_io_request(dict(path='/private/tmp/inert.json',sha256='a'*64),entry.TARGET,argv[:-1],w,8)
if __name__=='__main__':unittest.main()
