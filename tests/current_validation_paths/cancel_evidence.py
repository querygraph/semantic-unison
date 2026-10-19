"""Pure cancellation-specific proof; normal validation rejection remains exit2."""
from current_validation_paths.evidence import _audit
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.plan import require


def cancelled_client(out,command,code):
    require(type(code) is int and code==3,'current uitext Sys.Break fatalExit3 required')
    require(type(out) is dict and set(out)=={'command','returncode','timed_out','capture_truncated','stdout','stderr',
        'client_cleanup','aggregate_or_parent_terminal_proved','io_cpu_release_authorized'},'exact cancellation child capture required')
    require(exact(out['command'],command) and type(out['returncode']) is int and out['returncode']==3
        and out['timed_out'] is False and out['capture_truncated'] is False
        and out['aggregate_or_parent_terminal_proved'] is False and out['io_cpu_release_authorized'] is False,
        'actual normal exit3 cancellation child required')
    c=out['client_cleanup']
    require(type(c) is dict and set(c)=={'pid','returncode','reaped','hard_kill_required',
        'other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
        and type(c['pid']) is int and 0<c['pid']<2**31 and type(c['returncode']) is int and c['returncode']==3
        and c['reaped'] is True and c['hard_kill_required'] is False and c['other_group_members_absent_before_reap'] is True
        and c['group_cleanup_before_leader_reap'] is True,'cancelled client/group unresolved')
    for stream in ('stdout','stderr'):
        require(type(out[stream]) is str and len(out[stream].encode())<=262144,'complete bounded cancellation diagnostics required')
    return c['pid']


def audit(pair,*,cancellation,client_command,proxy_command,server_command,raw_proxy_bytes,expected_helpers):
    require(type(cancellation) is dict and set(cancellation)=={'fixture_observation','client_interrupt'},'exact saved signal/fixture evidence required')
    observed=cancellation['fixture_observation'];sent=cancellation['client_interrupt']
    require(type(observed) is dict and set(observed)=={'helper','client_pid','candidate_bytes_verified',
        'previous_destination_preserved','source_preserved','helper_settlement_proved','resource_release_authorized'}
        and type(observed['client_pid']) is int and observed['candidate_bytes_verified'] is True
        and observed['previous_destination_preserved'] is True and observed['source_preserved'] is True
        and observed['helper_settlement_proved'] is False and observed['resource_release_authorized'] is False,
        'exact non-settlement fixture observation required')
    client_pid=cancelled_client(pair['client'],client_command,3)
    require(exact(sent,dict(pid=client_pid,signal=2,sent=True,client_reaped_before_signal=False,resource_release_authorized=False))
        and observed['client_pid']==client_pid,'signal must target this exact unreaped direct client')
    require(type(expected_helpers) is list and len(expected_helpers)==1,'one receiving-client helper required')
    entry=expected_helpers[0];helper=observed['helper']
    require(type(helper) is dict and entry==dict(endpoint='client',pid=helper.get('pid'),candidate_sha256=helper.get('sha256'),
        candidate_bytes=helper.get('size'),mode='hang',outcome='cancelled'),'pre-signal helper must match actual raw cancelled helper')
    result=_audit(pair,client_command=client_command,proxy_command=proxy_command,server_command=server_command,
        raw_proxy_bytes=raw_proxy_bytes,expected_client_exit=3,expected_helpers=expected_helpers,terminal_audit=cancelled_client)
    require('Update propagation interrupted' in result['log'] and 'Aborted by user request' in result['log'],
        'both original native cancellation diagnostics required')
    result['client_interrupt']=sent;result['cancellation_fixture']=observed
    return result
