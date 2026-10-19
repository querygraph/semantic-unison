"""Independent raw replay over fabricated captures/pins only; zero IO/children."""
import copy,hashlib,json,unittest
from pathlib import Path
from current_validation_paths.contract import plan
from current_validation_paths import recipes,parent
from current_validation_paths.producer_evidence_test import fixture as crash_fixture
from current_validation_paths.producer_evidence import audit as audit_crash
from sdk_merge_receiving.admission import PYTHON
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()


def encode(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

class Replay(unittest.TestCase):
    def setUp(self):
        self.packet=plan(SOURCE,'/private/tmp/u-vpath-0123456789abcdef','stock')
        self.packet.update(repository='/source-only/current-repository',binary=dict(path='/inert/current-unison',sha256='a'*64))
        row=self.packet['rows'][0];self.root=row['directory'];self.records={};self.root_records={}
        self.scripts=recipes.scripts(recipes.literal_templates(SOURCE),self.packet['repository'])
        self.resources=[dict(fd=700+i,device=1,inode=900+i) for i in range(9)]
        device,inode=getattr(self,'case_identity',(1,2))
        self.phase=recipes.phase(row,1,self.scripts,self.packet['binary']['path']);self.identity=dict(device=device,inode=inode)
        observer=recipes.producer_observer(row,(device,inode))
        self.intent=dict(sequence=1,case_root=self.root,**self.phase,before_fake_helper_counts=dict(client=0,server=0),
            before_external_counts=dict(copy=0,merge=0),producer_interruption=observer,resource_release_authorized=False)
        self.config=dict(directory=self.root,identity=self.identity,stage='call-001',binary=self.packet['binary']['path'],
            flags=self.phase['server_command'][3:],deadline=900.,worker_pid=500,resource_fds=self.resources,producer_observer=observer)
        _,self.pair,_=crash_fixture();self.proxy=[PYTHON,'-B',self.root+'/call-001-proxy.py']
        self.pair['client']['command']=self.phase['command'];self.pair['proxy']['command']=self.proxy
        frame=self.pair['raw_proxy'];frame['server_command']=self.phase['server_command']
        record=frame['transport']['event']['stage']['record'];record.update(source=self.root+'/left/resumed.DNG',
            destination=self.root+'/right/.resumed.stage.unison.tmp',pid=301,group=301,size=observer['staged_bytes'],sha256=observer['staged_sha256'])
        self.record=record;self.pair['client']['stderr']=self.pair['client']['stderr'].replace('pid=201','pid=301')
        frame['transport']['event']['stage'].update(source_sha256=observer['source_sha256'],staged_sha256=observer['staged_sha256'],
            staged_bytes=observer['staged_bytes'],stage_identity=[1,2,33152,observer['staged_bytes'],1,1,1,501])
        frame['transport']['event']['release']['marker']=self.root+'/external-copy.release'
        self.verdict=audit_crash(self.pair,client_command=self.phase['command'],proxy_command=self.proxy,
            server_command=self.phase['server_command'],raw_proxy_bytes=json.dumps(frame).encode(),observer=observer)
        self.item=dict(root=self.root)
        self.save('intent_pin','call-001-INTENT.json',dict(intent=self.intent,global_call=1,resource_release_authorized=False))
        self.save_config();self.save_pair();self.save('audit_pin','call-001-AUDIT.json',self.verdict)
        self.records[self.root,'call-001-INHERITED.json']=encode(dict(proxy_pid=102,worker_pid=500,resource_fds=self.resources,
            binding=dict(inherited_fds=[r['fd'] for r in self.resources],canonical_metadata_bound=True,lock_ownership_independently_proved=False,resource_release_authorized=False)))
        self.failure=dict(index=0,family=row['family'],name=row['name'],error='original inert settled-prefix assertion',ordinary_case_failure_only=True,
            worker_local_settled_candidate=True,independent_parent_raw_audit_required=True,resource_release_authorized=False)
        self.result=dict(complete=False,cases=[],failed_case=self.failure,calls={'1':self.item},attempted_CLI_calls=1,
            actual_SDK_calls=0,actual_Photo_calls=0,parent_terminal_proved=False,resource_release_authorized=False,independent_parent_raw_audit_required=True)
        self.root_records['case-00-seq-001-INTENT.json']=copy.deepcopy(self.intent)
        self.root_records['case-00-seq-001-ACCEPTED.json']=dict(intent=copy.deepcopy(self.intent),verdict=self.verdict,resource_release_authorized=False)
        self.root_records['case-00-FAILED.json']=self.failure
        self.root_records['case-00-START.json']=dict(row=row,resource_release_authorized=False)
        self.state=dict(identity=self.identity,counters=dict(client=[],server=[],copy=[record],merge=[]),scripts_current=True,profile_current=True)
    def save(self,key,name,value):
        raw=encode(value);self.records[self.root,name]=raw;self.item[key]=dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    def save_pair(self):
        self.save('pair_pin','call-001-PAIR.json',dict(pair=self.pair,raw_proxy_hex=json.dumps(self.pair['raw_proxy']).encode().hex(),resource_release_authorized=False))
    def save_config(self):
        self.save('config_pin','call-001-CONFIG.json',dict(proxy=self.config,script_sha256=hashlib.sha256(recipes.proxy_source(self.packet['repository'],self.config).encode()).hexdigest(),resource_release_authorized=False))
    def replay(self):
        def state(root,scripts,profile,proxies):
            self.assertEqual(root,self.root);self.assertEqual(scripts,self.scripts);self.assertEqual(profile,self.phase['server_profile_text'])
            self.assertEqual(proxies,{'call-001-proxy.py':recipes.proxy_source(self.packet['repository'],self.config)})
            return self.state
        return parent.replay(self.packet,self.result,source=SOURCE,worker_pid=500,resources=self.resources,owner_deadline=1000.,
            read_case=lambda root,name:self.records[root,name],read_root=lambda name:self.root_records[name],case_state=state)
    def test_failed_original_prefix_can_be_replayed_without_benchmark_pass_or_release(self):
        value=self.replay();self.assertFalse(value['complete']);self.assertEqual(value['raw_pairs_reparsed'],1)
        self.assertEqual(value['producer_interruptions'],1);self.assertEqual(value['copy'],1)
        self.assertTrue(value['external_children_settled']);self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['parent_terminal_proved'])
    def test_changed_raw_pin_refuses_even_if_worker_claims_settled(self):
        self.records[self.root,'call-001-PAIR.json']+=b' '
        with self.assertRaises(ValueError):self.replay()
    def test_changed_actual_client_command_rejected_after_repin(self):
        self.pair['client']['command']=['/wrong/client'];self.save_pair()
        with self.assertRaises(ValueError):self.replay()
    def test_changed_inherited_resource_inode_refuses_after_repin(self):
        self.config['resource_fds']=copy.deepcopy(self.resources);self.config['resource_fds'][0]['inode']=99999;self.save_config()
        with self.assertRaises(ValueError):self.replay()
    def test_unknown_group_is_not_safe_failed_prefix(self):
        self.pair['client']['stderr']=self.pair['client']['stderr'].replace('other-members=0','other-members=unknown');self.save_pair()
        with self.assertRaises(ValueError):self.replay()
    def test_extra_or_missing_final_counter_cannot_disappear(self):
        self.state['counters']['copy']=[]
        with self.assertRaises(ValueError):self.replay()
    def test_worker_phase_cannot_raise_endpoint_budget_after_repin(self):
        command=self.intent['command'];command[command.index('-semanticcpubudget')+1]='18'
        self.save('intent_pin','call-001-INTENT.json',dict(intent=self.intent,global_call=1,resource_release_authorized=False))
        with self.assertRaises(ValueError):self.replay()
    def test_false_script_or_profile_freshness_refuses(self):
        self.state['scripts_current']=False
        with self.assertRaises(ValueError):self.replay()
    def test_missing_actual_proxy_inherited_record_is_not_terminal_proof(self):
        record=json.loads(self.records[self.root,'call-001-INHERITED.json']);record['worker_pid']=999
        self.records[self.root,'call-001-INHERITED.json']=encode(record)
        with self.assertRaises(ValueError):self.replay()
    def test_noncontiguous_call_inventory_cannot_be_ignored(self):
        self.result['calls']['3']=self.result['calls'].pop('1')
        with self.assertRaises(ValueError):self.replay()
    def test_missing_case_start_or_root_acceptance_refuses(self):
        self.root_records['case-00-START.json']={}
        with self.assertRaises(ValueError):self.replay()

if __name__=='__main__':unittest.main()
