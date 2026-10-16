"""Independent finite receiving-comparison prefix/case audit; no release power."""
from pathlib import Path
import sys
import math
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from invocation_journal import audit_attempted
from sdk_throughput.plan import comparison,row_matches
from sdk_multifile.result import audit as case_audit
from sdk_multifile.receipts import sdk_audit
from live_records import parse as parse_live


def require(value,message):
    if not value:raise ValueError(message)


def audit(result,plan,*,raw_proxy_receipts):
    scheduled=comparison(plan['binaries'],plan['tool'],plan['workspace'])['rows']
    require(type(result) is dict and result.get('schema')=='unison-sdk-receiving-comparison-worker/1'
            and type(result.get('complete')) is bool,'typed comparison worker result required')
    require(result.get('semantic_eligibility_claimed') is False and result.get('pixel_equivalence_claimed') is False
            and result.get('throughput_qualified') is False,'no result-scope escalation')
    entries=result.get('invocations');rows=result.get('cases');complete=result['complete']
    require(type(entries) is list and len(entries)<=24 and type(rows) is list and len(rows)<=24,'bounded finite prefix required')
    require(type(raw_proxy_receipts) is list and len(raw_proxy_receipts)==len(entries),'separate raw proxy for every attempted row required')
    if not complete:require(type(result.get('failure')) is str and result['failure'],'original failed-result reason required')
    if not entries:
        require(not complete and result.get('phase')=='PREPARING_NO_CALL' and not rows,'possible call or active preparation is not a known empty prefix')
        return dict(functional_status='FAILED',attempted_cli_invocations=0,sdk_helpers_settled=0,resource_release_authorized=False)
    require(len(rows)==len(entries) and result.get('phase')==('FINISHED' if complete else 'CALL_MAY_HAVE_STARTED'),'case count or phase differs')
    lifecycle=audit_attempted(result);proofs=[];measurements=[]
    for i,(entry,row,proxy) in enumerate(zip(entries,rows,raw_proxy_receipts)):
        expected=scheduled[i]
        require(type(row) is dict and row_matches(row.get('schedule'),expected),'exact scheduled prefix/order required')
        require(entry['command']==expected['command'] and entry['identity']==dict(label=expected['label'],mode='semantic',
                workers=expected['endpoint_workers'],directory=expected['directory'],stage='seed'),'exact command/worker identity required')
        out=entry['outcome'];case=row.get('case')
        require(type(case) is dict and case.get('outcome')==out and out['proxy']==proxy,'case/journal/raw proxy binding differs')
        require(all(type(out.get(k)) is str and len(out[k])<=4*1048576 for k in ('stdout','stderr','supervisor_output')),'bounded raw diagnostics required')
        if i<len(entries)-1:require(case.get('complete') is True,'worker continued after failed case')
        log=out['stdout']+out['stderr']+out['supervisor_output']
        if proxy['server_command'] is None:
            require(not complete and not sdk_audit.records.parse(log) and not sdk_audit.records.parse_groups(log) and not parse_live(log)
                    and case.get('complete') is False and 'helper_settlements' not in case and 'validation' not in case,
                    'no-server prefix contradicts helper evidence')
            continue  # audit_attempted consumed the full pinned no-creation frame.
        proof=case_audit(case,sources=plan['sources'],server_pid=proxy['server_pid']);proofs.append(proof)
        if case['complete']:
            require(out['returncode']==0 and out['supervisor_cleanup']['returncode']==0 and proxy['server_returncode']==0
                    and proxy.get('fault') is None and out.get('fault') is None and proxy['pump_errors']==[],
                    'completed case contradicts failed transport')
            wall=out.get('wall_seconds')
            require(type(wall) is float and math.isfinite(wall) and wall>0,'finite measured call wall time required')
            measurements.append(dict(index=i,label=expected['label'],endpoint_workers=expected['endpoint_workers'],phase=expected['phase'],wall_seconds=wall))
        if complete:require(proof['functional_status']=='PASSED','complete comparison contains failed case')
    if complete:require(len(entries)==len(proofs)==24 and 'failure' not in result,'complete exact24row matrix required')
    return dict(lifecycle,functional_status='PASSED' if complete else 'FAILED',sdk_helpers_settled=sum(p['sdk_helpers_settled'] for p in proofs),
                verified_case_measurements=measurements,measured_rows=sum(m['phase']=='measured' for m in measurements),
                aggregate_parent_fd_closure_proved=False,receiving_bytes_reverified=False,resource_release_authorized=False,
                throughput_qualified=False)
