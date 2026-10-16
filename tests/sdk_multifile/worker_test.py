import copy
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import worker as w
from combined_test import frame
from plan import BUILD
from invocation import SCRIPT_NAMES


class Worker(unittest.TestCase):
    def test_complete_two_case_journal_and_independent_proxy_audit(self):
        with tempfile.TemporaryDirectory(prefix='usm-') as tmp:
            root=Path(tmp);data={};raw={};saved=[];calls=[]
            for name,value in [('uncompressed.dng',b'first original tiny'),('jpeg.dng',b'second original tiny')]:data[name]=value
            sources=[dict(candidate_id=n,sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for n,v in data.items()]
            p=dict(workspace=str(root),sources=sources,tool=dict(path='/inert/sdk',sha256='a'*64,threads=1,build_id=BUILD),
                   binaries={n:dict(label=n,path='/inert/'+n,sha256='a'*64) for n in ['stock','ox']},transport_source_sha256={n:'a'*64 for n in SCRIPT_NAMES})
            def prepare(d,label):
                for name,value in data.items():(d/'left'/name).write_bytes(value)
                return dict(original_test_preparation=True,not_native_clone_proof=True)
            class Invoke:
                def __init__(self,directory,*,binary,tool,journal,**kw):self.d=Path(directory);self.binary=binary;self.journal=journal
                def __call__(self):
                    from plan import plan
                    argv=plan(self.binary,p['tool'],self.d)['command'];i=len(calls)
                    self.journal.begin(dict(label=self.binary['label'],mode='semantic',workers=3,directory=str(self.d),stage='seed'),argv)
                    owner=dict(pid=50+i,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
                    outcome=dict(command=argv,returncode=0,timed_out=False,capture_truncated=False,supervisor_capture_truncated=False,
                                 client_cleanup=owner,supervisor_cleanup=dict(owner,pid=60+i),stderr='',supervisor_output='')
                    outcome['stdout']=''.join(frame(21+j,s['sha256'],s['bytes'],1+j,3+j) for j,s in enumerate(sources))
                    outcome['proxy']=dict(schema='unison-loopback-protocol-count/1',server_pid=9,server_returncode=0,server_command=[argv[0],'-server'],server_cleanup=dict(owner,pid=9),input_pump_joined=True,pump_errors=[])
                    for name,value in data.items():(self.d/'right'/name).write_bytes(value)
                    raw[str(self.d/'seed-proxy.json')]=copy.deepcopy(outcome['proxy']);calls.append(outcome)
                    self.journal.finish(outcome);return outcome
            with patch.object(w,'prepare_scripts',return_value=p['transport_source_sha256']),patch.object(w,'Invoker',Invoke):
                result=w.execute(p,root,time.monotonic()+300,prepare_sources=prepare,read_proxy=lambda path:raw[str(path)],persist=saved.append)
            self.assertTrue(result['complete']);self.assertEqual(len(calls),2)
            self.assertEqual(result['parent_audit']['sdk_helpers_settled'],4)
            self.assertTrue(any(v['invocations'] and v['invocations'][-1]['state']=='INTENT' for v in saved))
            self.assertFalse(result['parent_audit']['resource_release_authorized'])
    def test_preparation_failure_and_uncertainty_do_not_start_transport(self):
        for uncertain in [False,True]:
            with tempfile.TemporaryDirectory(prefix='usm-') as tmp:
                root=Path(tmp);saved=[]
                p=dict(workspace=str(root),transport_source_sha256={})
                error=w.UnresolvedOwnership('original preparation ownership') if uncertain else ValueError('original preparation refusal')
                def prepare(*_):raise error
                with patch.object(w,'prepare_scripts',return_value={}),patch.object(w,'Invoker') as transport:
                    with self.assertRaises(type(error)) as caught:
                        w.execute(p,root,time.monotonic()+10,prepare_sources=prepare,read_proxy=lambda _:None,persist=saved.append)
                    transport.assert_not_called()
                self.assertIs(caught.exception,error)
                self.assertEqual(saved[-1]['invocations'],[])
                if uncertain:self.assertNotIn('failure',saved[-1])
                else:
                    self.assertEqual(saved[-1]['phase'],'PREPARING_NO_CALL')
                    self.assertIn('original preparation refusal',saved[-1]['failure'])

if __name__=='__main__':unittest.main()
