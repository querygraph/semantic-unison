"""Original inert pool/child/auditor doubles and tiny private JSON records."""
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
import uuid
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership
from sdk_negative_receiving import admission as A,owner
from sdk_negative_receiving.admission_test import fixture

class Lease:
    def __init__(self,label,events,fds,fault):
        self.label=label;self.events=events;self.fds=fds;self.closed=False;self.fault=fault
    def close_after_verified_settlement(self,**proof):
        if self.closed:raise AssertionError('numeric close retry')
        assert all(value is True for value in proof.values())
        self.closed=True;self.events.append('close-'+self.label)
        if self.fault==self.label+'-close':
            raise UnresolvedIOOwnership('inert injected close',retained_fds=self.fds[1:],
                uncertain_closes=[dict(fd=self.fds[0],role='inert',observed_before_close=None)])

class Owners(unittest.TestCase):
    def setUp(self):self.roots=[];self.carriers=[]
    def tearDown(self):
        # Only real metadata directories are owned here. Pool descriptors and
        # child handles are inert doubles; no OS close failure is injected.
        for error in self.carriers:
            store=error.negative_owner['store']
            if store is not None and not store.closed:store.close()
        for root in self.roots:shutil.rmtree(root,ignore_errors=True)

    def call(self,fault=None):
        packet,grant,request,plan,_=fixture()
        root=Path('/private/tmp')/('u-snr-'+uuid.uuid4().hex[:16]);self.roots.append(root)
        packet['workspace']=grant['workspace']=str(root)
        grant['command']=A.worker_command(packet,plan)
        if fault=='existing':root.mkdir(mode=0o700)
        self.events=[];self.cpu=Lease('cpu',self.events,tuple(range(701,709)),fault)
        self.io=Lease('io',self.events,(900,),fault)
        def acquire_io():self.events.append('acquire-io');return None if fault=='io-contention' else self.io
        def acquire_cpu(indexes):
            self.assertEqual(indexes,tuple(range(8)));self.events.append('acquire-cpu')
            return None if fault=='cpu-contention' else self.cpu
        def artifact(packet):
            self.events.append('artifacts')
            if fault=='artifact':raise ValueError('inert artifact mismatch')
        def finish(deadline):
            self.events.append('finish-child')
            return dict(returncode=0,original='fake child record')
        self.child=SimpleNamespace(owner=SimpleNamespace(pid=1234567),finish=finish)
        def start(command,environment,pass_fds):
            self.events.append('start-child');self.assertEqual(pass_fds,(*self.cpu.fds,*self.io.fds))
            if fault=='start':raise OSError('inert failed constructor')
            return self.child
        def audit(packet,store,outcome):
            self.events.append('audit-external')
            if fault=='audit':raise ValueError('inert missing SDK proof')
            return dict(external_children_settled=True,scope='inert original only')
        try:
            return owner.run(packet,grant,request_ref=request,plan_ref=plan,
                cpu_pool=SimpleNamespace(try_acquire=acquire_cpu),io_pool=SimpleNamespace(try_acquire=acquire_io),
                artifact_check=artifact,parent_audit=audit,environment={},start_child=start,now=lambda:100,
                describe_fds=lambda cpu,io:[dict(fd=fd,device=1,inode=fd) for fd in (*cpu.fds,*io.fds)])
        except UnresolvedOwnership as error:self.carriers.append(error);raise

    def test_exact_acquire_artifact_start_audit_close_order(self):
        result=self.call()
        self.assertEqual(self.events,['acquire-io','acquire-cpu','artifacts','start-child',
            'finish-child','audit-external','close-cpu','close-io'])
        self.assertTrue(result['cpu_closed']);self.assertTrue(result['io_closed'])
        self.assertFalse(result['parent_terminal_proved'])

    def test_contention_rolls_back_partial_bundle_without_child(self):
        result=self.call('cpu-contention')
        self.assertEqual(result['state'],'CONTENTION_UNSTARTED_CONSUMED')
        self.assertEqual(self.events,['acquire-io','acquire-cpu','close-io'])
        result=self.call('io-contention');self.assertEqual(self.events,['acquire-io'])
        self.assertFalse(result['child_started'])

    def test_existing_namespace_refuses_without_acquiring_any_resource(self):
        with self.assertRaises(FileExistsError):self.call('existing')
        self.assertEqual(self.events,[])

    def test_known_preentry_artifact_failure_closes_without_child_attestation(self):
        with self.assertRaises(ValueError):self.call('artifact')
        self.assertEqual(self.events,['acquire-io','acquire-cpu','artifacts','close-cpu','close-io'])
        self.assertTrue((self.roots[-1]/'PREENTRY-FAILED.json').exists())

    def test_failed_start_constructor_is_unknown_not_an_audited_empty_prefix(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('start')
        error=caught.exception
        self.assertTrue(error.negative_owner['child_attempted']);self.assertFalse(error.negative_owner['child_started'])
        self.assertEqual(set((*self.cpu.fds,*self.io.fds))-set(error.retained_fds),set())
        self.assertFalse(self.cpu.closed);self.assertFalse(self.io.closed)

    def test_missing_external_proof_keeps_child_and_all_resources(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.call('audit')
        self.assertIs(caught.exception.negative_owner['child'],self.child)
        self.assertFalse(self.cpu.closed);self.assertFalse(self.io.closed)
        self.assertNotIn('close-cpu',self.events)

    def test_cpu_close_uncertainty_retains_io_and_every_remaining_cpu_fd(self):
        with self.assertRaises(UnresolvedIOOwnership) as caught:self.call('cpu-close')
        error=caught.exception
        self.assertEqual(error.uncertain_fds,(701,))
        self.assertEqual(set(error.retained_fds),set(range(702,709))|{900})
        self.assertNotIn('close-io',self.events);self.assertFalse(self.io.closed)

if __name__=='__main__':unittest.main()
