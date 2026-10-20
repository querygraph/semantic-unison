"""Designated archive missing-base call; never relaxes batch zero-only audits.

Only the owning ten-stage scenario may use this adapter. Nonzero status is not
closure: raw captures, exact child wait/group records and server EOF binding are
independently required. Functional variant preservation belongs to its caller.
"""
import json,os,re,time
from batch_transport import launch
from batch_artifacts import publish,read
from batch_observations import read as read_observation
from sdk_merge_receiving.evidence import unique
from sdk_merge_receiving.transport import wait_socket
from shared_cpu_pool import UnresolvedOwnership


def child(store,pin,command,codes):
    if type(codes) is not tuple or any(type(n) is not int for n in codes) or codes not in ((0,),(1,2)):
        raise ValueError('only success or designated normal refusal set required')
    value=store.read_json(pin['name'],expected_sha256=pin['sha256'])
    raw=store.read(pin['name'],expected_sha256=pin['sha256'])
    if len(raw)!=pin['bytes'] or set(value)!={'schema','outcome','streams','observation','external_server_audit_required','resource_release_authorized'}:
        raise ValueError('exact retained batch child record required')
    if value['schema']!='unison-batch-child/2' or value['external_server_audit_required'] is not True or value['resource_release_authorized'] is not False:
        raise ValueError('non-releasing batch child schema required')
    out=dict(value['outcome'])
    if set(out)!={'command','returncode','timed_out','capture_truncated','client_cleanup','aggregate_or_parent_terminal_proved','io_cpu_release_authorized'}:
        raise ValueError('exact retained outcome fields required')
    code=out['returncode'];c=out['client_cleanup']
    if (out['command']!=command or type(code) is not int or code not in codes or out['timed_out'] is not False
            or out['capture_truncated'] is not False or out['aggregate_or_parent_terminal_proved'] is not False
            or out['io_cpu_release_authorized'] is not False):raise ValueError('normal designated exit required')
    if (type(c) is not dict or set(c)!={'pid','returncode','reaped','hard_kill_required','other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
            or type(c['pid']) is not int or not 0<c['pid']<2**31 or type(c['returncode']) is not int or c['returncode']!=code
            or c['reaped'] is not True or c['hard_kill_required'] is not False
            or c['other_group_members_absent_before_reap'] is not True or c['group_cleanup_before_leader_reap'] is not True):
        raise ValueError('actual reap/group proof required independent of exit')
    if type(value['streams']) is not dict or set(value['streams'])!={'stdout','stderr'}:raise ValueError('both raw captures required')
    for key in ('stdout','stderr'):
        data=read(store,value['streams'][key])
        if len(data)>4*1048576:raise ValueError('capture exceeds batch bound')
        out[key]=data.decode('utf8','replace')
    read_observation(store,value['observation'],c['pid'])
    return out


def finish(handle,deadline,store,command,codes):
    try:pin=handle.finish(deadline)
    except ValueError:
        # Call publishes all raw/capture/observation evidence BEFORE its strict
        # zero-only audit. Missing/partial record is never a known negative.
        if handle.record is None:raise
        pin=handle.record
    child(store,pin,command,codes)
    return pin


def audit(store,evidence,*,client_command,proxy_command,server_command):
    if type(evidence) is not dict or set(evidence)!={'client','proxy','server_frame'}:raise ValueError('exact refusal pair fields required')
    client=child(store,evidence['client'],client_command,(1,2));proxy=child(store,evidence['proxy'],proxy_command,(0,))
    frame=json.loads(read(store,evidence['server_frame']),object_pairs_hook=unique)
    fields={'schema','server_command','server_pid','server_returncode','server_reaped','server_group','input_eof_forwarded','output_eof_forwarded','forwarded_protocol_bytes','parent_group_audit_required','sdk_helper_audit_required','resource_release_authorized'}
    cp=client['client_cleanup']['pid'];pp=proxy['client_cleanup']['pid']
    if (type(frame) is not dict or set(frame)!=fields or frame['schema']!='unison-retained-merge-proxy/1'
            or frame['server_command']!=server_command or type(frame['server_pid']) is not int or not 0<frame['server_pid']<2**31
            or len({cp,pp,frame['server_pid']})!=3 or type(frame['server_returncode']) is not int or frame['server_returncode'] not in (0,1,2)
            or frame['server_reaped'] is not True or type(frame['server_group']) is not int or frame['server_group']!=pp
            or frame['input_eof_forwarded'] is not True or frame['output_eof_forwarded'] is not True
            or frame['parent_group_audit_required'] is not True or frame['sdk_helper_audit_required'] is not True
            or frame['resource_release_authorized'] is not False):raise ValueError('refusal native command/group/EOF binding differs')
    counts=frame['forwarded_protocol_bytes']
    if type(counts) is not dict or set(counts)!={'client_to_server_bytes','server_to_client_bytes'} or any(type(n) is not int or not 0<n<2**63 for n in counts.values()):raise ValueError('positive protocol byte counts required')
    text=client['stdout']+client['stderr']
    if 'no saved common base is available' not in text or 'Uncaught unix error' in text:raise ValueError('specific refusal diagnostic required')
    return dict(client_pid=cp,proxy_pid=pp,server_pid=frame['server_pid'],client_exit=client['returncode'],server_exit=frame['server_returncode'],resource_release_authorized=False)


def invoke(client_command,client_environment,*,proxy_command,proxy_environment,server_command,socket_path,deadline,pass_fds,store,name,read_proxy_bytes):
    if re.fullmatch('c[01]-5',name or '') is None or not time.monotonic()<deadline<float('inf') or os.path.lexists(socket_path):
        raise ValueError('only fresh ten-stage missing-base call admitted')
    proxy=client=None;evidence={}
    try:
        proxy=launch(proxy_command,proxy_environment,pass_fds=pass_fds,store=store,name=name+'-proxy')
        wait_socket(socket_path,proxy.pending,deadline)
        client=launch(client_command,client_environment,pass_fds=pass_fds,store=store,name=name+'-client')
        evidence['client']=finish(client,deadline,store,client_command,(1,2))
        evidence['proxy']=finish(proxy,deadline,store,proxy_command,(0,))
        raw=read_proxy_bytes()
        if type(raw) is not bytes or not 0<len(raw)<=65536:raise ValueError('bounded proxy record required')
        evidence['server_frame']=publish(store,name+'-server-frame',raw)
        joined=audit(store,evidence,client_command=client_command,proxy_command=proxy_command,server_command=server_command)
        return store.write(name+'-pair.json',dict(schema='unison-archive-refusal-pair/1',evidence=evidence,audit=joined))
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('archive refusal unresolved; retain every actual peer handle')
        if retained is not error:retained.original_failure=error
        retained.batch_pair_handles=[h for h in (proxy,client) if h is not None];retained.batch_pair_evidence=evidence
        if retained is error:raise
        raise retained from error
