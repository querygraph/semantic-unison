"""Original metadata/pool/worker doubles; no native entry execution or IO locks."""
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch
import uuid
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import UnresolvedIOOwnership
from sdk_negative_receiving import entry,admission as A
from sdk_negative_receiving.admission_test import fixture

class Modes(unittest.TestCase):
    def test_check_only_never_runs_owner_or_worker(self):
        packet,*_=fixture()
        with patch.object(entry,'checked',return_value=(packet,{},dict(runtime_admitted=False))), \
             patch.object(entry,'run_owner') as owner,patch.object(entry,'worker') as worker:
            self.assertEqual(entry.main(['--plan','/private/tmp/plan.json','--plan-sha256','1'*64,'--check-plan']),0)
            owner.assert_not_called();worker.assert_not_called()

    def test_missing_admission_or_mixed_modes_refuse_before_metadata_or_payload(self):
        for args in ([],['--worker','--admission','/private/tmp/admission.json','--admission-sha256','2'*64]):
            with patch.object(entry,'checked') as checked:
                with self.assertRaises(ValueError):entry.main(['--plan','/private/tmp/plan.json','--plan-sha256','1'*64,*args])
                checked.assert_not_called()

    def test_request_cannot_replace_the_owner_derived_command(self):
        packet,_,_,plan,_=fixture()
        request=dict(schema='unison-current-sdk-negative-receiving-request/1',state='PREPARED_UNADMITTED',
            target='current-sdk-negative-receiving',plan=plan,workspace=packet['workspace'],
            command=A.worker_command(packet,plan),execution_sha256=packet['execution_sha256'],
            production_sha256=packet['production_sha256'],limits=packet['limits'])
        entry.request_check(request,packet,plan)
        request['command']=['/unreviewed/program']
        with self.assertRaises(ValueError):entry.request_check(request,packet,plan)

    def test_owner_uses_exact_existing_pools_and_sanitized_environment(self):
        packet,grant,request_ref,plan,_=fixture()
        request=dict(schema='unison-current-sdk-negative-receiving-request/1',state='PREPARED_UNADMITTED',
            target='current-sdk-negative-receiving',plan=plan,workspace=packet['workspace'],command=A.worker_command(packet,plan),
            execution_sha256=packet['execution_sha256'],production_sha256=packet['production_sha256'],limits=packet['limits'])
        with ExitStack() as stack:
            stack.enter_context(patch.object(entry,'document',side_effect=[grant,request]))
            stack.enter_context(patch.object(entry.time,'time',return_value=100))
            stack.enter_context(patch.object(entry,'read_bytes',return_value=b'original policy'))
            stack.enter_context(patch.object(entry,'authorized_unison_tokens',return_value=tuple(range(8))))
            cpu=stack.enter_context(patch.object(entry.Pool,'read',return_value='original-cpu'))
            io=stack.enter_context(patch.object(entry.GlobalPool,'read',return_value='original-io'))
            run=stack.enter_context(patch.object(entry.owner,'run',return_value=dict(original=True)))
            self.assertEqual(entry.run_owner(packet,plan,dict(path='/private/tmp/admit.json',sha256='f'*64)),dict(original=True))
            self.assertEqual(run.call_args.kwargs['cpu_pool'],'original-cpu')
            self.assertEqual(run.call_args.kwargs['io_pool'],'original-io')
            environment=run.call_args.kwargs['environment']
            self.assertEqual(environment['HOME'],packet['workspace'])
            self.assertEqual(environment['PYTHONNOUSERSITE'],'1')
            self.assertNotIn('PYTHONPATH',environment)
            cpu.assert_called_once_with(entry.CPU_MANIFEST,entry.CPU_SHA)
            io.assert_called_once_with(entry.CANONICAL_MANIFEST,entry.CANONICAL_SHA256)

class Workers(unittest.TestCase):
    def call(self,fault=None):
        packet,_,_,plan,_=fixture();root=Path('/private/tmp')/('u-snr-'+uuid.uuid4().hex[:16])
        root.mkdir(mode=0o700);(root/'OWNER-START-READY').mkdir(mode=0o700)
        packet['workspace']=str(root);self.events=[]
        resources=[dict(fd=700+i,device=1,inode=700+i) for i in range(9)]
        start=dict(admission_nonce='a'*32,inherited_resource_fds=resources,
                   owner_observation_deadline=time.monotonic()+600)
        bound=dict(admission_nonce='a'*32,plan=plan)
        binding=dict(inherited_fds=tuple(range(700,709)))
        store=SimpleNamespace(fd=777,closed=False)
        store.read_json=lambda name,**kw:start if name=='OWNER-START.json' else bound
        store.write=lambda name,value:self.events.append(('write',name))
        def close():
            store.closed=True;self.events.append(('store-close',))
            if fault=='directory':raise UnresolvedIOOwnership('inert dir close',uncertain_closes=[
                dict(fd=777,role='inert',observed_before_close=None)])
        store.close=close
        def close_fds(fds):
            self.events.append(('resources-close',tuple(fds)))
            if fault=='resources':raise UnresolvedIOOwnership('inert partial close',retained_fds=tuple(range(700,706)),
                uncertain_closes=[dict(fd=706,role='inert',observed_before_close=None)])
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(entry,'Store',return_value=store))
                stack.enter_context(patch.object(entry,'verify_binding',return_value=binding))
                stack.enter_context(patch.object(entry.artifacts,'verify',side_effect=lambda _:self.events.append(('artifacts',))))
                stack.enter_context(patch.object(entry.runtime,'run',side_effect=lambda *a:self.events.append(('runtime',))))
                stack.enter_context(patch.object(entry,'checked',side_effect=lambda _:self.events.append(('metadata',))))
                stack.enter_context(patch.object(entry,'close_descriptors',side_effect=close_fds))
                return entry.worker(packet,plan,str(root))
        finally:shutil.rmtree(root)

    def test_normal_close_happens_only_after_runtime_and_final_rechecks(self):
        self.assertEqual(self.call(),0)
        self.assertEqual(self.events,[('write','WORKER-BINDING.json'),('artifacts',),('runtime',),
            ('metadata',),('artifacts',),('store-close',),('resources-close',tuple(range(700,709)))])

    def test_directory_uncertainty_keeps_all_inherited_resource_fds(self):
        with self.assertRaises(UnresolvedIOOwnership) as caught:self.call('directory')
        self.assertEqual(caught.exception.uncertain_fds,(777,))
        self.assertEqual(set(caught.exception.retained_fds),set(range(700,709)))
        self.assertFalse(any(e[0]=='resources-close' for e in self.events))

    def test_partial_resource_close_never_resurrects_already_closed_numbers(self):
        with self.assertRaises(UnresolvedIOOwnership) as caught:self.call('resources')
        self.assertEqual(caught.exception.uncertain_fds,(706,))
        self.assertEqual(caught.exception.retained_fds,tuple(range(700,706)))
        self.assertNotIn(707,caught.exception.retained_fds);self.assertNotIn(708,caught.exception.retained_fds)

if __name__=='__main__':unittest.main()
