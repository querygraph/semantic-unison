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
    PEER=None
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='vpa-',dir='/private/tmp');self.root=Path(self.temp.name)
        st=self.root.lstat();self.files=Files(self.root,(st.st_dev,st.st_ino));self.events=[];self.fault=None
        packet=dict(workspace=str(self.root),repository=str(Path(__file__).resolve().parents[2]),
            binary=dict(path='/original/current-unison',sha256='a'*64),interpreter=dict(path=PYTHON,sha256='b'*64),
            rows=[dict(directory=str(self.root/'case'),max_CLI_calls=69)],limits=dict(CLI_calls=69,per_CLI_observation_seconds=90))
        if self.PEER:packet['peer']=dict(compiler='ox',binary=dict(path=self.PEER,sha256='c'*64))
        self.envs=[]
        def pair_call(row,env,**kwargs):
            self.events.append('pair');self.envs.append(env)
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
            invoke=self.actor.invoke,audit=self.actor.audit,interrupt=lambda *args:None,persist=lambda *args:None,server_binary=self.PEER),
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

class ProducerActor(NormalActor):
    def setUp(self):
        super().setUp()
        import hashlib
        from current_validation_paths.files import epoch
        from current_validation_paths.producer_evidence_test import fixture as crash_fixture
        self.actor.rows[str(self.session.root)].update(family='resumed',arguments=['complete','pass'])
        self.session.interrupt_adapter=self.actor.interrupt;self.crash_fault=None
        normal_pair=self.actor.pair_call
        def interrupted_pair(row,env,**kwargs):
            intent=self.actor.active['intent']
            if 'producer_interruption' not in intent:return normal_pair(row,env,**kwargs)
            self.events.append('producer-pair')
            if self.crash_fault=='pair':raise UnresolvedOwnership('original inert producer transport',retained_fds=(999,))
            observer=intent['producer_interruption'];data=(self.session.left/'resumed.DNG').read_bytes()[:observer['staged_bytes']]
            candidate=self.session.right/'.resumed.stage.unison.tmp';candidate.write_bytes(data);st=candidate.lstat()
            record=dict(source=str(self.session.left/'resumed.DNG'),destination=str(candidate),pid=301,group=301,
                size=len(data),sha256=hashlib.sha256(data).hexdigest(),device=st.st_dev,inode=st.st_ino,
                interrupt=observer['kind'],nofile_hard=256)
            self.session.copy.with_suffix('.calls.jsonl').write_text(json.dumps(record)+'\n')
            self.session.copy.with_suffix('.release').write_bytes(b'fabricated source-controlled release')
            _,pair,_=crash_fixture();pair['client']['command']=row['command'];pair['proxy']['command']=kwargs['proxy_command']
            frame=pair['raw_proxy'];frame['server_command']=intent['server_command'];event=frame['transport']['event']
            event['stage'].update(record=record,stage_identity=list(epoch(st)),source_sha256=observer['source_sha256'],
                staged_sha256=observer['staged_sha256'],staged_bytes=len(data))
            event['release']['marker']=str(self.session.copy.with_suffix('.release'))
            pair['client']['stderr']=pair['client']['stderr'].replace('pid=201','pid=301')
            if self.crash_fault=='group':pair['client']['stderr']=pair['client']['stderr'].replace('other-members=0','other-members=unknown')
            raw=json.dumps(frame).encode();kwargs['persist'](row,pair,raw)
            if self.crash_fault=='post-stage':candidate.write_bytes(b'changed after captured crash')
            return pair,raw
        self.actor.pair_call=interrupted_pair
    def interrupt(self,kind='complete'):
        self.actor.rows[str(self.session.root)]['arguments'][0]=kind
        return self.session.interruption('resumed.DNG',bytes(range(256))*8192+b'synthetic resume tail\n',kind)
    def test_initial_complete_interruption_then_normal_call_share_global_sequence(self):
        record=self.interrupt();self.assertEqual(record['size'],len(bytes(range(256))*8192+b'synthetic resume tail\n'))
        self.assertEqual(self.actor.attempts,1);self.assertEqual(self.session.sequence,1)
        self.assertEqual(self.actor.calls[1]['verdict']['client_returncode'],3)
        self.session.sync();self.assertEqual(self.actor.attempts,2);self.assertEqual(self.session.sequence,2)
        self.assertEqual(self.events,['artifacts','producer-pair','artifacts','pair']);self.actor.close()
    def test_partial_interruption_keeps_exact_original_staging_inode(self):
        record=self.interrupt('partial');self.assertEqual(record['size'],len(bytes(range(256))*8192+b'synthetic resume tail\n')//2)
        self.assertEqual(self.session.root.__class__(record['destination']).lstat().st_ino,record['inode'])
    def test_producer_cannot_bypass_exhausted_global_budget(self):
        self.actor.packet['limits']['CLI_calls']=0
        with self.assertRaises(UnresolvedOwnership):self.interrupt()
        self.assertEqual(self.events,[]);self.assertEqual(self.actor.attempts,0)
    def test_unknown_transport_retains_same_inherited_resources(self):
        self.crash_fault='pair'
        with self.assertRaises(UnresolvedOwnership) as caught:self.interrupt()
        self.assertTrue({999,*range(700,709)}<=set(caught.exception.retained_fds))
        with self.assertRaises(UnresolvedOwnership):self.actor.close()
    def test_unknown_producer_group_refuses_independent_audit(self):
        self.crash_fault='group'
        with self.assertRaises(UnresolvedOwnership):self.interrupt()
        self.assertEqual(self.actor.calls,{})
    def test_stage_change_after_raw_capture_retains_even_after_raw_audit(self):
        self.crash_fault='post-stage'
        with self.assertRaises(UnresolvedOwnership):self.interrupt()
        self.assertEqual(len(self.actor.calls),1)
        with self.assertRaises(UnresolvedOwnership):self.actor.close()
    def test_nonresumed_case_refuses_interruption_before_process_adapter(self):
        self.actor.rows[str(self.session.root)]['family']='external'
        with self.assertRaises(UnresolvedOwnership):self.interrupt()
        self.assertEqual(self.events,[]);self.assertEqual(self.actor.attempts,0)


class PeeredActor(NormalActor):
    """The other compiler's pinned peer serves: the launcher must expect exactly that binary."""
    PEER='/original/peer-unison'
    def test_launcher_and_proxy_expect_the_peer_server(self):
        self.session.sync()
        self.assertEqual(self.envs[-1]['UNISON_MERGE_BINARY'],self.PEER)
        call=json.loads((self.root/'case/call-001-CONFIG.json').read_text())
        self.assertEqual(call['proxy']['binary'],self.PEER)
        intent=json.loads((self.root/'case/call-001-INTENT.json').read_text())['intent']
        self.assertEqual(intent['command'][intent['command'].index('-servercmd')+1],self.PEER)
        self.assertEqual(intent['command'][0],'/original/current-unison')

if __name__=='__main__':unittest.main()
