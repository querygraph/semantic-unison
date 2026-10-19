"""Trusted-adapter serial kernel; no admission/child/lock/release authority.

Every invoked call has durable intent first. Expected rejection is a completed
case only after independent raw transport/finding and destination audits. Any
unexpected condition retains the original carrier and stops new calls.
"""
from copy import deepcopy
import hashlib,json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.plan import require,digest
from sdk_negative_receiving.plan import schedule


def execute(binaries,tool,workspace,*,prepare,invoke,audit_transport,verify_outputs,persist):
    rows=schedule(binaries,tool,workspace)['rows'];results=[];events=[];active=None;outcome=None
    def save():
        persist(dict(events=deepcopy(events),results=deepcopy(results),
                     resource_release_authorized=False,parent_audit_required=True))
    try:
        save()
        for index,row in enumerate(rows):
            active=dict(index=index,codec=row['codec'],policy=row['policy'],stage=row['stage'])
            candidate=prepare(deepcopy(row))
            require(type(candidate) is dict and set(candidate)=={'sha256','bytes'}
                and type(candidate['bytes']) is int and 0<candidate['bytes']<=128*1048576,
                'bounded exact phase candidate required')
            digest(candidate['sha256'])
            command_sha=hashlib.sha256(json.dumps(row['command'],ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
            events.append(dict(event='INTENT',**active,command_sha256=command_sha,candidate=deepcopy(candidate)))
            save() # No call until durable intent completes.
            outcome=invoke(deepcopy(row))
            audited=audit_transport(deepcopy(row),outcome,deepcopy(candidate))
            require(type(audited) is dict and audited.get('resource_release_authorized') is False,
                    'non-releasing raw transport/finding audit required')
            publication=verify_outputs(deepcopy(row),deepcopy(candidate))
            require(type(publication) is dict and publication.get('resource_release_authorized') is False,
                    'non-releasing exact output audit required')
            results.append(dict(**active,candidate=deepcopy(candidate),transport=deepcopy(audited),
                                publication=deepcopy(publication)))
            events.append(dict(event='ACCEPTED',**active,expected_client_exit=row['expected_client_exit']))
            save();active=None;outcome=None
        require(len(results)==12 and len(events)==24,'exact complete negative receiving matrix required')
        return dict(complete=True,results=results,events=events,
                    parent_audit_required=True,resource_release_authorized=False)
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'negative receiving preparation/call/audit unresolved; retain all resource owners')
        if retained is not error:retained.original_failure=error
        retained.negative_receiving_state=dict(active=deepcopy(active),outcome=outcome,
            results=deepcopy(results),events=deepcopy(events))
        if retained is error:raise
        raise retained from error
