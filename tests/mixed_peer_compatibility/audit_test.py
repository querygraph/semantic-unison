"""Independent fake lifecycle frames; no process or payload activity."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from mixed_peer_compatibility.audit import audit
from mixed_peer_compatibility.contract import CASES,STAGES,command

class Prefix(unittest.TestCase):
    artifacts={'stock':'/inert/stock','ox':'/inert/ox','old-stock':'/inert/old'}
    def setUp(self):
        self.result={'invocations':[]};self.raw=[]
        for index in range(12):
            case,phase=divmod(index,3);current,orientation=CASES[case]
            argv,flags=command(self.artifacts,'/private/tmp/inert',case,STAGES[phase])
            owner=lambda pid:dict(pid=pid,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
            server=self.artifacts[current if orientation=='old-client' else 'old-stock']
            base=[server,'-server']+(['__new-rpc-mode'] if index%2 else [])
            proxy=dict(schema='unison-loopback-protocol-count/1',server_cleanup=owner(103),server_pid=103,server_returncode=0,
                server_command=base+flags,input_pump_joined=True,launcher_control_header_bytes_excluded=4+len(json.dumps(base).encode()),
                server_group_binding=dict(native_pid=103,native_process_group=102,supervisor_pid=102,supervisor_process_group=102,observed_before_native_reap=True))
            run=dict(command=argv,returncode=0,capture_truncated=False,supervisor_capture_truncated=False,
                     client_cleanup=owner(101),supervisor_cleanup=owner(102),proxy=proxy)
            self.raw.append(copy.deepcopy(proxy))
            self.result['invocations'].append(dict(index=index,state='OUTCOME',command=argv,
                identity=dict(case=case,label=current,orientation=orientation,stage=STAGES[phase]),outcome=run))
    def check(self):return audit(self.result,self.artifacts,'/private/tmp/inert',self.raw)
    def test_full(self):self.assertEqual(self.check()['attempted_calls'],12)
    def test_closed_failed_prefix(self):
        self.result['invocations']=self.result['invocations'][:1];self.raw=self.raw[:1]
        run=self.result['invocations'][0]['outcome'];run['returncode']=7;run['client_cleanup']['returncode']=7
        self.assertFalse(self.check()['functional_success_inferred'])
    def test_pending(self):
        self.result['invocations'][-1]['state']='INTENT'
        with self.assertRaises(ValueError):self.check()
    def test_raw_substitution(self):
        self.raw[-1]['server_pid']=999
        with self.assertRaises(ValueError):self.check()
    def test_client_not_reaped(self):
        self.result['invocations'][0]['outcome']['client_cleanup']['reaped']=False
        with self.assertRaises(ValueError):self.check()
    def test_pump_missing(self):
        self.raw[0]['input_pump_joined']=False;self.result['invocations'][0]['outcome']['proxy']=copy.deepcopy(self.raw[0])
        with self.assertRaises(ValueError):self.check()
    def test_wrong_server_flags(self):
        self.raw[0]['server_command']+=['-semanticworkers','18'];self.result['invocations'][0]['outcome']['proxy']=copy.deepcopy(self.raw[0])
        with self.assertRaises(ValueError):self.check()
    def test_wrong_group(self):
        self.raw[0]['server_group_binding']['native_process_group']=999;self.result['invocations'][0]['outcome']['proxy']=copy.deepcopy(self.raw[0])
        with self.assertRaises(ValueError):self.check()
    def no_server(self):
        self.result['invocations']=self.result['invocations'][:1]
        run=self.result['invocations'][0]['outcome']
        run['returncode']=1;run['client_cleanup']['returncode']=1
        run['supervisor_cleanup']['returncode']=70
        run['proxy']={'schema':'unison-loopback-protocol-count/1',
            **{key:None for key in ('server_command','server_pid','server_returncode','server_cleanup','server_resources','launcher_control_header_bytes_excluded')},
            'forwarded_protocol_bytes':{'client_to_server_bytes':0,'server_to_client_bytes':0},
            'input_pump_joined':True,'pump_errors':[],'fault':'refused before accept'}
        self.raw=[copy.deepcopy(run['proxy'])]
    def test_exact_no_creation(self):
        self.no_server()
        self.assertFalse(self.check()['rows'][0]['server_created'])
    def test_null_pid_not_no_creation(self):
        self.no_server();self.raw[0]['server_command']=['/inert/old','-server']
        self.result['invocations'][0]['outcome']['proxy']=copy.deepcopy(self.raw[0])
        with self.assertRaises(ValueError):self.check()
    def test_empty(self):
        self.result['invocations']=[];self.raw=[]
        with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
