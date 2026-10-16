"""Join exact CLI journal, separately read proxy frames and two-candidate cases."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from invocation_journal import audit_attempted
from sdk_multifile.plan import plan as command_plan
from sdk_multifile.result import audit as case_audit
from sdk_multifile.receipts import sdk_audit
from live_records import parse as parse_live


def require(value,message):
    if not value:raise ValueError(message)


def audit(result,plan,*,raw_proxy_receipts):
    require(result.get('schema')=='unison-sdk-multifile-worker/1'
            and type(result.get('complete')) is bool,'typed multi-file worker result required')
    require(result.get('semantic_eligibility_claimed') is False
            and result.get('pixel_equivalence_claimed') is False,'no semantic/pixel escalation')
    entries=result.get('invocations');rows=result.get('cases');complete=result['complete']
    require(type(entries) is list and len(entries)<=2 and type(rows) is list and len(rows)<=2,
            'bounded exact two-case journal required')
    require(type(raw_proxy_receipts) is list and len(raw_proxy_receipts)==len(entries),
            'every attempted call requires its independently read proxy frame')
    if not complete:require(type(result.get('failure')) is str and result['failure'],'original worker failure required')
    if not entries:
        require(not complete and result.get('phase')=='PREPARING_NO_CALL' and not rows,
                'zero-call preparation cannot cover possible calls or active case preparation')
        return dict(functional_status='FAILED',attempted_cli_invocations=0,sdk_helpers_settled=0,
                    aggregate_parent_fd_closure_proved=False,resource_release_authorized=False)
    require(len(rows)==len(entries) and result.get('phase')==('FINISHED' if complete else 'CALL_MAY_HAVE_STARTED'),
            'case/journal count or phase differs')
    lifecycle=audit_attempted(result);proofs=[]
    for index,(entry,row,raw_proxy) in enumerate(zip(entries,rows,raw_proxy_receipts)):
        label=('stock','ox')[index];directory=Path(plan['workspace'])/label
        expected=command_plan(plan['binaries'][label],plan['tool'],directory)['command']
        require(entry['identity']==dict(label=label,mode='semantic',workers=3,directory=str(directory),stage='seed')
                and entry['command']==expected,'exact ordered compiler/namespace/flags required')
        out=entry['outcome'];case=row.get('case')
        require(row.get('label')==label and type(case) is dict and case.get('outcome')==out
                and out['proxy']==raw_proxy,'case/journal/raw proxy binding differs')
        log=out['stdout']+out['stderr']+out['supervisor_output']
        if raw_proxy['server_command'] is None:
            require(not complete and not sdk_audit.records.parse(log)
                    and not sdk_audit.records.parse_groups(log) and not parse_live(log)
                    and case.get('complete') is False and 'helper_settlements' not in case
                    and 'validation' not in case,'no-server branch contradicts SDK observations')
            # audit_attempted requires the pinned proxy's full pre-creation
            # protocol, not just a null PID. No helper absence inference alone.
            continue
        proof=case_audit(case,sources=plan['sources'],server_pid=raw_proxy['server_pid'])
        proofs.append(proof)
        if complete:
            require(proof['functional_status']=='PASSED' and out['returncode']==0
                    and out['supervisor_cleanup']['returncode']==0 and raw_proxy['server_returncode']==0
                    and raw_proxy.get('fault') is None and out.get('fault') is None
                    and raw_proxy['pump_errors']==[],'complete matrix contradicts failed call')
    if complete:require(len(entries)==len(proofs)==2 and 'failure' not in result,'two complete compiler calls required')
    return dict(lifecycle,functional_status='PASSED' if complete else 'FAILED',
                sdk_helpers_settled=sum(p['sdk_helpers_settled'] for p in proofs),case_audits=proofs,
                aggregate_parent_fd_closure_proved=False,receiving_bytes_reverified=False,
                resource_release_authorized=False)
