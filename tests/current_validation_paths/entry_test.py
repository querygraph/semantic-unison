"""Metadata/pool/worker doubles only; no native entry execution or lock."""
from contextlib import ExitStack
import shutil,time,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from shared_io_pool import UnresolvedIOOwnership
from current_validation_paths import entry,admission as A
from current_validation_paths.admission_test import fixture


def request(packet,plan):
    return dict(schema='unison-current-named-receiving-request/1',state='PREPARED_UNADMITTED',target=A.TARGET,plan=plan,
        workspace=packet['workspace'],compiler=packet['compiler'],command=A.worker_command(packet,plan),
        source_pins=packet['source_pins'],production_sha256=packet['production_sha256'],limits=packet['limits'])


class Modes(unittest.TestCase):
    def test_check_only_never_runs_owner_or_worker(self):
        packet,*_=fixture()
        with patch.object(entry,'checked',return_value=(packet,{},dict(runtime_admitted=False))), \
             patch.object(entry,'run_owner') as owner,patch.object(entry,'worker') as worker:
            self.assertEqual(entry.main(['--plan','/private/tmp/plan.json','--plan-sha256','1'*64,'--check-plan']),0)
            owner.assert_not_called();worker.assert_not_called()
    def test_missing_admission_or_mixed_modes_refuse_before_metadata(self):
        for args in ([],['--worker','--admission','/private/tmp/admission.json','--admission-sha256','2'*64]):
            with patch.object(entry,'checked') as checked:
                with self.assertRaises(ValueError):entry.main(['--plan','/private/tmp/plan.json','--plan-sha256','1'*64,*args])
                checked.assert_not_called()
    def test_failed_prefix_closes_but_exits_one_and_retained_state_exits_75(self):
        packet,*_=fixture()
        for value,code in ((dict(state='OWNED_WORKER_AND_EXTERNAL_CHILDREN_CLOSED',complete=True),0),
                           (dict(state='OWNED_WORKER_AND_EXTERNAL_CHILDREN_CLOSED',complete=False),1),
                           (dict(state='CONTENTION_UNSTARTED_CONSUMED'),75)):
            with patch.object(entry,'checked',return_value=(packet,{},{})),patch.object(entry,'run_owner',return_value=value):
                self.assertEqual(entry.main(['--plan','/private/tmp/plan.json','--plan-sha256','1'*64,
                    '--admission','/private/tmp/a.json','--admission-sha256','2'*64]),code)
    def test_request_cannot_replace_command_or_compiler(self):
        packet,_,_,plan,_=fixture();value=request(packet,plan);entry.request_check(value,packet,plan)
        for key,changed in (('command',['/unreviewed']),('compiler','ox')):
            with self.subTest(key=key),self.assertRaises(ValueError):entry.request_check(dict(value,**{key:changed}),packet,plan)
    def test_owner_uses_exact_pools_and_sanitized_environment(self):
        packet,grant,_,plan,_=fixture()
        with ExitStack() as stack:
            stack.enter_context(patch.object(entry,'document',side_effect=[grant,request(packet,plan)]))
            stack.enter_context(patch.object(entry.time,'time',return_value=100))
            stack.enter_context(patch.object(entry,'read_bytes',return_value=b'policy'))
            stack.enter_context(patch.object(entry,'authorized_unison_tokens',return_value=tuple(range(8))))
            cpu=stack.enter_context(patch.object(entry.Pool,'read',return_value='cpu'))
            io=stack.enter_context(patch.object(entry.GlobalPool,'read',return_value='io'))
            run=stack.enter_context(patch.object(entry.owner,'run',return_value=dict(original=True)))
            self.assertEqual(entry.run_owner(packet,plan,dict(path='/private/tmp/admit.json',sha256='f'*64)),dict(original=True))
            kwargs=run.call_args.kwargs;self.assertEqual((kwargs['cpu_pool'],kwargs['io_pool']),('cpu','io'))
            self.assertEqual(kwargs['environment']['HOME'],packet['workspace']);self.assertNotIn('PYTHONPATH',kwargs['environment'])
            cpu.assert_called_once_with(entry.CPU_MANIFEST,entry.CPU_SHA);io.assert_called_once_with(entry.CANONICAL_MANIFEST,entry.CANONICAL_SHA256)


class Workers(unittest.TestCase):
    def call(self,fault=None):
        root=Path('/private/tmp')/('u-vpath-'+uuid.uuid4().hex[:16]);packet,_,_,plan,_=fixture(workspace=str(root))
        root.mkdir(mode=0o700);(root/'OWNER-START-READY').mkdir(mode=0o700);self.events=[]
        resources=[dict(fd=700+i,device=1,inode=700+i) for i in range(9)]
        start=dict(admission_nonce='a'*32,inherited_resource_fds=resources,owner_observation_deadline=time.monotonic()+600)
        bound=dict(admission_nonce='a'*32,plan=plan);binding=dict(inherited_fds=tuple(range(700,709)))
        store=SimpleNamespace(fd=777,closed=False)
        store.read_json=lambda name,**kw:start if name=='OWNER-START.json' else bound
        store.write=lambda name,value:self.events.append(('write',name,value.get('result_complete','-')))
        def close():
            store.closed=True;self.events.append(('store-close',))
            if fault=='directory':raise UnresolvedIOOwnership('inert dir close',uncertain_closes=[dict(fd=777,role='inert',observed_before_close=None)])
        store.close=close
        def run(packet,store,inherited,deadline):
            self.assertEqual(inherited,resources);self.events.append(('runtime',))
            if fault=='runtime':raise ValueError('inert unresolved worker')
            return dict(result=dict(complete=fault!='prefix'),worker_metadata_closed=True,resource_release_authorized=False)
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(entry,'Store',return_value=store))
                stack.enter_context(patch.object(entry,'verify_binding',return_value=binding))
                stack.enter_context(patch.object(entry,'artifacts',side_effect=lambda _:self.events.append(('artifacts',))))
                stack.enter_context(patch.object(entry.runtime,'run',side_effect=run))
                stack.enter_context(patch.object(entry,'checked',side_effect=lambda _:self.events.append(('metadata',))))
                stack.enter_context(patch.object(entry,'close_descriptors',side_effect=lambda fds:self.events.append(('resources-close',tuple(fds)))))
                return entry.worker(packet,plan,str(root))
        finally:shutil.rmtree(root)
    def test_close_only_after_runtime_final_rechecks_and_closed_record(self):
        for fault,complete in ((None,True),('prefix',False)):
            self.assertEqual(self.call(fault),0)
            self.assertEqual(self.events,[('write','WORKER-BINDING.json','-'),('artifacts',),('runtime',),('metadata',),('artifacts',),
                ('write','WORKER-CLOSED.json',complete),('store-close',),('resources-close',tuple(range(700,709)))])
    def test_unresolved_runtime_or_directory_keeps_inherited_resources(self):
        for fault in ('runtime','directory'):
            with self.subTest(fault=fault),self.assertRaises(Exception) as caught:self.call(fault)
            self.assertTrue(set(range(700,709))<=set(caught.exception.retained_fds))
            self.assertFalse(any(e[0]=='resources-close' for e in self.events))

if __name__=='__main__':unittest.main()
