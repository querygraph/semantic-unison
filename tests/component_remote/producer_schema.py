"""Exact direct-child producer schemas for future component RPC audits.

This predicate checks successful cleanup shapes, not command binding, all raw
ledgers, current input bytes, parent terminal or resource release. The complete
functional auditor supplies those other checks. No cancellation field is added
or defaulted when its actual producer does not emit one.
"""
from shared_cpu_pool import require

CLIENT_KEYS={'pid','returncode','reaped','hard_kill_required',
 'other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
SUPERVISOR_KEYS={'pid','returncode','reaped','other_group_members_absent_before_reap',
 'members_before_reap','timed_out','scope','group_cleanup_before_leader_reap'}

def successful_call(run):
    """Validate the actual pinned producer schemas; do not invent cancel_reason."""
    require(run['returncode']==0 and type(run['returncode']) is int and
      run['timed_out'] is False and run['capture_truncated'] is False and
      run['supervisor_capture_truncated'] is False,'non-successful RPC call')
    client=run['client_cleanup'];supervisor=run['supervisor_cleanup']
    require(set(client)==CLIENT_KEYS and set(supervisor)==SUPERVISOR_KEYS,
            'actual client/supervisor producer schema required')
    for value in (client,supervisor):
        require(type(value['pid']) is int and value['pid']>0 and
          type(value['returncode']) is int and value['returncode']==0 and
          value['reaped'] is True and value['group_cleanup_before_leader_reap'] is True and
          value['other_group_members_absent_before_reap'] is True,'normal direct wait/group proof required')
    require(client['hard_kill_required'] is False and supervisor['timed_out'] is False and
      supervisor['scope']=='owned group only; separate sessions require independently audited proofs',
      'normal producer settlement required')
    members=supervisor['members_before_reap']
    require(type(members) is list and all(set(row)=={'pid','state'} and
      row['pid']==supervisor['pid'] and type(row['state']) is str and row['state'].startswith('Z')
      for row in members),'pre-reap supervisor census differs')
    proxy=run['proxy'];native=proxy['server_cleanup']
    require(native is not None and proxy['server_returncode']==0 and proxy['fault'] is None and
      proxy['pump_errors']==[] and proxy['input_pump_joined'] is True and
      native['returncode']==0 and native['reaped'] is True and
      native['cancel_reason'] is None and native['hard_kill_required'] is False,
      'native server wait/cancellation/pump proof missing')

