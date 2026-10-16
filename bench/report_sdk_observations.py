"""Reparse saved SDK/probe evidence; no SDK, probe or payload execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests/sdk_host_matrix'))
from shared_parent_audit import audit


def read_pin(path,expected):
    with Path(path).open('rb') as stream:raw=stream.read(16*1048576+1)
    if len(raw)>16*1048576 or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('bounded pinned report input required')
    return json.loads(raw)


def report(plan,result):
    proof=audit(result,reference=plan['tools']['reference'],experimental=plan['tools']['experimental'],
                fixtures=plan['fixtures'],memory_bytes=plan['host_memory_bytes'],observation_contract=plan['process_observation'])
    if proof['functional_status']!='PASSED':raise ValueError('complete functional matrix required')
    rows=[]
    for functional,raw in zip(proof['functional_audit']['functional_results'],result['rows']):
        samples=raw['outcome']['process_observations']['samples']
        available=[v['observation'] for v in samples if v['observation']['available']]
        rows.append(dict(index=functional['index'],codec=functional['codec'],backend=functional['backend'],
                         requested_threads=functional['requested_threads'],samples=len(samples),available_samples=len(available),
                         missing_samples=len(samples)-len(available),
                         minimum_sampled_threads=min((v['threads'] for v in available),default=None),
                         maximum_sampled_threads=max((v['threads'] for v in available),default=None),
                         maximum_sampled_resident_bytes=max((v['resident_bytes'] for v in available),default=None)))
    return dict(schema='unison-sdk-sampled-os-report/1',rows=rows,
                sdk_calls=len(rows),probe_calls=sum(v['samples'] for v in rows),
                audit=proof,scope='sample maxima only; not actual peaks, process-tree totals, hard caps, calibrated CPU, pixels or speedup',
                sampling_overhead_included=True,fixed_order_single_calls=True,
                parent_and_fd_closure_proved=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['plan','plan-sha256','result','result-sha256','output']:p.add_argument('--'+k,required=True)
    a=p.parse_args();value=report(read_pin(a.plan,a.plan_sha256),read_pin(a.result,a.result_sha256))
    with Path(a.output).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
