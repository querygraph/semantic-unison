"""Complete 21-case parent replay over fabricated captures only; zero IO/children.

Per-call helper/copy/merge shapes follow the original case bodies: interrupted
resume, rejected-then-retried external/reuse/merge, timeout, cancellation and
six serialized directory helpers, each ending in its original no-op call.
"""
import copy,hashlib,json,unittest
from pathlib import PurePosixPath as Path
from current_validation_paths.contract import plan
from current_validation_paths import recipes,parent
from current_validation_paths.evidence import audit as audit_normal
from current_validation_paths.cancel_evidence import audit as audit_cancel
from current_validation_paths.producer_evidence import audit as audit_producer
from current_validation_paths.runtime import case_summary
from current_validation_paths.parent_test import SOURCE,encode
from sdk_merge_receiving.admission import PYTHON
RESOURCES=[dict(fd=700+i,device=1,inode=900+i) for i in range(9)]


def shape(row,sequence):
    """(client helpers, server helpers, copies, merges) of one original call."""
    family=row['family'];args=row['arguments'];last=sequence==row['max_CLI_calls']
    if last and family!='directory_admission':return 0,0,0,0
    if family=='resumed':return (0,0,1,0) if sequence==1 else (0,1,0,0)
    if family=='external':return (0,0 if args[1]=='off' else 1,1,0) if sequence==1 else (0,1,0,0)
    if family=='moved':return 0,1,0,0
    if family=='merged':
        if sequence==1:return 0,1,0,0
        if sequence==2:return 1,1 if args[0]=='pass' else 0,0,1
        return 1,1,0,1
    if family in ('timed_out','cancelled'):return (1,0,0,0) if family=='cancelled' and sequence in (2,3) else (0,1,0,0)
    return (0,6,0,0) if sequence==1 else (0,0,0,0)


def receipt(endpoint,mode,sha,size):
    if mode=='hang':return b''
    return ('UNISON-DNG-VALIDATION 1\ncandidate-sha256 '+('0'*64 if mode=='wrong-receipt' else sha)+'\ncandidate-size '+str(size)+
        '\ndriver-build validation-path-'+endpoint+'-v1\nstructure valid\ndecode success\nraw-digest missing\nerrors '+
        ('1' if mode=='error' else '0')+'\nwarnings 0\nEND\n').encode()


def helper_lines(value,outcome):
    prefix='server: ' if value['endpoint']=='server' else '';hang=value['mode']=='hang'
    return ('['+prefix+'validation-process] Helper result v0 pid='+str(value['pid'])+' status='+('signal:15' if hang else 'exit:0')+
        ' outcome='+outcome+' candidate-sha256='+value['sha256']+' candidate-bytes='+str(value['size'])+
        ' capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex='+receipt(value['endpoint'],value['mode'],value['sha256'],value['size']).hex()+
        ' stderr-hex=\n['+prefix+'validation-group] Retained group v0 pid='+str(value['pid'])+' candidate-sha256='+value['sha256']+' other-members=0\n')


def external_line(pid):
    return '[external-process] External result v0 pid='+str(pid)+' status=exit:0 outcome=completed cpu-weight=1 other-members=0 capture-truncated=false\n'


def child(command,code,pid,stderr):
    return dict(command=command,returncode=code,timed_out=False,capture_truncated=False,stdout='',stderr=stderr,
        client_cleanup=dict(pid=pid,returncode=code,reaped=True,hard_kill_required=False,
            other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True),
        aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False)


class Run:
    """Fabricated worker output for the first `cases` rows, optionally ending in a failure."""
    def __init__(self,cases=21,failed_calls=None):
        self.packet=plan(SOURCE,'/private/tmp/u-vpath-0123456789abcdef','stock')
        self.packet.update(repository='/source-only/current-repository',binary=dict(path='/inert/current-unison',sha256='a'*64))
        self.scripts=recipes.scripts(recipes.literal_templates(SOURCE),self.packet['repository'])
        self.records={};self.root_records={};self.states={};self.calls={};self.summaries=[];number=0
        for row in self.packet['rows'][:cases+(failed_calls is not None)]:
            root=row['directory'];identity=dict(device=1,inode=100+row['index']);verdicts=[]
            streams=dict(client=[],server=[],copy=[],merge=[])
            self.root_records['case-%02d-START.json'%row['index']]=dict(row=row,resource_release_authorized=False)
            count=row['max_CLI_calls'] if row['index']<cases else failed_calls
            for sequence in range(1,count+1):
                number+=1;verdicts.append(dict(root=root,verdict=self.call(row,sequence,number,identity,streams)))
            self.states[root]=dict(identity=identity,counters=streams,scripts_current=True,profile_current=True)
            if row['index']<cases:
                summary=case_summary(row,verdicts,dict(case=row['name'],original_assertions='passed'))
                self.summaries.append(summary);self.root_records['case-%02d-RESULT.json'%row['index']]=summary
        failure=None
        if failed_calls is not None:
            row=self.packet['rows'][cases]
            failure=dict(index=cases,family=row['family'],name=row['name'],error='original fabricated case assertion',
                ordinary_case_failure_only=True,worker_local_settled_candidate=True,independent_parent_raw_audit_required=True,resource_release_authorized=False)
            self.root_records['case-%02d-FAILED.json'%cases]=failure
        self.result=dict(complete=failure is None,cases=self.summaries,failed_case=failure,calls=self.calls,attempted_CLI_calls=number,
            actual_SDK_calls=0,actual_Photo_calls=0,parent_terminal_proved=False,resource_release_authorized=False,independent_parent_raw_audit_required=True)
    def save(self,root,item,key,name,value):
        raw=encode(value);self.records[root,name]=raw;item[key]=dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    def call(self,row,sequence,number,identity,streams):
        root=row['directory'];stem='call-%03d'%number;base=10000+20*number
        phase=recipes.phase(row,sequence,self.scripts,self.packet['binary']['path'])
        kind='producer_interruption' if row['family']=='resumed' and sequence==1 else 'cancellation' if row['family']=='cancelled' and sequence==2 else None
        intent=dict(sequence=sequence,case_root=root,**phase,before_fake_helper_counts=dict(client=len(streams['client']),server=len(streams['server'])),
            before_external_counts=dict(copy=len(streams['copy']),merge=len(streams['merge'])),resource_release_authorized=False)
        if kind=='producer_interruption':intent[kind]=recipes.producer_observer(row,(identity['device'],identity['inode']))
        if kind=='cancellation':intent[kind]=recipes.cancellation_fixture()
        config=dict(directory=root,identity=identity,stage=stem,binary=self.packet['binary']['path'],flags=phase['server_command'][3:],
            deadline=900.,worker_pid=500,resource_fds=RESOURCES)
        if kind=='producer_interruption':config['producer_observer']=intent[kind]
        proxy=[PYTHON,'-B',root+'/'+stem+'-proxy.py'];client_pid,proxy_pid,server_pid=base+1,base+2,base+3
        clients,servers,copies,merges=shape(row,sequence);logs=dict(client='',server='');values=[]
        for k,endpoint in enumerate(['client']*clients+['server']*servers):
            control=intent['helper_controls'][endpoint];side=Path(root)/('left' if endpoint=='client' else 'right')
            if control.get('directory'):
                destination=Path(control['destination'])/('item-%d.dng'%k);candidate=side/'.unison-stage'/destination.name
            else:destination=Path(control['destination']);candidate=side/('.'+destination.name+'.%03d.unison.tmp'%number)
            sha=hashlib.sha256((stem+endpoint+str(k)).encode()).hexdigest();size=4096+k;previous=None
            if kind=='cancellation':
                fixture=intent[kind];sha,size,previous=fixture['incoming_sha256'],fixture['incoming_bytes'],fixture['previous_sha256']
            value=dict(candidate=str(candidate),destination=str(destination),sha256=sha,size=size,device=1,inode=base+50+k,
                argv=['--unison-dng-validation-v1','--expected-sha256',sha,'--expected-size',str(size),'--threads','1','--',str(candidate)],
                pid=base+4+k,destination_sha256=previous,mode=control['mode'],endpoint=endpoint,nofile_hard=256)
            outcome=('cancelled' if kind else 'timed-out') if value['mode']=='hang' else 'completed'
            streams[endpoint].append(value);values.append(value);logs[endpoint]+=helper_lines(value,outcome)
        if kind=='producer_interruption':
            observer=intent[kind]
            record=dict(source=root+'/left/resumed.DNG',destination=root+'/right/.resumed.DNG.stage.unison.tmp',pid=base+15,group=base+15,
                size=observer['staged_bytes'],sha256=observer['staged_sha256'],device=1,inode=base+60,interrupt=observer['kind'],nofile_hard=256)
            streams['copy'].append(record)
            stage=dict(record=record,stage_identity=[1,base+60,33152,observer['staged_bytes'],1,1,1,501],source_sha256=observer['source_sha256'],
                staged_sha256=observer['staged_sha256'],staged_bytes=observer['staged_bytes'],old_destination_absent=True,
                validator_calls_before_copy_return=0,resource_release_authorized=False)
            raw=dict(schema='unison-generated-producer-interruption/1',server_command=phase['server_command'],server_pid=server_pid,
                server_returncode=-9,server_reaped=True,server_group=proxy_pid,resource_release_authorized=False,
                transport=dict(event=dict(stage=stage,signal=dict(pid=server_pid,signal=9,owned_unreaped_before_signal=True,group=proxy_pid,
                    reason='observed generated external-copy stage; owned receiver interruption'),
                    release=dict(marker=root+'/external-copy.release',copy_fixture_released=True,producer_signalled=False,resource_release_authorized=False)),
                    counts=dict(client_to_server_bytes=5,server_to_client_bytes=7,discarded_client_bytes=3),client_eof_observed=True,
                    server_eof_observed=True,input_eof_forwarded=False,discard_permitted_only_after_owned_signal=True))
            logs['client']+='Lost connection with the server\n'+external_line(base+15);code=3
        else:
            for kind_name,count in (('copy',copies),('merge',merges)):
                for _ in range(count):
                    pid=base+15+len(streams['copy'])+len(streams['merge'])
                    record=dict(pid=pid,group=pid,nofile_hard=256)
                    record.update(dict(source=root+'/left/external.dng',destination=root+'/right/.external.dng.stage.unison.tmp',size=3712,
                        sha256='c'*64,device=1,inode=base+70,interrupt='no') if kind_name=='copy' else
                        dict(inputs=['d'*64,'e'*64],result='f'*64,output=root+'/merge-output-%03d'%number))
                    streams[kind_name].append(record);logs['client']+=external_line(pid)
            raw=dict(schema='unison-retained-merge-proxy/1',server_command=phase['server_command'],server_pid=server_pid,server_returncode=0,
                server_reaped=True,server_group=proxy_pid,input_eof_forwarded=True,output_eof_forwarded=True,
                forwarded_protocol_bytes=dict(client_to_server_bytes=7,server_to_client_bytes=9),parent_group_audit_required=True,
                sdk_helper_audit_required=True,resource_release_authorized=False)
            code=phase['expected_client_exit']
            if kind=='cancellation':logs['client']+='Update propagation interrupted\nAborted by user request\n'
        pair=dict(client=child(phase['command'],code,client_pid,logs['client']),proxy=child(proxy,0,proxy_pid,logs['server']),
            raw_proxy=raw,external_sdk_audit_required=True,resource_release_authorized=False)
        arguments=dict(client_command=phase['command'],proxy_command=proxy,server_command=phase['server_command'],raw_proxy_bytes=json.dumps(raw).encode())
        item=dict(root=root)
        if kind=='producer_interruption':verdict=audit_producer(pair,**arguments,observer=intent[kind])
        elif kind=='cancellation':
            cancellation=dict(fixture_observation=dict(helper=values[0],client_pid=client_pid,candidate_bytes_verified=True,
                previous_destination_preserved=True,source_preserved=True,helper_settlement_proved=False,resource_release_authorized=False),
                client_interrupt=dict(pid=client_pid,signal=2,sent=True,client_reaped_before_signal=False,resource_release_authorized=False))
            expected=[dict(endpoint='client',pid=values[0]['pid'],candidate_sha256=values[0]['sha256'],candidate_bytes=values[0]['size'],mode='hang',outcome='cancelled')]
            verdict=audit_cancel(pair,**arguments,cancellation=cancellation,expected_helpers=expected)
            self.save(root,item,'cancellation_pin',stem+'-CANCELLATION.json',cancellation)
        else:
            expected=[dict(endpoint=v['endpoint'],pid=v['pid'],candidate_sha256=v['sha256'],candidate_bytes=v['size'],mode=v['mode'],
                outcome='timed-out' if v['mode']=='hang' else 'completed') for v in values]
            external=[dict(endpoint='client',pid=r['group'],fixture_pid=r['pid'],kind=k) for k in ('copy','merge')
                for r in streams[k][intent['before_external_counts'][k]:]]
            verdict=audit_normal(pair,**arguments,expected_client_exit=code,expected_helpers=expected,expected_external=external)
        verdict=json.loads(json.dumps(verdict))
        self.save(root,item,'intent_pin',stem+'-INTENT.json',dict(intent=intent,global_call=number,resource_release_authorized=False))
        self.save(root,item,'config_pin',stem+'-CONFIG.json',dict(proxy=config,script_sha256=hashlib.sha256(
            recipes.proxy_source(self.packet['repository'],config).encode()).hexdigest(),resource_release_authorized=False))
        self.save(root,item,'pair_pin',stem+'-PAIR.json',dict(pair=pair,raw_proxy_hex=json.dumps(raw).encode().hex(),resource_release_authorized=False))
        self.save(root,item,'audit_pin',stem+'-AUDIT.json',verdict)
        self.records[root,stem+'-INHERITED.json']=encode(dict(proxy_pid=proxy_pid,worker_pid=500,resource_fds=RESOURCES,
            binding=dict(inherited_fds=[r['fd'] for r in RESOURCES],canonical_metadata_bound=True,lock_ownership_independently_proved=False,resource_release_authorized=False)))
        prefix='case-%02d-seq-%03d-'%(row['index'],sequence)
        self.root_records[prefix+'INTENT.json']=copy.deepcopy(intent)
        self.root_records[prefix+'ACCEPTED.json']=dict(intent=copy.deepcopy(intent),verdict=verdict,resource_release_authorized=False)
        self.calls[str(number)]=item
        return verdict
    def replay(self):
        def state(root,scripts,profile,proxies):
            assert scripts==self.scripts and profile==self.root_records[max(k for k in self.root_records
                if k.startswith('case-%02d-seq-'%next(r['index'] for r in self.packet['rows'] if r['directory']==root)) and k.endswith('INTENT.json'))]['server_profile_text']
            return copy.deepcopy(self.states[root])
        return parent.replay(self.packet,self.result,source=SOURCE,worker_pid=500,resources=RESOURCES,owner_deadline=1000.,
            read_case=lambda root,name:self.records[root,name],read_root=lambda name:copy.deepcopy(self.root_records[name]),case_state=state)


class Complete(unittest.TestCase):
    def test_complete_original_inventory_replays_without_release(self):
        value=Run().replay()
        self.assertEqual({k:value[k] for k in ('cli_calls','fake_validators','copy','merge','producer_interruptions','client_cancellations')},
            dict(cli_calls=69,fake_validators=54,copy=9,merge=7,producer_interruptions=4,client_cancellations=2))
        self.assertTrue(value['complete']);self.assertEqual(value['original_completed_cases'],21);self.assertEqual(value['raw_pairs_reparsed'],69)
        self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['parent_terminal_proved'])
    def test_failed_prefix_inside_merge_case_replays_only_attempted_calls(self):
        run=Run(cases=13,failed_calls=2);value=run.replay()
        self.assertFalse(value['complete']);self.assertEqual(value['original_completed_cases'],13);self.assertEqual(value['raw_pairs_reparsed'],run.result['attempted_CLI_calls'])
    def test_complete_claim_with_truncated_inventory_refuses(self):
        run=Run(cases=20);run.result['complete']=True
        with self.assertRaisesRegex(ValueError,'full original case inventory'):run.replay()
    def test_dropped_middle_call_refuses(self):
        run=Run();calls=run.result['calls'];run.result['calls']={str(i):calls[str(i if i<30 else i+1)] for i in range(1,69)};run.result['attempted_CLI_calls']=68
        with self.assertRaisesRegex(ValueError,'named record pin'):run.replay()
    def test_swapped_calls_across_cases_refuse(self):
        run=Run();calls=run.result['calls'];calls['5'],calls['20']=calls['20'],calls['5']
        with self.assertRaisesRegex(ValueError,'skipped or replayed'):run.replay()
    def test_helper_record_moved_to_neighbouring_call_refuses(self):
        run=Run();server=run.states[run.packet['rows'][14]['directory']]['counters']['server']
        self.assertEqual([v['mode'] for v in server],['pass','error','pass']);server[1],server[2]=server[2],server[1]
        with self.assertRaisesRegex(ValueError,'escaped exact source control'):run.replay()
    def test_missing_final_merge_counter_refuses(self):
        run=Run();run.states[run.packet['rows'][15]['directory']]['counters']['merge'].pop()
        with self.assertRaisesRegex(ValueError,'monotone exact counter prefix'):run.replay()
    def test_case_summary_cannot_relabel_original_result_or_counts(self):
        for key,value in (('original_result',dict(case='other')),('fake_validators',4)):
            run=Run();run.summaries[12]=dict(run.summaries[12],**{key:value})
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'original case summary'):run.replay()
    def test_seventieth_call_or_unaccepted_case_record_refuses(self):
        run=Run();run.result['calls']['70']=run.result['calls']['69'];run.result['attempted_CLI_calls']=70
        with self.assertRaisesRegex(ValueError,'contiguous call'):run.replay()
        run=Run();del run.root_records['case-20-seq-002-ACCEPTED.json']
        with self.assertRaises(KeyError):run.replay()

if __name__=='__main__':unittest.main()
