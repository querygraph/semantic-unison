"""Reparse returned two-candidate case records; CLI/FD/output audit is separate."""
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sdk_multifile.receipts import audit as verdict,BUILD
from combined import settlements,sdk_audit


def require(value,message):
    if not value:raise ValueError(message)


def audit(result,*,sources,server_pid):
    require(type(sources) is list and len(sources)==2,'two independent source bindings required')
    require([s.get('candidate_id') for s in sources]==['uncompressed.dng','jpeg.dng'],
            'fixed two-candidate order required')
    for source in sources:
        require(set(source)=={'candidate_id','sha256','bytes'}
                and type(source['bytes']) is int and 0<source['bytes']<=128*1048576
                and type(source['sha256']) is str and re.fullmatch('[0-9a-f]{64}',source['sha256']),
                'typed bounded source identity required')
    require(type(result) is dict and result.get('schema')=='unison-sdk-multifile-case/1'
            and type(result.get('complete')) is bool and result.get('sources')==sources
            and result.get('semantic_eligibility_claimed') is False
            and result.get('pixel_equivalence_claimed') is False,'typed source-bound non-escalating case required')
    complete=result['complete']
    if not complete:require(type(result.get('failure')) is str and result['failure'],'original failed-case diagnostic required')
    if 'outcome' not in result:
        require(not complete and result.get('phase')=='PREPARING_NO_CALL'
                and 'helper_settlements' not in result and 'validation' not in result,
                'empty prefix after possible dispatch is unresolved')
        return dict(functional_status='FAILED',sdk_helpers_settled=0,no_call_preparation=True,
                    cli_worker_fd_closure_proved=False,receiving_bytes_reverified=False)
    out=result['outcome']
    require(type(out) is dict and type(server_pid) is int and 0<server_pid<2**31
            and out.get('proxy',{}).get('server_pid')==server_pid,'independent server binding required')
    require(all(type(out.get(k)) is str and len(out[k])<=4*1048576
                for k in ['stdout','stderr','supervisor_output']),'bounded raw call diagnostics required')
    log=out['stdout']+out['stderr']+out['supervisor_output']
    records=sdk_audit.records.parse(log);expected=[]
    for source in sources:
        matched=[r for r in records if r.candidate_sha256==source['sha256'] and r.candidate_bytes==source['bytes']]
        require(len(matched)==1 and matched[0].pid is not None,'unknown or duplicate candidate helper')
        expected.append(dict(source,helper_pid=matched[0].pid))
    proof=settlements(log,expected=expected)
    require(result.get('helper_settlements')==proof,'summary helper proof differs from raw diagnostics')
    if complete:
        require(result.get('phase')=='VERIFIED_TWO_GENERATED_CANDIDATES' and 'failure' not in result
                and type(out.get('returncode')) is int and out['returncode']==0
                and out.get('timed_out') is False and out.get('capture_truncated') is False
                and out.get('supervisor_capture_truncated') is False,'complete functional case must succeed')
        require(result.get('validation')==verdict(log,expected=expected,owner_pid=server_pid,build_id=BUILD),
                'stored SDK verdict/overlap differs from raw evidence')
    else:require(result.get('phase')=='HELPER_SETTLEMENT_RECORDED','failed known prefix lacks helper settlement phase')
    return dict(functional_status='PASSED' if complete else 'FAILED',sdk_helpers_settled=2,
                no_call_preparation=False,cli_worker_fd_closure_proved=False,
                receiving_bytes_reverified=False,resource_release_authorized=False)
