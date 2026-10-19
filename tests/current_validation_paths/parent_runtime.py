"""Retained-owner whole-run join; called only while IO/CPU are still owned.

Binds the actual worker terminal, its inherited grant observation and closed
metadata record, then replays every attempted call through the parent reader.
A settled failed prefix is reported complete=False, never as a pass.
"""
import hashlib,os
from pathlib import PurePosixPath
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import child
from sdk_merge_receiving.plan import require
from current_validation_paths import admission as A,parent
from current_validation_paths.parent_io import Reader


def audit(packet,store,outcome,*,reader=Reader,read=read_bytes):
    start=store.read_json('OWNER-START.json',expected_sha256=None)
    bound=store.read_json('ADMISSION-BOUND.json',expected_sha256=None)
    pid=child(outcome,bound['command'])
    require(start['owner_pid']==os.getpid() and pid!=os.getpid() and start['child_pid']==pid and start['command']==bound['command']
        and start['admission_nonce']==bound['admission_nonce'] and start['target']==A.TARGET
        and type(start['cpu_credits']) is int and start['cpu_credits']==8
        and exact(start['token_indexes'],list(range(8))) and start['io_mode']=='EX_GLOBAL',
        'actual parent/worker/admission/target differs')
    resources=start['inherited_resource_fds']
    require(type(resources) is list and len(resources)==9 and all(type(r) is dict and set(r)=={'fd','device','inode'}
        and all(type(v) is int and v>0 for v in r.values()) and r['fd']>=3 for r in resources)
        and len({r['fd'] for r in resources})==9,'exact inherited grant observations required')
    binding=dict(inherited_fds=[r['fd'] for r in resources],canonical_metadata_bound=True,
        lock_ownership_independently_proved=False,resource_release_authorized=False)
    require(exact(store.read_json('WORKER-BINDING.json',expected_sha256=None),dict(schema='unison-current-named-worker-binding/1',
        parent_pid=os.getpid(),worker_pid=pid,resource_fds=resources,binding=binding)),'actual worker inherited binding differs')
    result=store.read_json('RESULT.json',expected_sha256=None)
    require(exact(store.read_json('WORKER-CLOSED.json',expected_sha256=None),dict(result_complete=result.get('complete'),
        worker_metadata_closed=True,inherited_resource_fds_closed=False,resource_release_authorized=False)),
        'worker metadata closure incomplete')
    raw=read(packet['legacy_source']['path'],256*1024)
    require(len(raw)==packet['legacy_source']['bytes'] and hashlib.sha256(raw).hexdigest()==packet['legacy_source']['sha256'],
        'original case source changed')
    roots={row['directory']:PurePosixPath(row['directory']).name for row in packet['rows']}
    files=reader(packet['workspace'],dict(store.identity),roots)
    try:
        verdict=parent.replay(packet,result,source=raw.decode('utf-8'),worker_pid=pid,resources=resources,
            owner_deadline=start['owner_observation_deadline'],read_case=files.read_case,read_root=files.read_root,
            case_state=files.case_state)
    except UnresolvedOwnership:raise
    except BaseException:
        files.close();raise
    files.close()
    return dict(external_children_settled=True,complete=verdict['complete'],replay=verdict,
        parent_terminal_proved=False,resource_release_authorized=False)
