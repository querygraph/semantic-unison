"""Pure designated negative receiving audit; no ordinary failed-prefix release.

Expected require exit1 and warn exit0 have distinct evidence contracts. Caller
still owns destination byte/epoch checks, worker settlement and all resources.
The successful-merge transport auditor remains unchanged.
"""
import hashlib,json
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import child as positive_child,unique
from sdk_merge_receiving.plan import require
from sdk_negative_receiving.finding import helper


def rejected_child(out,command):
    require(type(out) is dict and set(out)=={'command','returncode','timed_out',
        'capture_truncated','stdout','stderr','client_cleanup',
        'aggregate_or_parent_terminal_proved','io_cpu_release_authorized'},'exact child evidence required')
    require(exact(out['command'],command) and type(out['returncode']) is int
        and out['returncode']==1 and out['timed_out'] is False
        and out['capture_truncated'] is False and out['aggregate_or_parent_terminal_proved'] is False
        and out['io_cpu_release_authorized'] is False,'exact designated rejection terminal required')
    c=out['client_cleanup']
    require(type(c) is dict and set(c)=={'pid','returncode','reaped','hard_kill_required',
        'other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
        and type(c['pid']) is int and 0<c['pid']<2**31 and type(c['returncode']) is int
        and c['returncode']==1 and c['reaped'] is True and c['hard_kill_required'] is False
        and c['other_group_members_absent_before_reap'] is True
        and c['group_cleanup_before_leader_reap'] is True,'designated failed child/group unresolved')
    for stream in ('stdout','stderr'):
        require(type(out[stream]) is str and len(out[stream].encode())<=262144,
                'bounded full designated-rejection diagnostics required')
    return c['pid']


def policy_flag(command,policy):
    require(type(command) is list and all(type(s) is str for s in command)
        and command.count('-adobevalidate')==1,'one explicit validation policy required')
    index=command.index('-adobevalidate')
    require(index+1<len(command) and command[index+1]==policy,'receiving command policy differs')
    require(command.count('-adobevalidatescope')==1,'explicit received-only scope required')
    index=command.index('-adobevalidatescope')
    require(index+1<len(command) and command[index+1]=='received','receiving scope differs')


def audit(pair,*,client_command,proxy_command,server_command,policy,
          raw_proxy_bytes,candidate_sha256,candidate_bytes):
    require(policy in ('require','warn'),'negative receive policy must be require or warn')
    policy_flag(client_command,policy);policy_flag(server_command,policy)
    require(type(pair) is dict and set(pair)=={'client','proxy','raw_proxy',
        'external_sdk_audit_required','resource_release_authorized'}
        and pair['external_sdk_audit_required'] is True and pair['resource_release_authorized'] is False,
        'exact non-releasing retained pair required')
    client_pid=(rejected_child if policy=='require' else positive_child)(pair['client'],client_command)
    proxy_pid=positive_child(pair['proxy'],proxy_command)
    require(client_pid!=proxy_pid,'aliased client/proxy identities')
    require(type(raw_proxy_bytes) is bytes and 0<len(raw_proxy_bytes)<=65536,'bounded raw proxy required')
    frame=json.loads(raw_proxy_bytes,object_pairs_hook=unique,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite raw proxy')))
    require(type(frame) is dict and exact(frame,pair['raw_proxy']) and set(frame)=={
        'schema','server_command','server_pid','server_returncode','server_reaped','server_group',
        'input_eof_forwarded','output_eof_forwarded','forwarded_protocol_bytes',
        'parent_group_audit_required','sdk_helper_audit_required','resource_release_authorized'},
        'exact independently read raw frame required')
    require(frame['schema']=='unison-retained-merge-proxy/1' and exact(frame['server_command'],server_command)
        and type(frame['server_pid']) is int and 0<frame['server_pid']<2**31
        and frame['server_pid'] not in (client_pid,proxy_pid)
        and type(frame['server_returncode']) is int and frame['server_returncode']==0
        and frame['server_reaped'] is True and type(frame['server_group']) is int
        and frame['server_group']==proxy_pid and frame['input_eof_forwarded'] is True
        and frame['output_eof_forwarded'] is True and frame['parent_group_audit_required'] is True
        and frame['sdk_helper_audit_required'] is True and frame['resource_release_authorized'] is False,
        'normal server/pump completion required despite client designated rejection')
    counts=frame['forwarded_protocol_bytes']
    require(type(counts) is dict and set(counts)=={'client_to_server_bytes','server_to_client_bytes'}
        and all(type(v) is int and 0<v<2**63 for v in counts.values()),'both protocol directions required')
    log='\n'.join(pair[p][s] for p in ('client','proxy') for s in ('stdout','stderr'))
    finding=helper(log,candidate_sha256=candidate_sha256,candidate_bytes=candidate_bytes)
    require(finding['settlement']['helper_pid'] not in (client_pid,proxy_pid,frame['server_pid']),
            'SDK helper aliases transport process')
    marker='Adobe DNG validation rejected' if policy=='require' else 'Adobe DNG validation warning'
    require(marker in log and 'SDK driver reported validation errors' in log,
            'explicit native validation rejection/warning diagnostic required')
    return dict(policy=policy,expected_client_exit=1 if policy=='require' else 0,
        client_pid=client_pid,proxy_pid=proxy_pid,server_pid=frame['server_pid'],finding=finding,
        raw_proxy_sha256=hashlib.sha256(raw_proxy_bytes).hexdigest(),
        destination_fence_required=True,worker_settlement_required=True,
        parent_terminal_proved=False,resource_release_authorized=False)
