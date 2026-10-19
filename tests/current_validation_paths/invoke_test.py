"""Actual private JSON/script IO with inert pair/artifact adapters only."""
import json,os,shutil,tempfile,unittest
from pathlib import Path
from current_validation_paths.files import Files
from current_validation_paths.original import load
from current_validation_paths.session import factory
from current_validation_paths.invoke import Actor
from sdk_merge_receiving.evidence_test import fixture
from sdk_merge_receiving.admission import PYTHON
from shared_cpu_pool import UnresolvedOwnership
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()


class NormalActor(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='vpa-',dir='/private/tmp');self.root=Path(self.temp.name)
        st=self.root.lstat();self.files=Files(self.root,(st.st_dev,st.st_ino));self.events=[];self.fault=None
        packet=dict(workspace=str(self.root),repository=str(Path(__file__).resolve().parents[2]),
            binary=dict(path='/original/current-unison',sha256='a'*64),interpreter=dict(path=PYTHON,sha256='b'*64),
            rows=[dict(directory=str(self.root/'case'))],limits=dict(CLI_calls=69,per_CLI_observation_seconds=90))
        def pair_call(row,env,**kwargs):
            self.events.append('pair')
            if self.fault=='pair':raise UnresolvedOwnership('original inert child retained',retained_fds=(999,))
            _,pair=fixture('seed');pair['client']['command']=row['command'];pair['proxy']['command']=kwargs['proxy_command']
            pair['raw_proxy']['server_command']=self.actor.active['intent']['server_command']
            raw=json.dumps(pair['raw_proxy']).encode();kwargs['persist'](row,pair,raw)
            if self.fault=='tamper':
                active=self.actor.active;(self.root/'case'/active['pair_pin']['name']).write_bytes(b'corrupted original fixture record')
            return pair,raw
        resources=[dict(fd=700+i,device=1,inode=800+i) for i in range(9)]
        self.actor=Actor(packet,resources,__import__('time').monotonic()+30,pair_call=pair_call,artifact_check=lambda p:self.events.append('artifacts'))
        result=load(SOURCE,session_factory=lambda legacy:factory(legacy,files=self.files,binary=packet['binary']['path'],repository=packet['repository'],
            invoke=self.actor.invoke,audit=self.actor.audit,interrupt=lambda *args:None,persist=lambda *args:None),
            path_factory=lambda _:self.files.Path,cancel_actor=lambda *args:None,filename='/source-only/run.py')
        cls=result['functions']['resumed'].__globals__['Session'];self.session=cls(self.files.Path(self.root/'case'),packet['binary']['path'])
    def tearDown(self):
        # Inert failures never create an actual native child or uncertain close.
        # Close only these known real metadata FDs, not fake700..708/999.
        for store in self.actor.stores.values():
            if not store.closed:store.close()
        if not self.files.closed:
            if self.files.retained is None:self.files.close()
            else:os.close(self.files.fd);self.files.closed=True
        self.temp.cleanup()
    def test_normal_invoke_persists_raw_pair_then_reaudits_before_actor_close(self):
        self.session.sync();self.assertEqual(self.events,['artifacts','pair'])
        self.assertEqual(self.actor.attempts,1);self.assertEqual(len(self.actor.calls),1)
        self.assertTrue((self.root/'case/call-001-INTENT.json').exists());self.assertTrue((self.root/'case/call-001-PAIR.json').exists())
        self.assertTrue((self.root/'case/call-001-AUDIT.json').exists());self.assertIsNone(self.actor.active)
        self.actor.close();self.assertTrue(self.actor.closed)
    def test_failed_pair_keeps_every_inherited_copy_and_refuses_retry(self):
        self.fault='pair'
        with self.assertRaises(UnresolvedOwnership) as raised:self.session.sync()
        self.assertTrue({999,*range(700,709)}<=set(raised.exception.retained_fds))
        with self.assertRaises(UnresolvedOwnership):self.actor.close()
        with self.assertRaises(UnresolvedOwnership):self.session.sync()
        self.assertEqual(self.events,['artifacts','pair'])
    def test_tampered_durable_pair_is_not_a_settled_result(self):
        self.fault='tamper'
        with self.assertRaises(UnresolvedOwnership):self.session.sync()
        self.assertEqual(self.actor.calls,{})
        self.assertFalse((self.root/'case/call-001-AUDIT.json').exists())
    def test_changed_generated_script_refuses_before_process_adapter(self):
        self.session.copy.write_text('modified original fixture script')
        with self.assertRaises(UnresolvedOwnership):self.session.sync()
        self.assertEqual(self.events,['artifacts'])
    def test_declared_call_budget_stops_before_second_dispatch(self):
        self.actor.packet['limits']['CLI_calls']=1;self.session.sync()
        with self.assertRaises(UnresolvedOwnership):self.session.sync()
        self.assertEqual(self.events,['artifacts','pair']);self.assertIsNone(self.session.last_outcome)

class CancellationActor(NormalActor):
    # Reuse real tiny owned files, but every process/signal remains fabricated.
    def setUp(self):
        super().setUp()
        import hashlib
        from current_validation_paths.evidence_test import expected,lines
        self.previous=b'original old receiving bytes';self.incoming=b'N'*4096;self.sha=hashlib.sha256(self.incoming).hexdigest()
        self.name='cancelled.dng';(self.session.left/self.name).write_bytes(self.previous);(self.session.right/self.name).write_bytes(self.incoming)
        self.session.control(self.name,client='hang');self.cancel_fault=None
        def cancel_call(row,env,**kwargs):
            self.events.append('cancel-pair')
            candidate=self.session.left/'private-cancellation-stage';candidate.write_bytes(self.incoming);st=candidate.lstat()
            record=dict(endpoint='client',mode='hang',pid=321,candidate=str(candidate),destination=str(self.session.left/self.name),
                sha256=self.sha,size=4096,destination_sha256=hashlib.sha256(self.previous).hexdigest(),device=st.st_dev,inode=st.st_ino,
                argv=['--unison-dng-validation-v1','--expected-sha256',self.sha,'--expected-size','4096','--threads','1','--',str(candidate)])
            self.session.drivers['client'].with_suffix('.calls.jsonl').write_text(json.dumps(record)+'\n')
            from types import SimpleNamespace
            observed=kwargs['before_interrupt'](SimpleNamespace(owner=SimpleNamespace(pid=101,reaped=False,terminal=lambda:False)),__import__('time').monotonic()+1)
            _,pair=fixture('seed');pair['client']['command']=row['command'];pair['proxy']['command']=kwargs['proxy_command']
            pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=3
            entry=expected('hang',endpoint='client');entry['outcome']='cancelled'
            pair['client']['stderr']=lines(entry).replace('a'*64,self.sha)+'[semantic] 1 jobs per filesystem\nUpdate propagation interrupted\nAborted by user request\n'
            pair['raw_proxy']['server_command']=self.actor.active['intent']['server_command']
            raw=json.dumps(pair['raw_proxy']).encode();kwargs['persist'](row,pair,raw)
            sent=dict(pid=101,signal=2,sent=True,client_reaped_before_signal=False,resource_release_authorized=False)
            if self.cancel_fault=='signal':sent['pid']=102
            if self.cancel_fault=='persist':raise UnresolvedOwnership('original inert cancellation persistence failure',retained_fds=(999,))
            return pair,raw,dict(fixture_observation=observed,client_interrupt=sent)
        self.actor.cancellation_call=cancel_call
    # Inherited normal-call controls deliberately remain valid with this setup.
    def test_cancel_uses_same_global_budget_and_durable_independent_audit(self):
        log=self.session.cancel(self.name,self.incoming,self.previous,policy='require')
        self.assertIn('Aborted by user request',log);self.assertEqual(self.actor.attempts,1)
        self.assertEqual(self.actor.calls[1]['verdict']['client_returncode'],3)
        self.assertEqual(self.actor.calls[1]['pair_pin']['name'],'call-001-PAIR.json')
        self.assertEqual(self.actor.calls[1]['cancellation_pin']['name'],'call-001-CANCELLATION.json')
        self.assertTrue((self.root/'case/call-001-CANCELLATION.json').exists())
        self.assertIsNone(self.session.cancel_fixture)
        self.session.control(self.name);self.session.sync();self.assertEqual(self.actor.attempts,2)
        self.assertEqual(self.events,['artifacts','cancel-pair','artifacts','pair']);self.actor.close()
    def test_invalid_cancellation_fixture_refuses_before_any_process_adapter(self):
        with self.assertRaises(UnresolvedOwnership):self.session.cancel('../escape',self.incoming,self.previous,policy='warn')
        self.assertEqual(self.events,[]);self.assertEqual(self.actor.attempts,0)
    def test_nonhang_control_refuses_before_cancellation_process_adapter(self):
        self.session.control(self.name)
        with self.assertRaises(UnresolvedOwnership):self.session.cancel(self.name,self.incoming,self.previous,policy='require')
        self.assertEqual(self.events,['artifacts']);self.assertEqual(self.actor.calls,{})
    def test_cancel_cannot_bypass_exhausted_global_call_budget(self):
        self.actor.packet['limits']['CLI_calls']=0
        with self.assertRaises(UnresolvedOwnership):self.session.cancel(self.name,self.incoming,self.previous,policy='require')
        self.assertEqual(self.events,[]);self.assertEqual(self.actor.attempts,0)
    def test_wrong_actual_signal_binding_retains_every_owner(self):
        self.cancel_fault='signal'
        with self.assertRaises(UnresolvedOwnership):self.session.cancel(self.name,self.incoming,self.previous,policy='warn')
        self.assertEqual(self.actor.calls,{})
        with self.assertRaises(UnresolvedOwnership):self.actor.close()
    def test_cancellation_persistence_uncertainty_not_normal_failed_prefix(self):
        self.cancel_fault='persist'
        with self.assertRaises(UnresolvedOwnership) as caught:self.session.cancel(self.name,self.incoming,self.previous,policy='require')
        self.assertIn(999,caught.exception.retained_fds);self.assertEqual(self.actor.calls,{})
        self.assertIsNone(self.session.last_outcome)

if __name__=='__main__':unittest.main()
