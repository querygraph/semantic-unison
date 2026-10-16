"""Audit every returned direct SDK call before parent aggregate/FD settlement."""
from shared_plan import shared_matrix
from shared_result import audit as functional
from plan import require

def audit(result,*,reference,experimental,fixtures,memory_bytes,observation_contract=None):
    cases=shared_matrix(reference,experimental,fixtures,memory_bytes)['cases']
    require(type(result) is dict and result.get('schema')=='unison-shared-sdk-kernel/1'
        and type(result.get('complete')) is bool and result.get('resource_release_authorized') is False,
        'exact typed non-releasing result required')
    complete=result['complete'];entries=result.get('invocations');rows=result.get('rows')
    require(type(entries) is list and len(entries)<=12 and type(rows) is list and len(rows)<=len(entries),
        'bounded direct call journal/rows required')
    if not entries:
        require(not complete and result.get('phase')=='PREPARING_NO_CALL'
            and type(result.get('failure')) is str and result['failure'] and not rows,'explicit failed no-call phase required')
    else:
        require(result.get('phase')==('FINISHED' if complete else 'CALL_MAY_HAVE_STARTED'),'call phase differs')
    pids=set();observations=[]
    for i,(entry,case) in enumerate(zip(entries,cases)):
        require(type(entry) is dict and type(entry.get('index')) is int and entry['index']==i
            and entry.get('state')=='OUTCOME' and entry.get('command')==case['command']
            and entry.get('identity')==dict(index=i+1,codec=case['codec'],backend=case['backend']),
            'unknown/reordered/unbound SDK invocation')
        out=entry.get('outcome');require(type(out) is dict,'actual returned outcome required')
        child=out.get('client_cleanup',{})
        require(out.get('command')==case['command'] and type(out.get('returncode')) is int
            and out.get('timed_out') is False and type(out.get('capture_truncated')) is bool
            and type(child.get('pid')) is int and child['pid']>0 and child['pid'] not in pids
            and child.get('reaped') is True and type(child.get('returncode')) is int
            and child['returncode']==out['returncode'] and child.get('other_group_members_absent_before_reap') is True
            and child.get('group_cleanup_before_leader_reap') is True and child.get('hard_kill_required') is False,
            'direct child/group/capture settlement unknown')
        require(type(out.get('stdout')) is str and len(out['stdout'])<=262144
            and type(out.get('stderr')) is str and len(out['stderr'])<=262144,'bounded raw diagnostics required')
        pids.add(child['pid'])
        if observation_contract is None:
            require('process_observations' not in out,'unrequested process observation records')
        else:
            from shared_observed import audit_observed
            observations.append(audit_observed(out,observation_contract))
        if i<len(rows):require(rows[i]==dict(index=i+1,command=case['command'],outcome=out),'functional row differs from journal')
    if complete:
        require(len(entries)==len(rows)==12 and 'failure' not in result,'full matrix required')
        value=functional(reference,experimental,fixtures,memory_bytes,rows)
    else:
        require(type(result.get('failure')) is str and result['failure'],'original failure required')
        value=None
    value_return=dict(attempted_direct_calls=len(entries),all_attempted_direct_children_and_groups_settled=True,
        functional_status='PASSED' if complete else 'FAILED',functional_audit=value,
        aggregate_parent_fd_closure_proved=False,resource_release_authorized=False)
    if observation_contract is not None:value_return['process_observation_audits']=observations
    return value_return
