"""Retained-parent whole-run join; called only while IO/CPU still owned."""
from copy import deepcopy
import hashlib,math,os
from pathlib import Path
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import child
from sdk_merge_receiving.parent import pinned
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.data import FIELDS,inspect,stamp
from sdk_merge_receiving.plan import require
from sdk_negative_receiving.plan import schedule
from sdk_negative_receiving.publication import verify
from sdk_negative_receiving.parent import audit as replay
from sdk_negative_receiving.runtime import key,proxy_command


def audit(packet,store,outcome):
    start=store.read_json('OWNER-START.json',expected_sha256=None)
    bound=store.read_json('ADMISSION-BOUND.json',expected_sha256=None)
    pid=child(outcome,bound['command'])
    require(start['owner_pid']==os.getpid() and pid!=os.getpid() and start['child_pid']==pid and start['command']==bound['command']
        and start['admission_nonce']==bound['admission_nonce'] and start['target']=='current-sdk-negative-receiving'
        and type(start['cpu_credits']) is int and start['cpu_credits']==8
        and exact(start['token_indexes'],list(range(8))) and start['io_mode']=='EX_GLOBAL',
        'actual parent/worker/admission/target differs')
    resources=start['inherited_resource_fds']
    require(type(resources) is list and len(resources)==9 and all(type(r) is dict and set(r)=={'fd','device','inode'}
        and all(type(v) is int and v>0 for v in r.values()) and r['fd']>=3 for r in resources)
        and len({r['fd'] for r in resources})==9,'exact inherited grant observations required')
    binding=store.read_json('WORKER-BINDING.json',expected_sha256=None)
    require(exact(binding,dict(schema='unison-current-negative-worker-binding/1',parent_pid=os.getpid(),worker_pid=pid,
        resource_fds=resources,binding=dict(inherited_fds=[r['fd'] for r in resources],canonical_metadata_bound=True,
            lock_ownership_independently_proved=False,resource_release_authorized=False))),
        'actual worker inherited binding differs')
    saved=store.read_json('WORKER-RESULT.json',expected_sha256=None)
    require(type(saved) is dict and set(saved)=={'result','pair_pins','event_pins','data_history','script_pins',
        'preparation_pins','output_pins','resource_release_authorized'} and saved['resource_release_authorized'] is False
        and len(saved['data_history'])==24 and len(saved['event_pins'])==25,'exact complete worker record required')
    rows=schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']
    require(set(saved['preparation_pins'])==set(saved['output_pins'])=={key(r) for r in rows},'complete phase records required')
    previous={};expected_scripts=set();latest={}
    def output(row,candidate):
        index=rows.index(row);name=key(row);group=(row['codec'],row['policy'])
        prep=pinned(store,saved['preparation_pins'][name],name+'-PREPARED.json')
        verified=pinned(store,saved['output_pins'][name],name+'-OUTPUTS.json')
        before,after=saved['data_history'][index*2:index*2+2]
        require(exact(before,prep['data']) and exact(after,verified)
            and before['event']=='PREPARED' and after['event']=='VERIFIED'
            and all(v[k]==row[k] for v in (before,after) for k in ('codec','policy','stage'))
            and exact(before['candidate'],candidate),'ordered durable data history differs')
        config=prep['proxy_config'];root=Path(row['directory'])
        require(set(config)=={'directory','identity','stage','binary','flags','deadline','worker_pid','resource_fds'}
            and config['directory']==str(root) and config['stage']==row['stage']
            and config['binary']==packet['binaries']['ox']['path'] and exact(config['flags'],row['server_flags'])
            and config['worker_pid']==pid and exact(config['resource_fds'],resources)
            and type(config['deadline']) in (int,float) and math.isfinite(config['deadline'])
            and config['deadline']<=start['owner_observation_deadline'],'exact phase runtime/shim configuration required')
        directory=Store(str(root),config['identity'])
        try:inherited=directory.read_json(row['stage']+'-INHERITED.json',expected_sha256=None)
        finally:directory.close()
        pair=pinned(store,saved['pair_pins'][name],name+'-PAIR.json')
        require(exact(inherited,dict(proxy_pid=pair['pair']['proxy']['client_cleanup']['pid'],worker_pid=pid,
            resource_fds=resources,binding=dict(inherited_fds=[r['fd'] for r in resources],canonical_metadata_bound=True,
                lock_ownership_independently_proved=False,resource_release_authorized=False))),
            'actual proxy inherited observation differs')
        case=next(c for c in packet['cases'] if c['codec']==row['codec']);ref=case['states']['base']
        outputs=verified['outputs'];require(set(outputs)=={'left','right'},'both endpoint fences required')
        for value in outputs.values():
            require(set(value)=={'sha256','bytes','identity'} and set(value['identity'])==set(FIELDS)
                and all(type(v) is int and v>=0 for v in value['identity'].values())
                and type(value['bytes']) is int and value['bytes']==ref['bytes']==value['identity']['st_size']
                and value['identity']['st_mode']==0o100600 and value['identity']['st_nlink']==1,
                'bounded private output fence required')
        if row['stage']=='seed':
            clone=before['clone'];epoch=packet['source_observations'][ref['path']]
            require(set(before)=={'codec','policy','stage','event','clone','candidate'}
                and candidate=={k:ref[k] for k in ('sha256','bytes')}
                and clone['source']==ref['path'] and exact(clone['source_identity'],epoch)
                and clone['backend']=='native-fclonefileat-only' and clone['source_payload_hash_bytes']==0
                and clone['clone_hash_bytes']==ref['bytes'] and clone['clone_sha256']==ref['sha256']
                and (clone['clone_identity']['st_dev'],clone['clone_identity']['st_ino'])!=(epoch['st_dev'],epoch['st_ino'])
                and all(value['sha256']==ref['sha256'] for value in outputs.values()),'source-bound seed clone/output differs')
            publication=dict(seed_exact=True,resource_release_authorized=False)
        else:
            fault=before['fault'];old=previous[group]
            require(set(before)=={'codec','policy','stage','event','fault','candidate'}
                and exact(fault['before'],old['left']) and exact(fault['after'],outputs['left'])
                and fault['source_payload_hash_bytes']==0 and fault['actual_SDK_finding_proved'] is False
                and fault['receiving_publication_proved'] is False and fault['resource_release_authorized'] is False
                and fault['mutation']['tag']==51111 and fault['mutation']['bytes_changed']==1
                and fault['mutation']['xor_mask']==1 and type(fault['mutation']['offset']) is int
                and 8<=fault['mutation']['offset']<ref['bytes'] and outputs['left']['sha256']==candidate['sha256'],
                'exact one-bit disposable mutation record differs')
            require(all(outputs['left']['identity'][k]==old['left']['identity'][k] for k in FIELDS
                if k not in ('st_mtime_ns','st_ctime_ns')),'fault changed stable private ownership')
            publication=verify(policy=row['policy'],before=old['right'],after=outputs['right'],candidate=candidate)
            for side,value in outputs.items():
                endpoint=root/side;native=endpoint.lstat()
                require(exact(inspect(endpoint,(native.st_dev,native.st_ino),{k:value[k] for k in ('sha256','bytes')}),value),
                        'fresh final output hash/epoch differs')
        require(exact(publication,verified['publication']),'saved publication verdict differs')
        previous[group]=deepcopy(outputs);latest[group]=name
        expected_scripts.update((str(root/'launcher.py'),proxy_command(packet,row)[2]))
        return publication
    verdict=replay(packet,dict(result=saved['result'],pair_pins=saved['pair_pins']),
        read_pinned=lambda pin:store.read(pin['name'],expected_sha256=pin['sha256']),
        proxy_command=lambda row:proxy_command(packet,row),verify_outputs=output)
    require(set(saved['script_pins'])==expected_scripts,'complete generated shim inventory required')
    for name,pin in saved['script_pins'].items():
        require(pin['path']==name and hashlib.sha256(read_bytes(name,65536)).hexdigest()==pin['sha256'],'generated shim changed')
    for index,pin in enumerate(saved['event_pins']):
        event=pinned(store,pin,'EVENT-%02d.json'%index)
        accepted=index//2;intent=index%2
        require(exact(event['snapshot']['events'],saved['result']['events'][:accepted*2+intent])
            and exact(event['snapshot']['results'],saved['result']['results'][:accepted])
            and event['snapshot']['resource_release_authorized'] is False
            and event['snapshot']['parent_audit_required'] is True and event['resource_release_authorized'] is False,
            'durable negative intent/acceptance snapshot differs')
        require(set(event['pair_pins'])=={key(r) for r in rows[:accepted]},'durable pair-prefix inventory differs')
        require(all(exact(v,saved['pair_pins'][k]) for k,v in event['pair_pins'].items()),'durable pair-prefix pin changed')
    require(exact(store.read_json('WORKER-DIRECTORIES-CLOSED.json',expected_sha256=None),
        dict(codec_policy_directories_closed=6,inherited_resource_fds_closed=False,resource_release_authorized=False)),
        'worker metadata directory closure incomplete')
    for name,epoch in packet['source_observations'].items():require(stamp(os.lstat(name))==epoch,'retained generated input epoch changed')
    return dict(external_children_settled=True,cli_calls=12,SDK_helpers=6,complete_raw_replay=verdict,
        final_private_outputs_rehashed=True,source_payload_hash_bytes=0,parent_terminal_proved=False,
        pixels_compared=False,semantic_eligibility_proved=False)
