"""New SDK target parent tests; inert owners/protocol frames/disposable FDs."""
from contextlib import ExitStack
import copy,json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import shared_execute as entry
import shared_parent_audit as parent_audit
from shared_parent_audit_test import Parent
import shared_dispatch as d
sys.path.insert(0,str(entry.ROOT/'tests/camera_sdk_concurrency'))
from dispatch_fault_test import Lease,Retained
from shared_cpu_pool import UnresolvedOwnership
class Faults(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='u-shm-fault-',dir='/private/tmp');self.w=Path(self.tmp.name);self.w.chmod(0o700)
        self.args,self.result=Parent().fixture();self.events=[]
        for i,f in enumerate(self.args[2]):
            p=self.w/('fixture'+str(i));p.write_bytes(b'x'*f['size']);f['path']=str(p)
            st=p.stat();f['identity']={k:getattr(st,k) for k in entry.FIELDS}
        from shared_plan import shared_matrix
        cases=shared_matrix(*self.args)['cases']
        for row,attempt,case in zip(self.result['rows'],self.result['invocations'],cases):
            row['command']=case['command'];attempt['command']=case['command'];attempt['outcome']['command']=case['command']
        self.plan=dict(tools=dict(reference=self.args[0],experimental=self.args[1]),fixtures=self.args[2],host_memory_bytes=self.args[3])
        self.cpu=Lease(8,self.events,'cpu');self.io=Lease(1,self.events,'io');self.live=False;self.exit=0
    def tearDown(self):self.cpu.dispose();self.io.dispose();self.tmp.cleanup()
    def fail(self):
        self.result.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='original',rows=[],invocations=self.result['invocations'][:1])
        self.result['invocations'][0]['outcome']['returncode']=7;self.result['invocations'][0]['outcome']['client_cleanup']['returncode']=7
    def run_parent(self):
        (self.w/'RESULT.json').write_text(json.dumps(self.result));outer=self
        class CPU:
            def try_acquire(self,indexes):outer.events.append('acquire:cpu');return outer.cpu
        class IO:
            def try_acquire(self):outer.events.append('acquire:io');return outer.io
        class Owner:
            pid=900001
            def __init__(self,*args,**kw):
                outer.events.append('spawn:inert');assert set(kw['pass_fds'])==set(outer.cpu.fds+outer.io.fds)
            def await_terminal(self,seconds):outer.events.append('await:inert');return not outer.live
        def settle(child,deadline):
            self.events.append('settle:inert');self.assertFalse(self.cpu.closed or self.io.closed)
            return dict(pid=child.pid,returncode=self.exit,reaped=True,other_group_members_absent_before_reap=True,timed_out=False)
        def retain(record):record();self.events.append('retain');raise Retained()
        original=parent_audit.audit
        def audit(*args,**kw):self.events.append('audit');self.assertFalse(self.cpu.closed or self.io.closed);return original(*args,**kw)
        pool=IO();deadline=time.time()+60
        with ExitStack() as stack:
            for target,name,value in [(d.Pool,'read',CPU()),(d,'checked_io_request',lambda *a:(pool,deadline)),(d,'OwnedGroup',Owner),(d,'settle',settle),(d,'retain_after_record',retain),(parent_audit,'audit',audit)]:
                stack.enter_context(patch.object(target,name,side_effect=value) if callable(value) else patch.object(target,name,return_value=value))
            stack.enter_context(patch('shared_io_pool.read_manifest',return_value=self.plan))
            return d.run(entry.TARGET,entry.child_argv('/inert/plan.json','a'*64,self.w),self.w,8,io_admission=dict(path='/inert',sha256='0'*64))
    def test_success_audits_before_reap_and_reverse_close(self):
        self.assertEqual(self.run_parent(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn:inert','await:inert','audit','settle:inert','close:cpu','close:io'])
    def test_failed_known_prefix_closes_without_functional_pass(self):
        self.fail();self.exit=7;self.assertEqual(self.run_parent(),7)
        self.assertEqual(json.loads((self.w/'SHARED-SERVER-AUDIT.json').read_text())['functional_status'],'FAILED')
    def test_unknown_direct_group_retains_before_reap(self):
        self.result['invocations'][0]['outcome']['client_cleanup']['other_group_members_absent_before_reap']=False
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_complete_result_failed_exit_retains(self):
        self.exit=1
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_failed_result_success_exit_retains(self):
        self.fail()
        with self.assertRaises(Retained):self.run_parent()
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_live_worker_retains_without_audit_or_reap(self):
        self.live=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('audit',self.events);self.assertNotIn('settle:inert',self.events)
    def test_cpu_close_uncertainty_retains_io_without_retry(self):
        self.cpu.error=UnresolvedOwnership('injected before any OS close')
        with self.assertRaises(Retained):self.run_parent()
        self.assertEqual(self.events.count('close:cpu'),1);self.assertNotIn('close:io',self.events)
if __name__=='__main__':unittest.main()
