"""Pure independently read transport/owner join for one exact scheduled call.

Consumes source-bound retained-owner records; does not poll processes or close
resources. Failure propagates to the retained worker, never a safe failed prefix.
"""
import hashlib
import json
from sdk_merge_receiving.plan import require
from sdk_merge_receiving.helpers import records


def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'duplicate raw proxy field')
        result[key]=value
    return result


def child(out, expected):
    require(type(out) is dict and set(out)=={'command','returncode','timed_out',
        'capture_truncated','stdout','stderr','client_cleanup',
        'aggregate_or_parent_terminal_proved','io_cpu_release_authorized'},
        'exact retained child record required')
    require(out['command']==expected and type(out['returncode']) is int
        and out['returncode']==0 and out['timed_out'] is False
        and out['capture_truncated'] is False
        and out['aggregate_or_parent_terminal_proved'] is False
        and out['io_cpu_release_authorized'] is False,'child command/status/capture differs')
    cleanup=out['client_cleanup']
    require(type(cleanup) is dict and set(cleanup)=={'pid','returncode','reaped',
        'hard_kill_required','other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
        and type(cleanup['pid']) is int and 0<cleanup['pid']<2**31
        and type(cleanup['returncode']) is int and cleanup['returncode']==0
        and cleanup['reaped'] is True and cleanup['hard_kill_required'] is False
        and cleanup['other_group_members_absent_before_reap'] is True
        and cleanup['group_cleanup_before_leader_reap'] is True,'child/group proof incomplete')
    for stream in ('stdout','stderr'):
        require(type(out[stream]) is str and len(out[stream].encode('utf-8'))<=262144,
                'bounded full child diagnostic required')
    return cleanup['pid']


def bind(row,pair,*,expected_proxy_command,raw_proxy_bytes):
    require(type(pair) is dict and set(pair)=={'client','proxy','raw_proxy',
        'external_sdk_audit_required','resource_release_authorized'}
        and pair['external_sdk_audit_required'] is True
        and pair['resource_release_authorized'] is False,'exact non-releasing pair required')
    client_pid=child(pair['client'],row['command'])
    proxy_pid=child(pair['proxy'],expected_proxy_command)
    require(client_pid!=proxy_pid,'aliased peer process identities')
    require(type(raw_proxy_bytes) is bytes and 0<len(raw_proxy_bytes)<=65536,
            'bounded independently read raw proxy bytes required')
    frame=json.loads(raw_proxy_bytes,object_pairs_hook=unique,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite raw JSON')))
    require(frame==pair['raw_proxy'] and type(frame) is dict and set(frame)=={
        'schema','server_command','server_pid','server_returncode','server_reaped',
        'server_group','input_eof_forwarded','output_eof_forwarded','forwarded_protocol_bytes',
        'parent_group_audit_required','sdk_helper_audit_required','resource_release_authorized'},
        'raw proxy frame differs from returned evidence')
    require(frame['schema']=='unison-retained-merge-proxy/1'
        and frame['server_command']==row['server_command']
        and type(frame['server_pid']) is int and 0<frame['server_pid']<2**31
        and frame['server_pid'] not in (client_pid,proxy_pid)
        and type(frame['server_returncode']) is int and frame['server_returncode']==0
        and frame['server_reaped'] is True and type(frame['server_group']) is int
        and frame['server_group']==proxy_pid and frame['input_eof_forwarded'] is True
        and frame['output_eof_forwarded'] is True
        and frame['parent_group_audit_required'] is True
        and frame['sdk_helper_audit_required'] is True
        and frame['resource_release_authorized'] is False,'native server/parent binding incomplete')
    counts=frame['forwarded_protocol_bytes']
    require(type(counts) is dict and set(counts)=={'client_to_server_bytes','server_to_client_bytes'}
        and all(type(v) is int and 0<v<2**63 for v in counts.values()),
        'typed nonempty protocol directions required')
    log='\n'.join(pair[peer][stream] for peer in ('client','proxy') for stream in ('stdout','stderr'))
    processes,groups=records.parse(log),records.parse_groups(log)
    expected={'client','server'} if row['stage']=='update' else set()
    require(len(processes)==len(groups)==len(expected)
        and {p.endpoint for p in processes}=={g.endpoint for g in groups}==expected,
        'phase helper diagnostics differ')
    hashes=[]
    for endpoint in ('client','server'):
        if endpoint not in expected:continue
        prefix='server: ' if endpoint=='server' else ''
        lines=[line for line in log.splitlines() if line.startswith(
            ('['+prefix+'validation-process] ','['+prefix+'validation-group] '))]
        require(len(lines)==2,'exact raw helper process/group pair required')
        hashes.append(hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest())
    joined=dict(identity=row['identity'],client=pair['client'],proxy=pair['proxy'],
                raw_proxy_sha256=hashlib.sha256(raw_proxy_bytes).hexdigest())
    record_hash=hashlib.sha256(json.dumps(joined,sort_keys=True,separators=(',',':'),
                                        allow_nan=False).encode()).hexdigest()
    return dict(returncode=0,log=log,transport_record_sha256=record_hash,
                helper_record_sha256s=hashes)
