"""Composed worker/auditor readback with fake native boundary and tiny originals."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import save
from mixed_peer_compatibility import worker,parent

class Readback(unittest.TestCase):
    artifacts={'stock':'/inert/stock','ox':'/inert/ox','old-stock':'/inert/old'}
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-mixed-parent-control-')
        self.root=Path(self.temp.name)
        with patch.object(worker,'retained_call',side_effect=self.fake):
            self.result=worker.execute(self.artifacts,self.root,time.monotonic()+300,lambda value:None)
    def tearDown(self):self.temp.cleanup()
    def fake(self,argv,env,directory,deadline):
        source=Path(argv[1])/'item.dng';target=source.parent.parent/'right/item.dng'
        if directory.name!='noop':target.write_bytes(source.read_bytes())
        owner=lambda pid:dict(pid=pid,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
        base=[env['UNISON_SYNC_BENCH_BINARY'],'-server','__new-rpc-mode']
        proxy=dict(schema='unison-loopback-protocol-count/1',server_cleanup=owner(103),server_pid=103,server_returncode=0,
            server_command=base+json.loads(env['UNISON_SYNC_BENCH_SERVER_FLAGS']),input_pump_joined=True,
            launcher_control_header_bytes_excluded=4+len(json.dumps(base).encode()),pump_errors=[],fault=None,
            server_group_binding=dict(native_pid=103,native_process_group=102,supervisor_pid=102,supervisor_process_group=102,observed_before_native_reap=True))
        save(directory/'proxy.json',proxy)
        return dict(command=argv,returncode=0,timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,
                    client_cleanup=owner(101),supervisor_cleanup=owner(102),proxy=proxy)
    def check(self):return parent.audit_saved(self.result,self.artifacts,self.root)
    def test_complete(self):
        out=self.check();self.assertEqual(out['functional'],'PASS');self.assertEqual(out['attempted_calls'],12)
    def test_raw_receipt_tampered(self):
        p=self.root/'0/seed/proxy.json';r=json.loads(p.read_text());r['server_pid']=999;p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.check()
    def test_final_bytes_tampered(self):
        (self.root/'3/right/item.dng').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.check()
    def test_false_completed_prefix(self):
        self.result['invocations']=self.result['invocations'][:-1]
        with self.assertRaises(ValueError):self.check()
    def test_failed_prefix_lifecycle_only(self):
        self.result['invocations']=self.result['invocations'][:1];self.result['complete']=False
        self.assertFalse(self.check()['bytes_verified'])
    def test_changed_noop_identity(self):
        self.result['cases'][0]['stages'][1]['target_identity']=dict(self.result['cases'][0]['stages'][1]['target_identity'],st_ino=999)
        with self.assertRaises(ValueError):self.check()
    def test_timeout_not_functional_success(self):
        self.result['invocations'][0]['outcome']['timed_out']=True
        with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
