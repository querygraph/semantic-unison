"""New target parent control flow with inert owners/receipts and disposable FDs."""
from contextlib import ExitStack
import copy,importlib.util,json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import execute as entry
import result_audit_test as fixtures
import shared_dispatch as d
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
class Retained(BaseException):pass
class Lease:
    def __init__(self,count,events,label):
        self.fds=tuple(os.open('/dev/null',os.O_RDONLY|os.O_CLOEXEC) for _ in range(count))
        self.events=events;self.label=label;self.closed=False;self.error=None
    def close_after_verified_settlement(self,**proof):
        assert all(v is True for v in proof.values()) and not self.closed
        self.events.append('close:'+self.label)
        if self.error:raise self.error
        close_descriptors(self.fds);self.closed=True
    def dispose(self):
        # These FDs were never passed to a real child. Mock-close errors never
        # call os.close, so fixture disposal is not a numeric retry after OS uncertainty.
        if not self.closed:close_descriptors(self.fds);self.closed=True
class Faults(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='u-cpf-',dir='/private/tmp');self.w=Path(self.tmp.name);self.w.chmod(0o700)
        fixture=fixtures.ParentAudit();original=fixture.plan
        fixture.plan=lambda:dict(original(),workspace=str(self.w))
        self.result,self.plan=fixture.positive();self.events=[]
        self.cpu=Lease(8,self.events,'cpu');self.io=Lease(1,self.events,'io');self.live=False;self.exit=0
    def tearDown(self):self.cpu.dispose();self.io.dispose();self.tmp.cleanup()
    def failed(self):
        self.result.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='original failed call')
        self.result['invocations']=self.result['invocations'][:1];self.result['cases']=self.result['cases'][:1]
        outcome=self.result['invocations'][0]['outcome'];outcome['returncode']=1;outcome['client_cleanup']['returncode']=1
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
        real_spec=importlib.util.spec_from_file_location
        def spec(name,path):
            value=real_spec(name,path)
            if name=='camera_receiving_result_audit':
                self.assertEqual(Path(path),entry.HERE/'result_audit.py');load=value.loader.exec_module
                def observed(module):
                    load(module);audit=module.audit
                    def run(*args,**kw):self.events.append('audit');self.assertFalse(self.cpu.closed or self.io.closed);return audit(*args,**kw)
                    module.audit=run
                value.loader.exec_module=observed
            return value
        pool=IO();deadline=time.time()+60
        with ExitStack() as stack:
            for target,name,value in [(d.Pool,'read',CPU()),(d,'checked_io_request',lambda *a:(pool,deadline)),
                (d,'OwnedGroup',Owner),(d,'settle',settle),(d,'retain_after_record',retain)]:
                stack.enter_context(patch.object(target,name,side_effect=value) if callable(value) else patch.object(target,name,return_value=value))
            stack.enter_context(patch('shared_io_pool.read_manifest',return_value=self.plan))
            stack.enter_context(patch('importlib.util.spec_from_file_location',side_effect=spec))
            return d.run(entry.TARGET,entry.child_argv('/inert/plan.json','a'*64,self.w),self.w,8,
                         io_admission=dict(path='/inert/no-real-admission',sha256='0'*64))
    def test_audit_precedes_reap_and_reverse_close(self):
        self.assertEqual(self.run_parent(),0)
        self.assertEqual(self.events,['acquire:io','acquire:cpu','spawn:inert','await:inert','audit','settle:inert','close:cpu','close:io'])
    def test_unknown_group_retains_before_reap(self):
        self.result['invocations'][0]['outcome']['stdout']=self.result['invocations'][0]['outcome']['stdout'].replace('other-members=0','other-members=unknown',1)
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_failed_prefix_can_close_without_passing(self):
        self.failed();self.exit=7;self.assertEqual(self.run_parent(),7)
        proof=json.loads((self.w/'SHARED-SERVER-AUDIT.json').read_text())
        self.assertEqual(proof['functional_status'],'FAILED');self.assertEqual(len(proof['helper_settlements']),2)
        self.assertTrue(self.cpu.closed and self.io.closed)
    def test_failed_result_success_exit_retains(self):
        self.failed()
        with self.assertRaises(Retained):self.run_parent()
        self.assertIn('settle:inert',self.events);self.assertFalse(self.cpu.closed or self.io.closed)
    def test_live_observation_keeps_all_grants(self):
        self.live=True
        with self.assertRaises(Retained):self.run_parent()
        self.assertNotIn('audit',self.events);self.assertNotIn('settle:inert',self.events)
        self.assertFalse(self.cpu.closed or self.io.closed)
    def test_close_uncertainty_keeps_io_and_does_not_retry(self):
        self.cpu.error=UnresolvedOwnership('inert close uncertainty')
        with self.assertRaises(Retained):self.run_parent()
        self.assertEqual(self.events.count('close:cpu'),1);self.assertNotIn('close:io',self.events)
        self.assertFalse(self.io.closed)
if __name__=='__main__':unittest.main()
