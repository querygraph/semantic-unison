"""Re-audit retained receiving comparison receipts; never execute a native call."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from sdk_throughput.audit import audit
from sdk_throughput.plan import comparison
from shared_io_pool import unique_object
from private_camera_receiving.close import close_descriptors


def read_receipt(path, expected_sha=None):
    """Read one bounded, stable regular receipt; propagate close uncertainty."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        first=os.fstat(fd)
        fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid')
        stamp=lambda s:tuple(getattr(s,k) for k in fields)
        if not (stat.S_ISREG(first.st_mode) and first.st_nlink==1 and first.st_uid==os.getuid()
                and 0<first.st_size<=16*1048576):raise ValueError('bounded owned receipt required')
        raw=bytearray()
        while len(raw)<first.st_size:
            block=os.read(fd,min(65536,first.st_size-len(raw)))
            if not block:raise ValueError('short receipt')
            raw.extend(block)
        if stamp(first)!=stamp(os.fstat(fd)) or stamp(first)!=stamp(os.lstat(path)):
            raise ValueError('receipt changed')
        digest=hashlib.sha256(raw).hexdigest()
        if expected_sha is not None and digest!=expected_sha:raise ValueError('receipt SHA differs')
        return json.loads(raw,object_pairs_hook=unique_object),dict(path=str(path),bytes=len(raw),sha256=digest)
    finally:close_descriptors([fd])


def summarize(result,plan,*,raw_proxy_receipts):
    proof=audit(result,plan,raw_proxy_receipts=raw_proxy_receipts)
    rows=comparison(plan['binaries'],plan['tool'],plan['workspace'])['rows']
    payload=sum(s['bytes'] for s in plan['sources']);groups=[]
    measurements=proof.get('verified_case_measurements',[])
    for label in ('stock','ox'):
        for workers in (1,3):
            selected=[m for m in measurements if (m['label'],m['endpoint_workers'])==(label,workers)]
            measured=[m for m in selected if m['phase']=='measured'];values=[m['wall_seconds'] for m in measured]
            median=statistics.median(values) if values else None
            groups.append(dict(label=label,endpoint_workers=workers,verified_warmups=sum(m['phase']=='warmup' for m in selected),
                               measured_count=len(measured),measured_samples=measured,
                               median_seconds=median,minimum_seconds=min(values) if values else None,maximum_seconds=max(values) if values else None,
                               receiving_payload_mib_per_median_wall_second=(payload/1048576/median) if median is not None else None,
                               all_five_measured_present=len(measured)==5))
    ratios=[]
    for label in ('stock','ox'):
        seq,parallel=[g for g in groups if g['label']==label]
        eligible=result['complete'] and seq['all_five_measured_present'] and parallel['all_five_measured_present']
        ratios.append(dict(label=label,observed_median_ratio_worker1_over_worker3=(seq['median_seconds']/parallel['median_seconds']) if eligible else None,
                           comparable_complete_cohorts=eligible))
    attempted=[]
    for i,entry in enumerate(result['invocations']):
        case=result['cases'][i]['case'];row=rows[i]
        attempted.append(dict(index=i,label=row['label'],endpoint_workers=row['endpoint_workers'],phase=row['phase'],
                              verified_complete_case=case['complete'],outcome_returncode=entry['outcome']['returncode']))
    return dict(schema='unison-sdk-receiving-comparison-report/1',complete=result['complete'],
                functional_status=proof['functional_status'],case_payload_bytes=payload,groups=groups,ratios=ratios,
                attempted_rows=attempted,attempted_cli_calls=len(attempted),sdk_helpers_settled=proof['sdk_helpers_settled'],
                failed_result_reason=result.get('failure'),raw_failed_prefix_preserved=not result['complete'],new_native_executions=0,
                resource_release_authorized=False,
                caveats=['Warm generated-input end-to-end receiving validation includes hashing, transport, staging, helper startup and SDK; not isolated SDK decode throughput.',
                         'One warmup/five measured repetitions per configuration; observed median ratios are descriptive, not confidence bounds or causal SDK speedup.',
                         'All verified measured cases retain their exact row indexes and order. Failed calls remain in attempted rows and raw pinned input, never imputed as zero.',
                         'Incomplete results have no comparative ratio. CPU8 reservations and source limits are not whole-process RSS/OSthread/physical IO caps.',
                         'No coldcache, representative camera corpus, semantic eligibility, pixel equivalence or production qualification. Source activity and scheduling disclosures must accompany actual results.',
                         'This receipt audit does not prove owning-tool terminal, fresh payload hashes or global resource release; those require separate actual owner/parent acceptance.'])


def markdown(d):
    out=['# SDK receiving comparison','',f"Functional status: {d['functional_status']}; complete: {d['complete']}. No new native executions.",'',
         '| Compiler | Endpoint workers | Measured samples | Median seconds | Range seconds |',
         '| --- | ---: | ---: | ---: | --- |']
    for g in d['groups']:
        median='unknown' if g['median_seconds'] is None else f"{g['median_seconds']:.6f}"
        spread='unknown' if g['minimum_seconds'] is None else f"{g['minimum_seconds']:.6f}–{g['maximum_seconds']:.6f}"
        out.append(f"| {g['label']} | {g['endpoint_workers']} | {g['measured_count']} | {median} | {spread} |")
    out+=['','Observed median ratios (worker1 / worker3):','']
    for r in d['ratios']:
        ratio='unavailable (incomplete)' if r['observed_median_ratio_worker1_over_worker3'] is None else f"{r['observed_median_ratio_worker1_over_worker3']:.4f}"
        out.append(f"- {r['label']}: {ratio}")
    out+=['','Limitations:','']+['- '+s for s in d['caveats']]
    return '\n'.join(out)+'\n'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','result'):parser.add_argument('--'+name,required=True,type=Path);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--report-dir',required=True,type=Path);args=parser.parse_args(argv)
    plan,plan_pin=read_receipt(args.plan,args.plan_sha256);result,result_pin=read_receipt(args.result,args.result_sha256)
    rows=comparison(plan['binaries'],plan['tool'],plan['workspace'])['rows'];proxies=[];pins=[]
    for row in rows[:len(result['invocations'])]:
        path=Path(row['directory'])/'seed-proxy.json'
        proxy,pin=read_receipt(path);proxies.append(proxy);pins.append(pin)
    d=summarize(result,plan,raw_proxy_receipts=proxies)
    d['inputs']=[plan_pin,result_pin,*pins]
    args.report_dir.mkdir(exist_ok=True)
    for name,value in [('sdk-receiving-comparison.json',json.dumps(d,indent=2,allow_nan=False)+'\n'),('sdk-receiving-comparison.md',markdown(d))]:
        with (args.report_dir/name).open('x') as f:f.write(value)
    print(json.dumps(dict(complete=d['complete'],attempted_cli_calls=d['attempted_cli_calls'],sdk_helpers_settled=d['sdk_helpers_settled'],new_native_executions=0)))


if __name__=='__main__':main()
