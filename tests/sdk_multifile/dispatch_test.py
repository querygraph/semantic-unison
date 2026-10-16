"""Inert worker/proxy models under disposable inner tokens; no SDK/IO pool."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
import shared_dispatch as d
from sdk_multifile import entry,parent
from sdk_multifile.parent_test import Parent
from sdk_multifile.plan import plan as command_plan
from dispatch_fault_test import Lease,Retained


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='usm-d-',dir='/private/tmp');self.w=Path(self.tmp.name);self.events=[]
        self.result,self.plan,proxies=Parent().fixture();self.plan['workspace']=str(self.w);self.plan['inputs']=[]
        values=[b'original first fake',b'original second fake']
        for source,value in zip(self.plan['sources'],values):
            p=self.w/('borrowed-'+source['candidate_id']);p.write_bytes(value)
            self.plan['inputs'].append(dict(path=str(p),identity={k:getattr(p.stat(),k) for k in entry.FIELDS}))
        for i,label in enumerate(['stock','ox']):
            directory=self.w/label;directory.mkdir()
            for side in ['left','right']:
                (directory/side).mkdir()
                for source,value in zip(self.plan['sources'],values):(directory/side/source['candidate_id']).write_bytes(value)
            attempt=self.result['invocations'][i];argv=command_plan(self.plan['binaries'][label],self.plan['tool'],directory)['command']
            attempt['identity']['directory']=str(directory);attempt['command']=argv;attempt['outcome']['command']=argv
            (directory/'seed-proxy.json').write_text(json.dumps(proxies[i]))
        self.cpu=Lease(8,self.events,'cpu');self.io=Lease(1,self.events,'io');self.exit=0;self.live=False
    def tearDown(self):self.cpu.dispose();self.io.dispose();self.tmp.cleanup()
    def run_parent(self):
        (self.w/'RESULT.json').write_text(json.dumps(self.result));outer=self
        class CPU:
            def try_acquire(self,indexes):outer.events.append('cpu');return outer.cpu
        class IO:
            def try_acquire(self):outer.events.append('io');return outer.io
        class Owner:
            pid=900001
            def __init__(self,*args,**kw):
                outer.events.append('spawn');assert set(kw['pass_fds'])==set(outer.cpu.fds+outer.io.fds)
            def await_terminal(self,_):return not outer.live
        def settle(*_):
            outer.events.append('settle');self.assertFalse(self.cpu.closed or self.io.closed)
            return dict(pid=900001,returncode=self.exit,reaped=True,other_group_members_absent_before_reap=True,timed_out=False)
        def retained(record):record();raise Retained()
        def read(path,digest):
            if str(path)=='/inert/plan':return self.plan
            return json.loads(Path(path).read_text())
        pool=IO();deadline=time.time()+60
        with ExitStack() as s:
            s.enter_context(patch.object(d.Pool,'read',return_value=CPU()))
            s.enter_context(patch.object(d,'checked_io_request',return_value=(pool,deadline)))
            s.enter_context(patch.object(d,'OwnedGroup',Owner));s.enter_context(patch.object(d,'settle',side_effect=settle))
            s.enter_context(patch.object(d,'retain_after_record',side_effect=retained))
            s.enter_context(patch('shared_io_pool.read_manifest',side_effect=read))
            return d.run(entry.TARGET,entry.child_argv('/inert/plan','a'*64,self.w),self.w,8,io_admission=dict(path='/inert',sha256='0'*64))
    def test_success_rehashes_outputs_before_group_and_token_close(self):
        self.assertEqual(self.run_parent(),0)
        proof=json.loads((self.w/'SHARED-SERVER-AUDIT.json').read_text());self.assertTrue(proof['receiving_bytes_reverified'])
        self.assertEqual(self.events,['io','cpu','spawn','settle','close:cpu','close:io'])
    def test_corrupt_output_or_raw_proxy_retains_before_reap(self):
        (self.w/'stock'/'right'/'jpeg.dng').write_bytes(b'wrong')
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('settle',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_live_worker_and_failed_exit_do_not_release(self):
        self.exit=1
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('settle',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_no_cpu_only_route(self):
        with patch.object(d.Pool,'read') as pool:
            with self.assertRaises(ValueError):d.run(entry.TARGET,[sys.executable,str(Path(entry.__file__).resolve())],self.w,8)
            pool.assert_not_called()

if __name__=='__main__':unittest.main()
