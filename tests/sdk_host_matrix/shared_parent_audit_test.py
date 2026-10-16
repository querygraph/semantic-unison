"""Inert complete/failed-prefix direct call journals only; no SDK."""
import copy,unittest
from shared_result_test import Results
from shared_parent_audit import audit
class Parent(unittest.TestCase):
    def fixture(self):
        args,rows=Results().frames();entries=[]
        for i,row in enumerate(rows):
            out=row['outcome'];out['command']=row['command'];out['client_cleanup'].update(other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True)
            codec=['uncompressed','jpeg','jxl'][i//4];backend='reference' if i%4==0 else 'experimental'
            entries.append(dict(index=i,identity=dict(index=i+1,codec=codec,backend=backend),command=row['command'],state='OUTCOME',outcome=out))
        return args,dict(schema='unison-shared-sdk-kernel/1',complete=True,rows=rows,phase='FINISHED',resource_release_authorized=False,invocations=entries)
    def call(self,args,d):return audit(d,reference=args[0],experimental=args[1],fixtures=args[2],memory_bytes=args[3])
    def test_complete_does_not_establish_aggregate_release(self):
        args,d=self.fixture();p=self.call(args,d);self.assertEqual(p['functional_status'],'PASSED');self.assertFalse(p['resource_release_authorized'])
    def test_known_nonzero_prefix_is_failed_not_pass(self):
        args,d=self.fixture();d.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='original',rows=[],invocations=d['invocations'][:1]);d['invocations'][0]['outcome']['returncode']=7;d['invocations'][0]['outcome']['client_cleanup']['returncode']=7
        self.assertEqual(self.call(args,d)['functional_status'],'FAILED')
    def test_unknown_or_unbound_prefix_refuses_release(self):
        args,base=self.fixture()
        for mode in ['intent','group','pid','command','row','index']:
            d=copy.deepcopy(base)
            if mode=='intent':d['invocations'][0]['state']='INTENT'
            elif mode=='group':d['invocations'][0]['outcome']['client_cleanup']['other_group_members_absent_before_reap']=False
            elif mode=='pid':d['invocations'][1]['outcome']['client_cleanup']['pid']=101
            elif mode=='command':d['invocations'][0]['outcome']['command']=['wrong']
            elif mode=='row':d['rows'][0]['index']=99
            else:d['invocations'][0]['index']=True
            with self.assertRaises(ValueError):self.call(args,d)
    def test_empty_only_explicit_preparing_failure(self):
        args,d=self.fixture();d.update(complete=False,phase='PREPARING_NO_CALL',failure='precall',rows=[],invocations=[])
        self.assertEqual(self.call(args,d)['attempted_direct_calls'],0)
        d['phase']='CALL_MAY_HAVE_STARTED'
        with self.assertRaises(ValueError):self.call(args,d)
if __name__=='__main__':unittest.main()
