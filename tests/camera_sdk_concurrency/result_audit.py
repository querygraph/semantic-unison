"""Parent-side result audit before aggregate reap; never releases resources."""
import hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'bench/sync'))
from invocation_journal import audit_attempted
from command import command
from synthetic_case import FILES,BUILD
from combined import settlements,audit_success,sdk_audit
from live_records import parse as parse_live


def require(value,message):
    if not value:raise ValueError(message)


def audit(result,plan,workspace):
    require(result['schema']=='unison-concurrent-synthetic-worker/1'
            and type(result['complete']) is bool,'typed synthetic worker result required')
    require(result['sdk_validation_claimed'] is False and result['semantic_eligibility_claimed'] is False,
            'synthetic control cannot claim SDK or semantic qualification')
    require(plan['workspace']==str(workspace) and plan['tool']['build_id']==BUILD,
            'exact synthetic namespace/tool scope required')
    rows=result['cases']
    require(type(rows) is list and len(rows)<=2,'bounded case rows required')
    if result['complete']:require(len(rows)==2,'two complete case rows required')
    entries=result['invocations']
    require(type(entries) is list and len(entries)<=2,'bounded seed census required')
    if not entries:
        require(not result['complete'] and result['phase']=='PREPARING_NO_CALL'
                and type(result.get('failure')) is str and bool(result['failure']),
                'zero-call preparation proof required')
        return dict(functional_status='FAILED',attempted_cli_invocations=0,helper_settlements=[])
    lifecycle=audit_attempted(result)
    if not result['complete']:
        require(type(result.get('failure')) is str and bool(result['failure']),'failed prefix lacks original failure')
    proofs=[];validations=[]
    for index,entry in enumerate(entries):
        label=('stock','ox')[index];d=Path(workspace)/label
        require(entry['identity']==dict(label=label,mode='semantic',workers=3,directory=str(d),stage='seed'),
                'ordered single-seed compiler identity differs')
        contract=command(d,binary=plan['binaries'][label],tool=plan['tool'])
        require(entry['command']==contract['argv'],'exact receiving command differs')
        outcome=entry['outcome'];log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
        if outcome['proxy']['server_command'] is None:
            require(not result['complete'] and not sdk_audit.records.parse(log)
                    and not sdk_audit.records.parse_groups(log) and not parse_live(log),
                    'no-server prefix contradicts helper observations')
            continue # audit_attempted already requires exact pinned no-creation proof.
        processes=sdk_audit.records.parse(log);expected=[]
        for name,data in FILES.items():
            digest=hashlib.sha256(data).hexdigest()
            matches=[p for p in processes if p.candidate_sha256==digest and p.candidate_bytes==len(data)]
            require(len(matches)==1 and matches[0].pid is not None,'two exact helper identities required')
            expected.append(dict(candidate_id=name,helper_pid=matches[0].pid,sha256=digest,bytes=len(data)))
        proofs.extend(settlements(log,expected=expected))
        if result['complete']:
            require(outcome['returncode']==0 and outcome['supervisor_cleanup']['returncode']==0
                    and outcome['proxy']['server_returncode']==0 and not outcome['timed_out']
                    and not outcome['capture_truncated'] and not outcome['supervisor_capture_truncated']
                    and outcome['proxy'].get('fault') is None and outcome.get('fault') is None
                    and outcome['proxy']['pump_errors']==[],'complete worker contradicts failed CLI')
            verdict=audit_success(log,expected=expected,
                owner_pid=outcome['proxy']['server_pid'],build_id=BUILD)
            row=rows[index];case=row['case']
            require(row['label']==label and case['complete'] is True
                    and case['phase']=='VERIFIED_TWO_SYNTHETIC_CANDIDATES'
                    and case['sdk_validation_claimed'] is False
                    and case['semantic_eligibility_claimed'] is False
                    and case['outcome']==outcome and case['validation']==verdict
                    and case['sources']==[dict(candidate_id=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)) for name,data in FILES.items()],
                    'complete case differs from independently audited call')
            validations.append(verdict)
    if result['complete']:
        require(len(entries)==2 and len(proofs)==4 and result['phase']=='FINISHED',
                'two complete compiler cases/four helpers required')
    return dict(lifecycle,functional_status='PASSED' if result['complete'] else 'FAILED',
                helper_settlements=proofs,validations=validations,
                all_pairs_overlap=bool(validations) and all(v['overlap_observed'] for v in validations),
                aggregate_parent_fd_closure_proved=False)
