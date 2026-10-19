"""Inert pool/child/auditor doubles and tiny private JSON records only."""
from pathlib import Path
import shutil,unittest,uuid
from types import SimpleNamespace
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership
from current_validation_paths import owner
from current_validation_paths.admission_test import fixture


class Lease:
    def __init__(self,label,events,fds,fault):self.label=label;self.events=events;self.fds=fds;self.closed=False;self.fault=fault
    def close_after_verified_settlement(self,**proof):
        if self.closed:raise AssertionError('numeric close retry')
        assert all(value is True for value in proof.values())
        self.closed=True;self.events.append('close-'+self.label)
        if self.fault==self.label+'-close':
            raise UnresolvedIOOwnership('inert injected close',retained_fds=self.fds[1:],uncertain_closes=[dict(fd=self.fds[0],role='inert',observed_before_close=None)])


class Owners(unittest.TestCase):
    def setUp(self):self.roots=[];self.carriers=[]
    def tearDown(self):
        for error in self.carriers:
            store=error.named_owner['store']
            if store is not None and not store.closed:store.close()
        for root in self.roots:shutil.rmtree(root,ignore_errors=True)
    def call(self,fault=None):
        root=Path('/private/tmp')/('u-vpath-'+uuid.uuid4().hex[:16]);self.roots.append(root)
        packet,grant,request,plan,_=fixture(workspace=str(root))
        if fault=='existing':root.mkdir(mode=0o700)
        self.events=[];self.cpu=Lease('cpu',self.events,tuple(range(701,709)),fault);self.io=Lease('io',self.events,(900,),fault)
        def acquire_io():self.events.append('acquire-io');return None if fault=='io-contention' else self.io
        def acquire_cpu(indexes):
            self.assertEqual(indexes,tuple(range(8)));self.events.append('acquire-cpu');return None if fault=='cpu-contention' else self.cpu
        def artifact(packet):
            self.events.append('artifacts')
            if fault=='artifact':raise ValueError('inert artifact mismatch')
        def finish(deadline):self.events.append('finish-child');return dict(returncode=0)
        self.child=SimpleNamespace(owner=SimpleNamespace(pid=1234567),finish=finish)
        def start(command,environment,pass_fds):
            self.events.append('start-child');self.assertEqual(pass_fds,(*self.cpu.fds,*self.io.fds))
            if fault=='start':raise OSError('inert failed constructor')
            return self.child
        def audit(packet,store,outcome):
            self.events.append('audit')
            if fault=='audit':raise ValueError('inert raw replay mismatch')
            if fault=='unclassified':return dict(external_children_settled=True)
            return dict(external_children_settled=True,complete=fault!='prefix')
        try:
            return owner.run(packet,grant,request_ref=request,plan_ref=plan,cpu_pool=SimpleNamespace(try_acquire=acquire_cpu),
                io_pool=SimpleNamespace(try_acquire=acquire_io),artifact_check=artifact,parent_audit=audit,environment={},
                start_child=start,now=lambda:100,describe_fds=lambda cpu,io:[dict(fd=fd,device=1,inode=fd) for fd in (*cpu.fds,*io.fds)])
        except UnresolvedOwnership as error:self.carriers.append(error);raise
    def test_exact_order_and_settled_failed_prefix_still_closes_but_reports_incomplete(self):
        for fault,complete in ((None,True),('prefix',False)):
            result=self.call(fault)
            self.assertEqual(self.events,['acquire-io','acquire-cpu','artifacts','start-child','finish-child','audit','close-cpu','close-io'])
            self.assertEqual(result['complete'],complete);self.assertTrue(result['cpu_closed'] and result['io_closed'])
            self.assertFalse(result['parent_terminal_proved'])
    def test_contention_rolls_back_without_child(self):
        self.assertEqual(self.call('cpu-contention')['state'],'CONTENTION_UNSTARTED_CONSUMED')
        self.assertEqual(self.events,['acquire-io','acquire-cpu','close-io'])
        self.call('io-contention');self.assertEqual(self.events,['acquire-io'])
    def test_existing_namespace_refuses_without_resources(self):
        with self.assertRaises(FileExistsError):self.call('existing')
        self.assertEqual(self.events,[])
    def test_preentry_artifact_failure_closes_without_child(self):
        with self.assertRaises(ValueError):self.call('artifact')
        self.assertEqual(self.events,['acquire-io','acquire-cpu','artifacts','close-cpu','close-io'])
    def test_start_audit_or_unclassified_audit_retain_child_and_all_resources(self):
        for fault in ('start','audit','unclassified'):
            with self.subTest(fault=fault),self.assertRaises(UnresolvedOwnership) as caught:self.call(fault)
            self.assertTrue(set((*self.cpu.fds,*self.io.fds))<=set(caught.exception.retained_fds))
            self.assertFalse(self.cpu.closed or self.io.closed)
    def test_cpu_close_uncertainty_retains_io(self):
        with self.assertRaises(UnresolvedIOOwnership) as caught:self.call('cpu-close')
        self.assertEqual(caught.exception.uncertain_fds,(701,));self.assertEqual(set(caught.exception.retained_fds),set(range(702,709))|{900})
        self.assertFalse(self.io.closed)

if __name__=='__main__':unittest.main()
