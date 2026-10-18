"""Original disposable/fabricated controls. No canonical locks or RPC dispatch."""
from copy import deepcopy
import json
import ast
import inspect
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote import audit, case, call, coordinator, io, producer_schema
from component_remote.contract import CASES, FLAGS, command, checked_plan, sources, PARAMETERS
from shared_cpu_pool import UnresolvedOwnership, close_descriptors

def client_group(pid,code=0):return {'pid':pid,'returncode':code,'reaped':True,'hard_kill_required':False,
 'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True}
def supervisor_group(pid,code=0):return {'pid':pid,'returncode':code,'reaped':True,
 'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True,
 'members_before_reap':[{'pid':pid,'state':'Z'}],'timed_out':False,
 'scope':'owned group only; separate sessions require independently audited proofs'}
def server_group(pid,code=0):return {'pid':pid,'returncode':code,'reaped':True,
 'cancel_reason':None,'hard_kill_required':False}
def outcome(plan,index):
    pid=900+index*3;server=plan['artifacts'][CASES[index][1]]['path'];base=[server,'-server','__new-rpc-mode']
    return {'command':command(plan,index),'returncode':0,'timed_out':False,'capture_truncated':False,
      'supervisor_capture_truncated':False,'client_cleanup':client_group(pid),'supervisor_cleanup':supervisor_group(pid+1),
      'stdout':'','proxy':{'schema':'unison-loopback-protocol-count/1','server_cleanup':server_group(pid+2),
      'server_pid':pid+2,'server_returncode':0,'server_command':base+FLAGS,
      'launcher_control_header_bytes_excluded':4+len(json.dumps(base).encode()),
      'server_group_binding':{'native_pid':pid+2,'native_process_group':pid+1,'supervisor_pid':pid+1,
        'supervisor_process_group':pid+1,'observed_before_native_reap':True},
      'input_pump_joined':True,'pump_errors':[],'fault':None}}
def plan(workspace):return {'workspace':str(workspace),'artifacts':{key:{'path':'/fixed/'+key}
    for key in ('stock','ox','old-stock','stock-probe','ox-probe')}}
def record(p,index,value):
    directory=Path(p['workspace'])/str(index);directory.mkdir(mode=0o700,exist_ok=True)
    io.save(directory/'INTENT.json',{'index':index,'command':command(p,index)})
    io.save(directory/'OUTCOME.json',value);io.save(directory/'proxy.json',value['proxy'])

class Retained(Exception):pass
class Controls(unittest.TestCase):
    def test_frozen_plan_source_scope_and_canonical_namespace(self):
        p={'schema':'unison-component-remote/1','workspace':'/private/tmp/u-cr-0123456789ab',
          'parameters':deepcopy(PARAMETERS),'execution_source_sha256':sources(),
          'artifacts':{key:{'path':'/fixed/'+key,'sha256':'0'*64}
             for key in ('stock','ox','old-stock','stock-probe','ox-probe')},
          'prerequisites':[{'path':'/fixed/p'+str(i),'sha256':'0'*64} for i in range(3)],
          'interpreter':{'path':sys.executable,'sha256':'0'*64},
          'io_manifest_sha256':coordinator.CANONICAL_SHA256,'cpu_manifest_sha256':coordinator.MANIFEST_SHA}
        self.assertEqual(checked_plan(p),Path(p['workspace']))
        for mutate in (lambda v:v['parameters'].update(call_seconds=120),
                       lambda v:v['execution_source_sha256'].pop(str(ROOT/'src/semanticRemote.ml')),
                       lambda v:v.update(workspace='/private/tmp/u-cr-not-a-nonce'),
                       lambda v:v.update(io_manifest_sha256='0'*64)):
            bad=deepcopy(p);mutate(bad)
            with self.assertRaises(ValueError):checked_plan(bad)

    def test_source_schema_matches_real_producers_instead_of_test_fabrication(self):
        tree=ast.parse((ROOT/'tests/sdk_host_matrix/shared_child.py').read_text())
        definitions=[node.value for node in ast.walk(tree) if isinstance(node,ast.keyword)
          and node.arg=='client_cleanup' and isinstance(node.value,ast.Call)]
        self.assertEqual(len(definitions),1)
        self.assertEqual({node.arg for node in definitions[0].keywords},producer_schema.CLIENT_KEYS)
        tree=ast.parse((ROOT/'tests/shared_process_owner.py').read_text())
        settle=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='settle')
        returns=[node.value for node in ast.walk(settle) if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict)]
        self.assertEqual(len(returns),1)
        emitted={node.value for node in returns[0].keys}
        tree=ast.parse((ROOT/'tests/component_remote/call.py').read_text())
        appended={target.slice.value for node in ast.walk(tree) if isinstance(node,ast.Assign)
          for target in node.targets if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name)
          and target.value.id=='stopped' and isinstance(target.slice,ast.Constant)}
        self.assertEqual(appended,{'group_cleanup_before_leader_reap'})
        self.assertEqual(emitted|appended,producer_schema.SUPERVISOR_KEYS)
        self.assertIn(str(ROOT/'tests/component_remote/producer_schema.py'),sources())

    def test_eight_projected_actual_receipts_match_accepted_schema(self):
        vector=io.load(ROOT/'tests/component_remote/producer-shapes-v1.json')
        self.assertEqual(vector['schema'],'component-rpc-actual-producer-shapes/1')
        historical=io.load(ROOT/'doc/component-remote-plan-v1.json')['execution_source_sha256']
        for name,digest in vector['producer_source_sha256'].items():
            matches=[value for path,value in historical.items() if path.endswith('/'+name)]
            self.assertEqual(matches,[digest])
        # Historical receipt provenance stays immutable when unrelated producer
        # comments change; the separate AST check binds the CURRENT field shape.
        self.assertEqual([row['index'] for row in vector['runs']],list(range(8)))
        for row in vector['runs']:
            value=row['projected_run'];producer_schema.successful_call(value)
            self.assertNotIn('cancel_reason',value['client_cleanup'])
            self.assertNotIn('cancel_reason',value['supervisor_cleanup'])
            for key in ('client_cleanup','supervisor_cleanup'):
                bad=deepcopy(value);bad[key]['cancel_reason']=None
                with self.assertRaises(ValueError):producer_schema.successful_call(bad)
        from component_remote.saved_functional import successful_call as accepted_saved_predicate
        # Preserve the sealed saved implementation while ensuring the new shared
        # runtime predicate has the same already-adopted body and declared keys.
        self.assertEqual(ast.dump(ast.parse(inspect.getsource(accepted_saved_predicate))),
                         ast.dump(ast.parse(inspect.getsource(producer_schema.successful_call))))

    def test_schema_helper_is_mandatory_in_future_source_inventory(self):
        p={'schema':'unison-component-remote/1','workspace':'/private/tmp/u-cr-0123456789ab',
          'parameters':deepcopy(PARAMETERS),'execution_source_sha256':sources(),
          'artifacts':{key:{'path':'/fixed/'+key,'sha256':'0'*64}
             for key in ('stock','ox','old-stock','stock-probe','ox-probe')},
          'prerequisites':[{'path':'/fixed/p'+str(i),'sha256':'0'*64} for i in range(3)],
          'interpreter':{'path':sys.executable,'sha256':'0'*64},
          'io_manifest_sha256':coordinator.CANONICAL_SHA256,'cpu_manifest_sha256':coordinator.MANIFEST_SHA}
        self.assertEqual(checked_plan(p),Path(p['workspace']))
        del p['execution_source_sha256'][str(ROOT/'tests/component_remote/producer_schema.py')]
        with self.assertRaises(ValueError):checked_plan(p)

    def test_exact_native_group_binding_and_raw_command(self):
        p=plan(Path('/fixed/work'));v=outcome(p,0)
        self.assertFalse(audit.settlement(v,command(p,0),'/fixed/stock')['server_not_created'])
        mutations=[lambda v:v['client_cleanup'].update(reaped=False),
          lambda v:v['supervisor_cleanup'].update(other_group_members_absent_before_reap=False),
          lambda v:v['proxy'].update(input_pump_joined=False),
          lambda v:v['proxy']['server_group_binding'].update(native_process_group=7),
          lambda v:v['proxy']['server_command'].append('-unexpected'),
          lambda v:v['proxy'].update(launcher_control_header_bytes_excluded=4),
          lambda v:v['proxy'].update(server_pid=v['client_cleanup']['pid']),
          lambda v:v.update(returncode=1)]
        for mutate in mutations:
            bad=deepcopy(v);mutate(bad)
            with self.assertRaises(ValueError):audit.settlement(bad,command(p,0),'/fixed/stock')

    def test_known_failed_call_settles_without_functional_success(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);v=outcome(p,0)
            v['returncode']=v['client_cleanup']['returncode']=1;record(p,0,v)
            self.assertEqual(len(audit.audit_prefix(p,work)),1)
            with self.assertRaises(ValueError):audit.functional(p,{'complete':False,'cases':[]},work)

    def test_pending_intent_or_raw_proxy_substitution_retains(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);d=work/'0';d.mkdir()
            io.save(d/'INTENT.json',{'index':0,'command':command(p,0)})
            with self.assertRaises(ValueError):audit.audit_prefix(p,work)
            v=outcome(p,0);io.save(d/'OUTCOME.json',v);io.save(d/'proxy.json',{})
            with self.assertRaises(ValueError):audit.audit_prefix(p,work)

    def test_explicit_no_creation_requires_complete_proxy_and_groups(self):
        p=plan(Path('/fixed/work'));v=outcome(p,0)
        v['returncode']=v['client_cleanup']['returncode']=1
        v['supervisor_cleanup']['returncode']=70
        v['proxy']={'schema':'unison-loopback-protocol-count/1',
          **{k:None for k in ('server_command','server_pid','server_returncode','server_cleanup',
                             'server_resources','launcher_control_header_bytes_excluded')},
          'forwarded_protocol_bytes':{'client_to_server_bytes':0,'server_to_client_bytes':0},
          'input_pump_joined':True,'pump_errors':[],'fault':'original pre-creation refusal'}
        self.assertTrue(audit.settlement(v,command(p,0),'/fixed/stock')['server_not_created'])
        for key in ('server_command','input_pump_joined','fault'):
            bad=deepcopy(v);del bad['proxy'][key]
            with self.assertRaises((ValueError,KeyError)):audit.settlement(bad,command(p,0),'/fixed/stock')

    def test_no_dispatch_marker_and_nonprefix_are_distinct(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);d=work/'0';d.mkdir()
            io.save(d/'NO-DISPATCH.json',{'schema':'component-no-dispatch/1','index':0,'measure_entered':False})
            self.assertEqual(audit.audit_prefix(p,work),[{'index':0,'no_dispatch':True}])
            (work/'1').mkdir()
            with self.assertRaises(ValueError):audit.audit_prefix(p,work)

    def test_fixture_scope_and_functional_independent_readback(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);result={'complete':True,'cases':[]}
            for index,(_,_,mode) in enumerate(CASES):
                d=work/str(index);d.mkdir(mode=0o700)
                for side in ('left','right'):(d/side).mkdir(mode=0o700)
                io.write(d/'left/components.dng',case.fixture())
                io.write(d/'right/components.dng',case.fixture(True,mode=='unsupported'))
                before=case.snapshot(d);v=outcome(p,index)
                v['stdout']='PROBE_FUNCTIONAL '+mode+'\nPROBE_LOCAL_RESOURCES_CLOSED (external client/server wait proofs still required)\n'
                if mode=='supported':
                    v['stdout']+='LOCAL_SHA256 '+before['left']['sha256']+'\nREMOTE_SHA256 '+before['right']['sha256']+'\nEncoded pixels: equal.\nOpaque bytes: different.\n'
                if mode=='unsupported':v['stdout']+='REMOTE_UNSUPPORTED not TIFF\n'
                # record() accepts an already prepared private case directory.
                record(p,index,v);result['cases'].append({'index':index,'mode':mode,
                  'before':before,'after':deepcopy(before),'outcome':v})
            self.assertEqual(audit.functional(p,result,work)['cases'],8)
            path=work/'0/left/components.dng'
            with path.open('r+b') as stream:stream.write(b'X')
            with self.assertRaises(ValueError):audit.functional(p,result,work)

    def test_qualified_close_uncertainty_no_retry(self):
        s=SimpleNamespace(st_dev=1,st_ino=2,st_size=1,st_mtime_ns=3,st_ctime_ns=4,
                          st_mode=stat.S_IFREG|0o600,st_nlink=1,st_uid=os.getuid())
        with patch.object(io.os,'open',return_value=123),patch.object(io.os,'fstat',return_value=s),\
             patch.object(io.os,'read',return_value=b'x'),patch.object(io.os,'close',side_effect=OSError('injected')) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:io.read('/fake')
            self.assertEqual(close.call_count,1)
            self.assertEqual(caught.exception.uncertain_fd,123)
            self.assertEqual(caught.exception.uncertain_closes[0]['observed_before_close']['inode'],2)

    def test_worker_uncertainty_never_audits_as_failed_prefix(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);packet={'plan':p,'parent_pid':os.getppid(),
              'inherited_fds':[{'fd':i,'device':1,'inode':i} for i in range(10,19)],'deadline_monotonic':999999999}
            unknown=UnresolvedOwnership('injected close',uncertain_fd=21)
            with patch.object(coordinator,'load',return_value=packet),\
              patch.object(coordinator,'checked_plan',return_value=work),\
              patch.object(coordinator,'inherited_identities',return_value=[(1,i) for i in range(10,19)]),\
              patch.object(coordinator.os,'fstat',side_effect=lambda fd:SimpleNamespace(st_dev=1,st_ino=fd)),\
              patch.object(coordinator,'check_artifacts'),patch.object(case,'execute',side_effect=unknown),\
              patch.object(coordinator,'audit_prefix') as audit_call,\
              patch.object(coordinator,'unknown',side_effect=Retained) as retain:
                with self.assertRaises(Retained):coordinator.worker(work/'WORKER-PACKET.json')
                audit_call.assert_not_called();self.assertIs(retain.call_args.args[1],unknown)

    def test_close_uncertainty_preserves_original_read_failure(self):
        s=SimpleNamespace(st_dev=1,st_ino=2,st_size=1,st_mtime_ns=3,st_ctime_ns=4,
                          st_mode=stat.S_IFREG|0o600,st_nlink=1,st_uid=os.getuid())
        original=ValueError('original read failure')
        with patch.object(io.os,'open',return_value=123),patch.object(io.os,'fstat',return_value=s),\
             patch.object(io.os,'read',side_effect=original),\
             patch.object(io.os,'close',side_effect=OSError('close failure')) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:io.read('/fake')
            self.assertIs(caught.exception.original_failure,original);self.assertEqual(close.call_count,1)

    def test_write_close_uncertainty_preserves_original_failure(self):
        s=SimpleNamespace(st_dev=1,st_ino=2,st_size=0,st_mtime_ns=3,st_ctime_ns=4,
                          st_mode=stat.S_IFREG|0o600,st_nlink=1,st_uid=os.getuid())
        original=ValueError('original write failure')
        with patch.object(io.os,'open',return_value=124),patch.object(io.os,'fstat',return_value=s),\
             patch.object(io.os,'write',side_effect=original),\
             patch.object(io.os,'close',side_effect=OSError('close failure')) as close:
            with self.assertRaises(UnresolvedOwnership) as caught:io.write('/fake',b'x')
            self.assertIs(caught.exception.original_failure,original);self.assertEqual(close.call_count,1)
            self.assertEqual(caught.exception.uncertain_fd,124)

    def test_worker_rejects_caller_selected_noncanonical_identity_set(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);packet={'plan':plan(work),'parent_pid':os.getppid(),
              'inherited_fds':[{'fd':i,'device':1,'inode':i} for i in range(10,19)]}
            with patch.object(coordinator,'load',return_value=packet),\
              patch.object(coordinator,'checked_plan',return_value=work),\
              patch.object(coordinator,'inherited_identities',return_value=[(2,i) for i in range(10,19)]),\
              patch.object(case,'execute') as execute:
                with self.assertRaises(ValueError):coordinator.worker(work/'WORKER-PACKET.json')
                execute.assert_not_called()

    def owner_fixture(self,root):
        workspace=root/'u-cr-fake';packet=plan(workspace)
        plan_path=root/'plan.json';io.save(plan_path,packet)
        admission_path=root/'admission.json'
        admission={'state':'ROOT_ADMITTED_ONE_COMPONENT_RPC_JOB','plan_sha256':io.sha(plan_path),
          'workspace':str(workspace),'start_deadline_unix':time.time()+60,
          'launch_argv_without_admission_sha256':[sys.executable,str(Path(coordinator.__file__)),
             '--plan',str(plan_path),'--admission',str(admission_path)]}
        fds=[]
        for index in range(9):
            path=root/('fake-resource-'+str(index));io.write(path,b'x');fds.append(os.open(path,os.O_RDONLY))
        class Lease:
            def __init__(self,values):self.fds=values;self.closed=False;self.close_calls=0
            def close_after_verified_settlement(self,**kwargs):
                self.close_calls+=1
                for fd in self.fds:os.close(fd)
                self.closed=True
        return workspace,plan_path,admission_path,admission,Lease(fds[:1]),Lease(fds[1:])

    def test_owner_observation_expiry_retains_without_aggregate_kill(self):
        with tempfile.TemporaryDirectory() as raw:
            work,plan_path,admission_path,admission,io_lease,cpu=self.owner_fixture(Path(raw))
            actual_read=coordinator.read
            try:
                with patch.object(coordinator,'checked_plan',return_value=work),\
                  patch.object(coordinator,'read_manifest',return_value=admission),\
                  patch.object(coordinator,'read',side_effect=lambda p: b'policy' if Path(p)==coordinator.POLICY else actual_read(p)),\
                  patch.object(coordinator,'authorized_unison_tokens',return_value=tuple(range(8))),\
                  patch.object(coordinator.GlobalPool,'read'),patch.object(coordinator.Pool,'read'),\
                  patch.object(coordinator,'try_io_cpu_bundle',return_value=(io_lease,cpu)),\
                  patch.object(coordinator,'check_artifacts'),\
                  patch.object(coordinator,'OwnedGroup',return_value=SimpleNamespace(pid=9999,await_terminal=lambda _:False)),\
                  patch.object(coordinator,'settle') as settle,\
                  patch.object(coordinator,'unknown',side_effect=Retained):
                    with self.assertRaises(Retained):coordinator.owner(plan_path,admission_path,'fake')
                    settle.assert_not_called()
                self.assertEqual((cpu.close_calls,io_lease.close_calls),(0,0))
            finally:
                for lease in (cpu,io_lease):
                    if not lease.closed:
                        for fd in lease.fds:os.close(fd) # known untouched fake FDs, not uncertain numbers

    def test_prechild_artifact_refusal_rolls_back_without_native_dispatch(self):
        with tempfile.TemporaryDirectory() as raw:
            work,plan_path,admission_path,admission,io_lease,cpu=self.owner_fixture(Path(raw))
            actual_read=coordinator.read
            try:
                with patch.object(coordinator,'checked_plan',return_value=work),\
                  patch.object(coordinator,'read_manifest',return_value=admission),\
                  patch.object(coordinator,'read',side_effect=lambda p:b'policy' if Path(p)==coordinator.POLICY else actual_read(p)),\
                  patch.object(coordinator,'authorized_unison_tokens',return_value=tuple(range(8))),\
                  patch.object(coordinator.GlobalPool,'read'),patch.object(coordinator.Pool,'read'),\
                  patch.object(coordinator,'try_io_cpu_bundle',return_value=(io_lease,cpu)),\
                  patch.object(coordinator,'check_artifacts',side_effect=ValueError('stale artifact')),\
                  patch.object(coordinator,'OwnedGroup') as dispatch:
                    self.assertEqual(coordinator.owner(plan_path,admission_path,'fake'),2)
                    dispatch.assert_not_called()
                self.assertEqual((cpu.close_calls,io_lease.close_calls),(1,1))
                self.assertTrue(io.load(work/'NOT-STARTED.json')['known_rollback'])
            finally:
                for lease in (cpu,io_lease):
                    if not lease.closed:
                        for fd in lease.fds:os.close(fd)

    def test_call_preserves_exact_capture_carrier_and_separate_proxy(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);socket=work/'call.sock';io.write(socket,b'fake socket readiness')
            supervisor=SimpleNamespace(pid=9999)
            carrier=UnresolvedOwnership('injected capture close',uncertain_fd=55)
            carrier.uncertain_closes=({'fd':55,'observed_before_close':{'inode':7}},)
            with patch.object(call,'OwnedGroup',return_value=supervisor),\
              patch.object(call,'invoke',side_effect=carrier),patch.object(call,'settle') as settle:
                with self.assertRaises(UnresolvedOwnership) as caught:
                    call.execute(['/fixed/probe'],{'UNISON_SYNC_BENCH_SOCKET':str(socket)},work,time.monotonic()+5)
                self.assertIs(caught.exception,carrier)
                self.assertIs(carrier.component_proxy_owner,supervisor);settle.assert_not_called()

    def test_case_preparation_refusal_proves_no_dispatch(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work)
            with patch.object(case,'read',side_effect=ValueError('original preparation refusal')),\
              patch.object(case,'invoke') as dispatch:
                with self.assertRaises(ValueError):case.execute(p,0,time.monotonic()+60)
                dispatch.assert_not_called()
            proof=io.load(work/'0/NO-DISPATCH.json')
            self.assertIs(proof['measure_entered'],False)
            self.assertEqual(audit.audit_prefix(p,work),[{'index':0,'no_dispatch':True}])

    def test_known_failed_case_has_saved_outcome_and_no_false_no_dispatch(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);p=plan(work);v=outcome(p,0)
            v['returncode']=v['client_cleanup']['returncode']=1
            def failed(argv,environment,directory,deadline):
                io.save(directory/'proxy.json',v['proxy']);return v
            with patch.object(case,'invoke',side_effect=failed):
                with self.assertRaises(ValueError):case.execute(p,0,time.monotonic()+60)
            self.assertFalse((work/'0/NO-DISPATCH.json').exists())
            self.assertEqual(io.load(work/'0/OUTCOME.json')['returncode'],1)
            self.assertEqual(len(audit.audit_prefix(p,work)),1)

    def test_worker_real_producer_shape_success_and_original_predicate_regression(self):
        from component_remote.saved_functional_controls import files
        for old_predicate in (False,True):
            with self.subTest(old_predicate=old_predicate),tempfile.TemporaryDirectory() as raw:
                work=Path(raw);p,recorded=files(work);fds=[]
                try:
                    for index in range(9):
                        path=work/('private-fake-grant-'+str(index));io.write(path,b'x')
                        fds.append(os.open(path,os.O_RDONLY|os.O_CLOEXEC))
                    rows=[{'fd':fd,'device':os.fstat(fd).st_dev,'inode':os.fstat(fd).st_ino} for fd in fds]
                    packet={'plan':p,'parent_pid':os.getppid(),'inherited_fds':rows,'deadline_monotonic':999999999}
                    original_load=coordinator.load
                    def load_packet(path):
                        return packet if Path(path)==work/'WORKER-PACKET.json' else original_load(path)
                    actual=producer_schema.successful_call
                    def predicate(value):
                        if old_predicate:
                            # This is the exact original erroneous assumption.
                            for key in ('client_cleanup','supervisor_cleanup'):value[key]['cancel_reason']
                        return actual(value)
                    with patch.object(coordinator,'load',side_effect=load_packet),\
                      patch.object(coordinator,'checked_plan',return_value=work),\
                      patch.object(coordinator,'inherited_identities',return_value=[(r['device'],r['inode']) for r in rows]),\
                      patch.object(coordinator,'check_artifacts'),\
                      patch.object(case,'execute',side_effect=recorded['cases']) as execute,\
                      patch.object(audit,'successful_call',side_effect=predicate):
                        code=coordinator.worker(work/'WORKER-PACKET.json')
                    result=io.load(work/'WORKER-RESULT.json');settled=io.load(work/'REMOTE-SETTLED.json')
                    self.assertEqual(execute.call_count,8);self.assertEqual(len(result['cases']),8)
                    self.assertEqual(code,1 if old_predicate else 0)
                    self.assertIs(result['complete'],not old_predicate)
                    self.assertIs(settled['functional_pass'],not old_predicate)
                    if old_predicate:self.assertEqual(result['failure'],"KeyError('cancel_reason')")
                    else:self.assertEqual(result['audit']['cases'],8)
                finally:close_descriptors(fds)

    def test_worker_stops_successors_after_known_functional_failure(self):
        with tempfile.TemporaryDirectory() as raw:
            work=Path(raw);packet={'plan':plan(work),'parent_pid':os.getppid(),
              'inherited_fds':[{'fd':i,'device':1,'inode':i} for i in range(10,19)],'deadline_monotonic':999999999}
            with patch.object(coordinator,'load',return_value=packet),\
              patch.object(coordinator,'checked_plan',return_value=work),\
              patch.object(coordinator,'inherited_identities',return_value=[(1,i) for i in range(10,19)]),\
              patch.object(coordinator.os,'fstat',side_effect=lambda fd:SimpleNamespace(st_dev=1,st_ino=fd)),\
              patch.object(coordinator,'check_artifacts'),\
              patch.object(case,'execute',side_effect=ValueError('known functional failure')) as execute,\
              patch.object(coordinator,'audit_prefix',return_value=[{'index':0}]),\
              patch.object(coordinator,'unknown') as unknown:
                self.assertEqual(coordinator.worker(work/'WORKER-PACKET.json'),1)
                self.assertEqual(execute.call_count,1);unknown.assert_not_called()
            self.assertFalse(io.load(work/'WORKER-RESULT.json')['complete'])
            self.assertIs(io.load(work/'REMOTE-SETTLED.json')['functional_pass'],False)

class EarlyClientClosure(unittest.TestCase):
    def test_persist_client_before_full_proxy_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);socket=work/'socket';io.write(socket,b'inert readiness')
            seen=[]
            def awaited(seconds):
                self.assertGreater(seconds,30)
                self.assertEqual(io.load(work/'CLIENT-OUTCOME.json')['returncode'],3)
                seen.append(seconds);return True
            supervisor=SimpleNamespace(pid=9999,await_terminal=awaited)
            with patch.object(call,'OwnedGroup',return_value=supervisor),patch.object(call,'invoke',return_value={'returncode':3}),patch.object(call,'load',return_value={'input_pump_joined':True,'server_cleanup':None}),patch.object(call,'settle',return_value={'other_group_members_absent_before_reap':True}):
                result=call.execute(['/inert/client'],{'UNISON_SYNC_BENCH_SOCKET':str(socket),'UNISON_SYNC_BENCH_DEADLINE_SECONDS':'35'},work,time.monotonic()+30)
            self.assertEqual(result['returncode'],3);self.assertEqual(len(seen),1)

if __name__=='__main__':
    before=sources();before[str(Path(__file__))]=io.sha(__file__);before[str(ROOT/'tests/component_remote/producer-shapes-v1.json')]=io.sha(ROOT/'tests/component_remote/producer-shapes-v1.json');before[str(ROOT/'doc/component-remote-plan-v1.json')]=io.sha(ROOT/'doc/component-remote-plan-v1.json')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    after=sources();after[str(Path(__file__))]=io.sha(__file__);after[str(ROOT/'tests/component_remote/producer-shapes-v1.json')]=io.sha(ROOT/'tests/component_remote/producer-shapes-v1.json');after[str(ROOT/'doc/component-remote-plan-v1.json')]=io.sha(ROOT/'doc/component-remote-plan-v1.json')
    if before!=after:raise RuntimeError('control/execution sources changed during controls')
    work=Path(tempfile.mkdtemp(prefix='unison-component-remote-controls-',dir='/private/tmp'))
    io.save(work/'RESULT.json',{'complete':result.wasSuccessful(),'tests':result.testsRun,
      'errors':len(result.errors),'failures':len(result.failures),'source_sha256':before,
      'canonical_locks_acquired':False,'transport_or_native_invoked':False,
      'scope':'original disposable/fabricated controls, not live RPC or canonical lease qualification'})
    print(work,flush=True);raise SystemExit(0 if result.wasSuccessful() else 1)
