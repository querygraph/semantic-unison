import copy
import unittest
from parent import audit
from sdk_multifile.plan import plan,BUILD
from result_test import Results


class Parent(unittest.TestCase):
    def fixture(self):
        p=dict(workspace='/private/tmp/u-sdk-multi',tool=dict(path='/inert/sdk',sha256='b'*64,build_id=BUILD,threads=1),
               binaries={n:dict(label=n,path='/inert/'+n,sha256='a'*64) for n in ['stock','ox']})
        r=dict(schema='unison-sdk-multifile-worker/1',complete=True,phase='FINISHED',invocations=[],cases=[],semantic_eligibility_claimed=False,pixel_equivalence_claimed=False)
        proxies=[]
        for i,label in enumerate(['stock','ox']):
            sources,case=Results().fixture();p['sources']=sources
            argv=plan(p['binaries'][label],p['tool'],p['workspace']+'/'+label)['command']
            out=case['outcome'];out['command']=argv
            owner=dict(pid=50+i,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,other_group_members_absent_before_reap=True)
            out.update(client_cleanup=owner,supervisor_cleanup=dict(owner,pid=60+i))
            out['proxy'].update(schema='unison-loopback-protocol-count/1',server_command=[argv[0],'-server'],server_returncode=0,server_cleanup=dict(owner,pid=9),input_pump_joined=True,pump_errors=[])
            proxies.append(copy.deepcopy(out['proxy']))
            r['cases'].append(dict(label=label,case=case))
            r['invocations'].append(dict(index=i,state='OUTCOME',identity=dict(label=label,mode='semantic',workers=3,directory=p['workspace']+'/'+label,stage='seed'),command=argv,outcome=out))
        return r,p,proxies
    def test_complete_pure_composition_is_not_parent_release(self):
        r,p,proxies=self.fixture();v=audit(r,p,raw_proxy_receipts=proxies)
        self.assertEqual(v['sdk_helpers_settled'],4);self.assertEqual(v['functional_status'],'PASSED')
        self.assertFalse(v['resource_release_authorized']);self.assertFalse(v['receiving_bytes_reverified'])
    def test_proxy_command_order_and_group_mutations_refuse(self):
        for kind in ['raw','command','order','group']:
            r,p,proxies=self.fixture()
            if kind=='raw':proxies[0]['server_pid']=99
            elif kind=='command':r['invocations'][0]['command'].append('-force')
            elif kind=='order':r['invocations'].reverse()
            else:r['invocations'][0]['outcome']['client_cleanup']['reaped']=False
            with self.assertRaises(ValueError):audit(r,p,raw_proxy_receipts=proxies)
    def test_zero_call_requires_no_active_case_and_explicit_preparation(self):
        r,p,_=self.fixture();r.update(complete=False,phase='PREPARING_NO_CALL',failure='original preparation',cases=[],invocations=[])
        self.assertEqual(audit(r,p,raw_proxy_receipts=[])['attempted_cli_invocations'],0)
        r['phase']='CALL_MAY_HAVE_STARTED'
        with self.assertRaises(ValueError):audit(r,p,raw_proxy_receipts=[])
    def test_full_proxy_no_creation_is_distinct_from_null_pid(self):
        r,p,proxies=self.fixture();r.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='pre-server failure')
        r['invocations']=r['invocations'][:1];r['cases']=r['cases'][:1]
        out=r['invocations'][0]['outcome'];out.update(returncode=2,stdout='',stderr='',supervisor_output='')
        out['client_cleanup']['returncode']=2;out['supervisor_cleanup']['returncode']=70
        out['proxy'].update(server_command=None,server_pid=None,server_returncode=None,server_cleanup=None,server_resources=None,
                            launcher_control_header_bytes_excluded=None,forwarded_protocol_bytes=dict(client_to_server_bytes=0,server_to_client_bytes=0),fault='pre-creation fixture')
        case=r['cases'][0]['case'];case.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='missing helpers')
        case.pop('helper_settlements');case.pop('validation')
        raw=[copy.deepcopy(out['proxy'])]
        self.assertEqual(audit(r,p,raw_proxy_receipts=raw)['sdk_helpers_settled'],0)
        del out['proxy']['server_resources'];raw=[copy.deepcopy(out['proxy'])]
        with self.assertRaises(ValueError):audit(r,p,raw_proxy_receipts=raw)

if __name__=='__main__':unittest.main()
