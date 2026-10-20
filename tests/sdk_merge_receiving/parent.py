"""Independent complete-run audit under the parent's retained IO/CPU grant.

Reparse immutable call/helper evidence, source-bound data records and current
private output bytes. No PID signaling, fd retry or parent-tool terminal claim.
Incomplete runs refuse; they need a separately scoped retained-prefix recovery.
"""
import hashlib
from copy import deepcopy
import json
import os
import math
from pathlib import Path
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.plan import schedule,require,digest
from sdk_merge_receiving.evidence import child,bind
from sdk_merge_receiving.helpers import audit as audit_helpers
from sdk_merge_receiving.ledger import Ledger
from sdk_merge_receiving.data import Cases,inspect,FIELDS
from sdk_merge_receiving.runtime import proxy_command
from sdk_merge_receiving.store import Store


def pinned(store,pin,name):
    require(type(pin) is dict and set(pin)=={'name','sha256','bytes'} and pin['name']==name
        and type(pin['bytes']) is int and 0<pin['bytes']<=2*1048576,'exact bounded record pin required')
    digest(pin['sha256'])
    raw=store.read(name,expected_sha256=pin['sha256'])
    require(len(raw)==pin['bytes'],'pinned record size differs')
    from sdk_merge_receiving.metadata import document
    return document(raw)


def outputs(packet,history):
    """Fresh parent-side hashes of six private final receiving files."""
    for index,case in enumerate(packet['cases']):
        expected={k:case['states']['target'][k] for k in ('sha256','bytes')}
        final=history[index*6+5]['outputs']
        for side in ('left','right'):
            endpoint=Path(packet['workspace'])/case['codec']/side
            native=endpoint.lstat()
            actual=inspect(endpoint,(native.st_dev,native.st_ino),expected)
            require(exact(actual,final[side]),'fresh parent output differs from final accepted noop')


def codec_record(row,config):
    value=Store(row['directory'],config['identity'])
    try:return value.read_json(row['stage']+'-INHERITED.json',expected_sha256=None)
    finally:value.close()


def audit(packet,store,outcome,*,read_program=read_bytes,verify_outputs=outputs,
          fence_inputs=lambda packet:Cases(packet).fence_sources(),read_codec=codec_record):
    bound=store.read_json('ADMISSION-BOUND.json',expected_sha256=None)
    start=store.read_json('OWNER-START.json',expected_sha256=None)
    worker_pid=child(outcome,bound['command'])
    require(start['child_pid']==worker_pid and start['owner_pid']==os.getpid()
        and start['command']==bound['command'] and start['admission_nonce']==bound['admission_nonce'],
        'actual worker/parent/admission binding differs')
    require(type(start['owner_observation_deadline']) in (int,float)
        and math.isfinite(start['owner_observation_deadline'])
        and start.get('target')=='current-sdk-merge' and type(start.get('cpu_credits')) is int
        and start['cpu_credits']==8 and exact(start.get('token_indexes'),list(range(8)))
        and start.get('io_mode')=='EX_GLOBAL','exact finite parent grant required')
    resources=start['inherited_resource_fds']
    require(type(resources) is list and len(resources)==9
        and all(type(r) is dict and set(r)=={'fd','device','inode'}
            and all(type(v) is int and v>0 for v in r.values()) and r['fd']>=3 for r in resources)
        and len({r['fd'] for r in resources})==9,'exact distinct inherited resource rows required')
    binding=store.read_json('WORKER-BINDING.json',expected_sha256=None)
    require(exact(binding,dict(schema='unison-current-merge-worker-binding/1',parent_pid=start['owner_pid'],
        worker_pid=worker_pid,resource_fds=resources,binding=dict(inherited_fds=[r['fd'] for r in resources],
            canonical_metadata_bound=True,lock_ownership_independently_proved=False,
            resource_release_authorized=False))),'actual worker inherited binding differs')
    saved=store.read_json('WORKER-RESULT.json',expected_sha256=None)
    require(type(saved) is dict and set(saved)=={'result','events','pair_pins','data_history',
        'script_pins','preparation_pins','resource_release_authorized'}
        and saved['resource_release_authorized'] is False,'exact non-releasing worker result required')
    result=saved['result'];rows=schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']
    require(type(result) is dict and set(result)=={'ledger','results','resource_release_authorized'}
        and result['resource_release_authorized'] is False and len(result['results'])==9,
        'complete nine-result worker report required')
    require(len(saved['events'])==19 and len(saved['data_history'])==18
        and len(saved['pair_pins'])==9 and len(saved['preparation_pins'])==9,
        'complete bounded event/data/pair/preparation counts required')
    ledger=Ledger();helper_count=0;reports=[];expected_scripts=set();last_outputs={}
    audited_results=[];audited_pairs={};expected_events=[]
    def expected_event():
        expected_events.append(dict(schema='unison-merge-worker-event/1',
            snapshot=dict(ledger=ledger.report(),results=deepcopy(audited_results),resource_release_authorized=False),
            pair_pins=deepcopy(audited_pairs),resource_release_authorized=False))
    expected_event()
    for index,row in enumerate(rows):
        codec,stage=row['codec'],row['stage'];key=codec+'-'+stage
        pair_record=pinned(store,saved['pair_pins'][key+'-PAIR.json'],key+'-PAIR.json')
        require(set(pair_record)=={'schema','identity','command','pair','raw_proxy_hex'}
            and pair_record['schema']=='unison-merge-pair-evidence/1'
            and exact(pair_record['identity'],row['identity']) and exact(pair_record['command'],row['command']),
            'pair record is not the exact scheduled call')
        require(type(pair_record['raw_proxy_hex']) is str and len(pair_record['raw_proxy_hex'])<=131072,
                'bounded raw proxy frame hex required')
        raw=bytes.fromhex(pair_record['raw_proxy_hex'])
        require(raw.hex()==pair_record['raw_proxy_hex'],'canonical raw proxy hex required')
        call=bind(row,pair_record['pair'],expected_proxy_command=proxy_command(packet,row),raw_proxy_bytes=raw)
        case=next(c for c in packet['cases'] if c['codec']==codec)
        candidate={k:case['states']['base' if stage=='seed' else 'target'][k] for k in ('sha256','bytes')}
        helpers=audit_helpers(call['log'],stage=stage,returncode=call['returncode'],
                              candidate_sha256=candidate['sha256'],candidate_bytes=candidate['bytes'])
        helper_count+=helpers['helper_count'];reports.extend(h['report'] for h in helpers['helpers'])
        command_sha=hashlib.sha256(json.dumps(row['command'],ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
        ledger.begin(codec,stage,command_sha)
        expected_event()
        ledger.finish(index,returncode=call['returncode'],transport_record_sha256=call['transport_record_sha256'],
                      helper_record_sha256s=call['helper_record_sha256s'])
        require(exact(result['results'][index],dict(index=index,codec=codec,stage=stage,
            candidate=candidate,helpers=helpers)),'worker functional result differs from raw records')
        audited_results.append(dict(index=index,codec=codec,stage=stage,candidate=candidate,helpers=helpers))
        audited_pairs[key+'-PAIR.json']=saved['pair_pins'][key+'-PAIR.json']
        expected_event()
        preparation=pinned(store,saved['preparation_pins'][key],key+'-PREPARED.json')
        require(set(preparation)=={'data','proxy_config','script_pins'},'exact phase preparation record required')
        config=preparation['proxy_config'];root=Path(row['directory'])
        require(type(config) is dict and set(config)=={'directory','identity','stage','binary','flags',
            'deadline','worker_pid','resource_fds'},'exact proxy configuration fields required')
        require(config['directory']==str(root) and config['stage']==stage
            and config['binary']==packet['binaries']['ox']['path'] and config['flags']==row['server_flags']
            and config['worker_pid']==worker_pid and exact(config['resource_fds'],start['inherited_resource_fds']),
            'proxy configuration differs from actual worker/flags/grant')
        require(type(config['deadline']) in (int,float) and math.isfinite(config['deadline'])
            and config['deadline']<=start['owner_observation_deadline'],'phase observation exceeds owner window')
        inherited=read_codec(row,config)
        require(exact(inherited,dict(proxy_pid=pair_record['pair']['proxy']['client_cleanup']['pid'],
            worker_pid=worker_pid,resource_fds=start['inherited_resource_fds'],
            binding=dict(inherited_fds=[r['fd'] for r in start['inherited_resource_fds']],
                canonical_metadata_bound=True,lock_ownership_independently_proved=False,
                resource_release_authorized=False))),'proxy actual inherited observation differs')
        prepared,verified=saved['data_history'][index*2:index*2+2]
        require(exact(prepared,preparation['data']) and prepared['codec']==codec and prepared['stage']==stage
            and prepared['event']=='PREPARED' and exact(prepared['candidate'],candidate)
            and verified['codec']==codec and verified['stage']==stage and verified['event']=='VERIFIED',
            'ordered data history differs')
        clones=prepared['clones'];sides=('left',) if stage=='seed' else ('left','right') if stage=='update' else ()
        require(type(clones) is list and len(clones)==len(sides),'exact phase clone count required')
        for clone,side in zip(clones,sides):
            reference=case['states']['base' if stage=='seed' else side]
            identity=clone['clone_identity'];source=packet['source_observations'][reference['path']]
            require(type(clone) is dict and set(clone)=={'source','source_identity','clone_identity',
                'clone_sha256','clone_hash_bytes','source_payload_hash_bytes','backend'}
                and clone['backend']=='native-fclonefileat-only' and clone['source']==reference['path']
                and exact(clone['source_identity'],source) and clone['clone_sha256']==reference['sha256']
                and type(clone['clone_hash_bytes']) is int and clone['clone_hash_bytes']==reference['bytes']
                and type(clone['source_payload_hash_bytes']) is int and clone['source_payload_hash_bytes']==0
                and type(identity) is dict and set(identity)==set(FIELDS)
                and all(type(v) is int and v>=0 for v in identity.values())
                and identity['st_mode']==0o100600 and identity['st_size']==reference['bytes']
                and identity['st_uid']==source['st_uid'] and identity['st_nlink']==1
                and (identity['st_dev'],identity['st_ino'])!=(source['st_dev'],source['st_ino']),
                'native disposable clone/source preservation record differs')
        require(type(verified['outputs']) is dict and set(verified['outputs'])=={'left','right'},
                'both endpoint output fences required')
        for value in verified['outputs'].values():
            require(value['sha256']==candidate['sha256'] and value['bytes']==candidate['bytes']
                and type(value['bytes']) is int and set(value['identity'])==set(FIELDS)
                and all(type(v) is int and v>=0 for v in value['identity'].values()),'output byte fence differs')
        if stage=='noop':require(exact(last_outputs[codec],verified['outputs']), 'noop changed output epochs/bytes')
        last_outputs[codec]=verified['outputs']
        expected_scripts.update((str(root/'launcher.py'),proxy_command(packet,row)[2]))
    require(helper_count==6 and exact(result['ledger'],ledger.report()),'six helpers/exact complete ledger required')
    for index,pin in enumerate(saved['events']):
        event=pinned(store,pin,'EVENT-%02d.json'%index)
        require(exact(event,expected_events[index]),'ordered durable intent/outcome event differs')
        if index==18:require(exact(event['snapshot'],result) and exact(event['pair_pins'],saved['pair_pins']),
                            'final saved event differs from worker result')
    require(set(saved['script_pins'])==expected_scripts,'exact generated shim inventory required')
    for name,pin in saved['script_pins'].items():
        require(pin['path']==name and hashlib.sha256(read_program(name,65536)).hexdigest()==pin['sha256'],
                'generated shim changed since execution')
    closed=store.read_json('WORKER-DIRECTORIES-CLOSED.json',expected_sha256=None)
    require(exact(closed,dict(codec_directories_closed=3,inherited_resource_fds_closed=False,
                              resource_release_authorized=False)), 'worker directory closure incomplete')
    fence_inputs(packet);verify_outputs(packet,saved['data_history'])
    return dict(external_children_settled=True,cli_calls=9,proxy_server_calls=9,sdk_helpers=6,
        raw_digest_verified_all=all(r['raw_digest_verified'] for r in reports),reports=reports,
        final_private_outputs_rehashed=True,source_payload_hash_bytes=0,
        parent_terminal_proved=False,semantic_eligibility_proved=False,pixels_compared=False)
