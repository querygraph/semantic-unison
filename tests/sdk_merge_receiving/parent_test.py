"""Fabricated complete source/SDK/process evidence; no execution or payload IO."""
import copy
import hashlib
import json
import os
import unittest
from sdk_merge_receiving import parent
from sdk_merge_receiving.admission import worker_command
from sdk_merge_receiving.admission_test import fixture as packet_fixture
from sdk_merge_receiving.plan import schedule
from sdk_merge_receiving.evidence import bind
from sdk_merge_receiving.evidence_test import fixture as pair_fixture
from sdk_merge_receiving.helpers import audit as helpers
from sdk_merge_receiving.helpers_test import frame
from sdk_merge_receiving.ledger import Ledger
from sdk_merge_receiving.runtime import proxy_command

class Memory:
    def __init__(self):self.files={}
    def put(self,name,value):
        raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode();self.files[name]=raw
        return dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    def read(self,name,*,expected_sha256=None):
        raw=self.files[name]
        if expected_sha256 is not None and hashlib.sha256(raw).hexdigest()!=expected_sha256:
            raise ValueError('inert record hash differs')
        return raw
    def read_json(self,name,*,expected_sha256=None):return json.loads(self.read(name,expected_sha256=expected_sha256))


def fixture():
    packet,_,_,plan,_=packet_fixture();store=Memory();ledger=Ledger();results=[];events=[];pairs={};preps={}
    history=[];scripts={};programs={};inherited={};last={}
    command=worker_command(packet,plan)
    resources=[dict(fd=700+i,device=1,inode=900+i) for i in range(9)]
    binding=dict(inherited_fds=[r['fd'] for r in resources],canonical_metadata_bound=True,
                 lock_ownership_independently_proved=False,resource_release_authorized=False)
    store.put('ADMISSION-BOUND.json',dict(command=command,admission_nonce='a'*32))
    store.put('OWNER-START.json',dict(owner_pid=os.getpid(),child_pid=22,command=command,
        admission_nonce='a'*32,owner_observation_deadline=1000,target='current-sdk-merge',
        cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',inherited_resource_fds=resources))
    store.put('WORKER-BINDING.json',dict(schema='unison-current-merge-worker-binding/1',parent_pid=os.getpid(),
        worker_pid=22,resource_fds=resources,binding=binding))
    def snapshot():return dict(ledger=ledger.report(),results=copy.deepcopy(results),resource_release_authorized=False)
    def event():events.append(store.put('EVENT-%02d.json'%len(events),dict(schema='unison-merge-worker-event/1',
        snapshot=snapshot(),pair_pins=copy.deepcopy(pairs),resource_release_authorized=False)))
    event()
    for index,row in enumerate(schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']):
        codec,stage=row['codec'],row['stage'];key=codec+'-'+stage
        case=next(c for c in packet['cases'] if c['codec']==codec)
        candidate={k:case['states']['base' if stage=='seed' else 'target'][k] for k in ('sha256','bytes')}
        _,pair=pair_fixture(stage);pair['client']['command']=row['command']
        pair['proxy']['command']=proxy_command(packet,row)
        pair['client']['client_cleanup']['pid']=1000+index*3
        pair['proxy']['client_cleanup']['pid']=1001+index*3
        pair['raw_proxy'].update(server_command=row['server_command'],server_group=1001+index*3,server_pid=1002+index*3)
        if stage=='update':
            pair['client']['stdout']=frame('client',pid=2000+index*2,digest=candidate['sha256'])
            pair['proxy']['stdout']=frame('server',pid=2001+index*2,digest=candidate['sha256'])
        raw=json.dumps(pair['raw_proxy']).encode()
        call=bind(row,pair,expected_proxy_command=proxy_command(packet,row),raw_proxy_bytes=raw)
        check=helpers(call['log'],stage=stage,returncode=0,candidate_sha256=candidate['sha256'],candidate_bytes=256)
        command_sha=hashlib.sha256(json.dumps(row['command'],ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
        ledger.begin(codec,stage,command_sha);event()
        pairs[key+'-PAIR.json']=store.put(key+'-PAIR.json',dict(schema='unison-merge-pair-evidence/1',
            identity=row['identity'],command=row['command'],pair=pair,raw_proxy_hex=raw.hex()))
        clones=[]
        for side in (('left',) if stage=='seed' else ('left','right') if stage=='update' else ()):
            ref=case['states']['base' if stage=='seed' else side];source=packet['source_observations'][ref['path']]
            identity=dict(source,st_ino=8000+index*10+len(clones),st_mode=0o100600)
            clones.append(dict(source=ref['path'],source_identity=source,clone_identity=identity,
                clone_sha256=ref['sha256'],clone_hash_bytes=256,source_payload_hash_bytes=0,backend='native-fclonefileat-only'))
        prepared=dict(codec=codec,stage=stage,event='PREPARED',candidate=candidate,clones=clones)
        if stage!='noop':
            last[codec]={side:dict(sha256=candidate['sha256'],bytes=256,identity=dict(
                packet['source_observations'][case['states']['base']['path']],st_mode=0o100600,
                st_ino=9000+index*10+n)) for n,side in enumerate(('left','right'))}
        verified=dict(codec=codec,stage=stage,event='VERIFIED',outputs=copy.deepcopy(last[codec]))
        history.extend([prepared,verified])
        config=dict(directory=row['directory'],identity=dict(device=1,inode=10),stage=stage,
            binary=packet['binaries']['ox']['path'],flags=row['server_flags'],deadline=500+index,
            worker_pid=22,resource_fds=resources)
        preps[key]=store.put(key+'-PREPARED.json',dict(data=prepared,proxy_config=config,script_pins={}))
        inherited[key]=dict(proxy_pid=1001+index*3,worker_pid=22,resource_fds=resources,binding=binding)
        for name in (row['directory']+'/launcher.py',proxy_command(packet,row)[2]):
            programs[name]=('original program metadata '+name).encode()
            scripts[name]=dict(path=name,sha256=hashlib.sha256(programs[name]).hexdigest())
        ledger.finish(index,returncode=0,transport_record_sha256=call['transport_record_sha256'],
                      helper_record_sha256s=call['helper_record_sha256s'])
        results.append(dict(index=index,codec=codec,stage=stage,candidate=candidate,helpers=check));event()
    store.put('WORKER-RESULT.json',dict(result=snapshot(),events=events,pair_pins=pairs,data_history=history,
        script_pins=scripts,preparation_pins=preps,resource_release_authorized=False))
    store.put('WORKER-DIRECTORIES-CLOSED.json',dict(codec_directories_closed=3,
        inherited_resource_fds_closed=False,resource_release_authorized=False))
    outcome=copy.deepcopy(pair_fixture('seed')[1]['client']);outcome['command']=command
    outcome['client_cleanup']['pid']=22;outcome['stdout']=''
    return packet,store,outcome,programs,inherited

class Parent(unittest.TestCase):
    def check(self,mutation=None):
        packet,store,out,programs,inherited=fixture();self.events=[]
        saved=store.read_json('WORKER-RESULT.json')
        if mutation=='missing':saved['pair_pins'].pop(next(iter(saved['pair_pins'])))
        if mutation=='fake-backend':saved['data_history'][0]['clones'][0]['backend']='original-test-double'
        if mutation=='noop':saved['data_history'][5]['outputs']['left']['identity']['st_mtime_ns']+=1
        if mutation=='worker':out['client_cleanup']['reaped']=False
        if mutation=='script':programs[next(iter(programs))]=b'changed shim'
        if mutation=='grant':inherited['uncompressed-seed']['resource_fds']=[]
        if mutation=='event':
            record=store.read_json(saved['events'][1]['name'])
            record['snapshot']['ledger']['state']='READY'
            saved['events'][1]=store.put(saved['events'][1]['name'],record)
        if mutation=='helper-target':
            name='uncompressed-update-PAIR.json';record=store.read_json(name)
            record['pair']['client']['stdout']=frame('client',pid=2002,digest='f'*64)
            saved['pair_pins'][name]=store.put(name,record)
        if mutation in ('fake-backend','noop'):
            # Re-pin the altered preparation too: semantic cross-checks, not
            # merely hash mismatch, must still reject the inconsistent proof.
            name='uncompressed-seed' if mutation=='fake-backend' else 'uncompressed-noop'
            prep=store.read_json(saved['preparation_pins'][name]['name'])
            if mutation=='fake-backend':prep['data']=saved['data_history'][0]
            saved['preparation_pins'][name]=store.put(name+'-PREPARED.json',prep)
        store.put('WORKER-RESULT.json',saved)
        def fence(packet):self.events.append('input-fence')
        def outputs(packet,history):self.events.append('six-output-hashes')
        return parent.audit(packet,store,out,read_program=lambda name,limit:programs[name],
            fence_inputs=fence,verify_outputs=outputs,
            read_codec=lambda row,config:inherited[row['codec']+'-'+row['stage']])

    def test_complete_original_fabricated_matrix_reparses_without_terminal_claim(self):
        proof=self.check()
        self.assertEqual(proof['cli_calls'],9);self.assertEqual(proof['sdk_helpers'],6)
        self.assertTrue(proof['external_children_settled']);self.assertTrue(proof['raw_digest_verified_all'])
        self.assertFalse(proof['parent_terminal_proved']);self.assertFalse(proof['pixels_compared'])
        self.assertEqual(self.events,['input-fence','six-output-hashes'])

    def test_incomplete_or_substituted_evidence_never_releases(self):
        for mutation in ('missing','fake-backend','noop','worker','script','grant','event','helper-target'):
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.check(mutation)

if __name__=='__main__':unittest.main()
