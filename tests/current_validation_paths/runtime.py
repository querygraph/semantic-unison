"""Complete original 21-case worker, called only by an admitted retained owner.

No CLI, token acquisition, arbitrary callback selected by a plan, or resource
release here. Inherited IO/CPU copies stay held through the actual worker exit
and independent parent audit. Unknown metadata/process ownership never unwinds.
"""
import hashlib,time
from copy import deepcopy
from pathlib import Path
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import exact
from current_validation_paths.contract import plan as case_plan
from current_validation_paths.files import Files
from current_validation_paths.original import load
from current_validation_paths.session import factory as session_factory
from current_validation_paths.cancel_case import factory as cancel_factory
from current_validation_paths.invoke import Actor


def prefix_settled(actor,files,error):
    # This is only a worker-local candidate. The owner must independently re-read
    # every raw attempted call before retiring inherited resource descriptions.
    return (not isinstance(error,UnresolvedOwnership) and actor.retained is None and files.retained is None
        and actor.active is None and len(actor.calls)==actor.attempts)


def case_summary(row,calls,result):
    helpers=sum(len(c['verdict']['helper_observations']) for c in calls)
    external=sum(len(c['verdict'].get('external_observations',[])) for c in calls)
    if len(calls)!=row['max_CLI_calls'] or helpers!=row['max_fake_validator_calls']:
        raise ValueError('original named case omitted or added a CLI/fake-validator call')
    return dict(index=row['index'],family=row['family'],arguments=row['arguments'],name=row['name'],
        calls=len(calls),fake_validators=helpers,external_children=external,original_result=result,
        receiving_case_assertions_passed=True,resource_release_authorized=False)


def run(packet,store,resources,deadline):
    """Trusted source composition only; fixture doubles live in original controls."""
    legacy=packet['legacy_source'];expected_path=packet['repository']+'/tests/validation_paths/run.py'
    if legacy['path']!=expected_path:raise ValueError('exact original legacy source reference required')
    raw=read_bytes(expected_path,256*1024)
    if len(raw)!=legacy['bytes'] or hashlib.sha256(raw).hexdigest()!=legacy['sha256']:raise ValueError('original case source changed')
    source=raw.decode('utf-8');expected=case_plan(source,packet['workspace'],packet['compiler'])
    if not exact(packet['rows'],expected['rows']) or not exact(packet['limits'],expected['limits']):
        raise ValueError('complete original ordered cases/limits required')
    if not time.monotonic()<deadline<float('inf'):raise ValueError('fresh inherited worker observation required')
    actor=Actor(packet,resources,deadline)
    files=Files(packet['workspace'],(store.identity['device'],store.identity['inode']))
    selected={};completed=[];failed=None
    roots={row['directory']:row for row in packet['rows']}
    def persist(event,session,value):
        if event not in ('INTENT','ACCEPTED'):raise ValueError('exact named session event required')
        row=roots[str(session.root)]
        store.write('case-%02d-seq-%03d-%s.json'%(row['index'],session.sequence,event),value)
    def make_session(legacy_class):
        cls=session_factory(legacy_class,files=files,binary=packet['binary']['path'],repository=packet['repository'],
            invoke=actor.invoke,audit=actor.audit,interrupt=actor.interrupt,persist=persist)
        selected['session']=cls;return cls
    def cancelled(root,binary,policy):return cancel_factory(selected['session'])(root,binary,policy)
    try:
        functions=load(source,session_factory=make_session,cancel_actor=cancelled,path_factory=lambda _:files.Path,
            filename=expected_path)['functions']
        for row in packet['rows']:
            if time.monotonic()>=deadline:raise TimeoutError('no new case after observation deadline')
            if files.Path(row['directory']).exists():raise ValueError('new original case workspace must be absent')
            store.write('case-%02d-START.json'%row['index'],dict(row=row,resource_release_authorized=False))
            try:
                result=functions[row['family']](files.Path(row['directory']),packet['binary']['path'],*row['arguments'])
                calls=[value for value in actor.calls.values() if value['root']==row['directory']]
                summary=case_summary(row,calls,result)
                store.write('case-%02d-RESULT.json'%row['index'],summary);completed.append(summary)
            except BaseException as error:
                if not prefix_settled(actor,files,error):raise
                failed=dict(index=row['index'],family=row['family'],name=row['name'],error=repr(error),
                    ordinary_case_failure_only=True,worker_local_settled_candidate=True,
                    independent_parent_raw_audit_required=True,resource_release_authorized=False)
                store.write('case-%02d-FAILED.json'%row['index'],failed)
                break
        if failed is None:
            try:
                if actor.attempts!=69 or len(completed)!=21:raise ValueError('full original case/call inventory differs')
                if sum(row['fake_validators'] for row in completed)!=54:raise ValueError('full fake-validator inventory differs')
                kinds=[item['expected']['kind'] for call in actor.calls.values() for item in call['verdict'].get('external_observations',[])]
                if kinds.count('copy')!=9 or kinds.count('merge')!=7:raise ValueError('all original producer/merge children required')
            except BaseException as error:
                if not prefix_settled(actor,files,error):raise
                failed=dict(index=None,family='whole-inventory',name='whole-inventory',error=repr(error),
                    ordinary_case_failure_only=True,worker_local_settled_candidate=True,
                    independent_parent_raw_audit_required=True,resource_release_authorized=False)
                store.write('INVENTORY-FAILED.json',failed)
        saved=dict(complete=failed is None,cases=completed,failed_case=failed,calls={str(i):{k:deepcopy(v) for k,v in call.items() if k not in ('verdict','intent')} for i,call in actor.calls.items()},attempted_CLI_calls=actor.attempts,
            actual_SDK_calls=0,actual_Photo_calls=0,parent_terminal_proved=False,resource_release_authorized=False,
            independent_parent_raw_audit_required=True)
        store.write('RESULT.json',saved)
        actor.close();files.close()
        return dict(result=saved,worker_metadata_closed=True,resource_release_authorized=False)
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('named receiving worker unresolved; retain every actual owner')
        if retained is not error:retained.original_failure=error
        retained.named_runtime_actor=actor;retained.named_runtime_files=files
        excluded=set(getattr(retained,'uncertain_fds',()))
        known=[*retained.retained_fds,*[r['fd'] for r in resources]]
        if not files.closed:known.append(files.fd)
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        if retained is error:raise
        raise retained from error
