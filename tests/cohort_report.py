"""Saved-only ten-cohort report; no execution, currentness or resource release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'bench/sync'))
import auto_cohort as A
import resource_report
from sync_timed_summary import distribution
from cohort_entry import audit_result
from cached_benchmark.contract import read_bytes
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import unique_object, require


def summarize(records):
    require(type(records) is list and len(records)<=10,'at most ten cohort records required')
    seen=set();cohorts=[];groups=[];workload=None
    for record in records:
        plan=record['plan'];result=record['result'];c=plan['cohort']
        require(A.exact(c,A.reconstruct(c)),'exact cohort declaration required')
        dimensions=dict(file_mib=c.get('file_mib',32),files=c.get('files',8))
        if workload is None:workload=dimensions
        require(dimensions==workload,'one workload per comparison report required')
        key=c['label'],c['selection']
        require(key not in seen,'duplicate compiler/selection cohort');seen.add(key)
        proof=audit_result(result,plan)
        row=dict(label=c['label'],selection=c['selection'],lifecycle=proof,
                 reserved_credits=c['reserved_credits'],declared_peak_credits=c['declared_peak_credits'],
                 endpoint_permit_upper_bound=c['endpoint_permit_upper_bound'],
                 functional_status=proof['functional_status'],
                 raw_sample_indexes=list(range(len(result.get('samples',[])))))
        if proof['functional_status']!='PASSED':
            row['failure']=result.get('failure');row['distributions_qualified']=False
            cohorts.append(row);continue
        observations=resource_report.build_report(result)
        row['observations']=observations;row['distributions_qualified']=True
        for mode in A.MODES:
            selected=[r for r in observations['rows'] if r['mode']==mode]
            measured=[r for r in selected if r['phase']=='measured']
            warm=[r for r in selected if r['phase']=='warmup']
            require(len(measured)==5 and len(warm)==1,'exact repeated distribution required')
            def values(field):return distribution([r[field] for r in measured])
            def nested(field,subfield):
                return distribution([None if r[field] is None else r[field][subfield] for r in measured])
            groups.append(dict(label=c['label'],selection=c['selection'],mode=mode,
                warmup_rows=1,measured_rows=5,
                update_wall_seconds=values('wall_seconds'),
                client_cpu_seconds=nested('client_wait4','cpu_seconds'),
                server_cpu_seconds=nested('server_wait4','cpu_seconds'),
                client_maxrss_bytes=nested('client_wait4','maxrss_bytes'),
                server_maxrss_bytes=nested('server_wait4','maxrss_bytes'),
                primary_reader_bytes=nested('primary_reader','logical_bytes'),
                returned_semantic_write_bytes=values('returned_semantic_logical_write_bytes'),
                inherited_same_offset_bytes=values('inherited_same_offset_bytes'),
                non_inherited_extent_model_bytes=values('non_inherited_output_extent_model_bytes'),
                client_to_server_bytes=nested('forwarded_protocol_bytes','client_to_server_bytes'),
                server_to_client_bytes=nested('forwarded_protocol_bytes','server_to_client_bytes'),
                application_read_bytes=values('application_read_bytes'),
                physical_storage_write_bytes=values('physical_storage_write_bytes')))
        cohorts.append(row)
    missing=[dict(label=label,selection=s) for s in A.SELECTORS for label in ('stock','ox')
             if (label,s) not in seen]
    complete=len(records)==10 and all(c['functional_status']=='PASSED' for c in cohorts)
    for group in groups:
        baseline=next((g for g in groups if g['label']==group['label'] and g['mode']==group['mode']
                       and type(g['selection']) is int and g['selection']==1),None)
        b=None if baseline is None else baseline['update_wall_seconds']['median']
        v=group['update_wall_seconds']['median']
        group['descriptive_one_worker_wall_ratio']=None if b is None or v is None or v==0 else b/v
    return dict(schema='unison-auto-cohort-report/1',state='FULL_GENERATED_MATRIX' if complete else 'INCOMPLETE_MATRIX',
        workload=workload,
        matrix_complete=complete,missing_cohorts=missing,cohorts=cohorts,groups=groups,
        raw_samples_retained=sum(len(c['raw_sample_indexes']) for c in cohorts),
        actual_parent_terminal_proved=False,resource_release_authorized=False,current_production_proved=False,
        interpretation=[
            'All raw samples stay in authenticated input files; every row index including failed prefixes is retained here. No exclusions, replacements or retries.',
            'Only one declared warmup per successful configuration is excluded from measured distributions.',
            'Five-sample nearest-rank p90 is the maximum, not a stable population-tail estimate.',
            'Configured auto upper bound is not actual domain count or OS-thread count.',
            'CPU and per-process RSS remain endpoint-separated; no sum as simultaneous tree usage.',
            'Returned semantic writes and modeled extents are different quantities; physical IO remains unknown unless measured.',
            'Descriptive one-worker wall ratios are not causal speedup, quiet-host, corpus or full SOL evidence.',
            'Nested audit/metadata pins do not prove actual parent terminal, authenticate tool events or authorize FD release.'])


def document(path,limit):
    raw=read_bytes(path,limit)
    return raw,json.loads(raw,object_pairs_hook=unique_object)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raw,manifest=document(args.manifest.resolve(),1048576)
    require(hashlib.sha256(raw).hexdigest()==args.manifest_sha256,'saved manifest hash differs')
    require(manifest.get('schema')=='unison-auto-cohort-report-input/1'
            and type(manifest.get('records')) is list and len(manifest['records'])<=10,
            'exact bounded saved input manifest required')
    records=[];pins=[];total=0
    for entry in manifest['records']:
        row={}
        for kind in ('plan','result'):
            item=entry[kind];path=Path(item['path'])
            require(path.is_absolute() and path.suffix=='.json','absolute saved JSON metadata required')
            data,value=document(path,16*1048576);total+=len(data)
            require(total<=160*1048576 and hashlib.sha256(data).hexdigest()==item['sha256'],
                    'bounded saved input hash differs')
            row[kind]=value;pins.append(dict(path=str(path),sha256=item['sha256'],bytes=len(data)))
        records.append(row)
    report=summarize(records);report['saved_inputs']=pins
    report['manifest_sha256']=args.manifest_sha256
    encoded=(json.dumps(report,indent=2,allow_nan=False)+'\n').encode()
    require(len(encoded)<=32*1048576,'report metadata size exceeded')
    fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        at=0
        while at<len(encoded):
            n=os.write(fd,encoded[at:]);require(n>0,'report write stalled');at+=n
        os.fsync(fd)
    finally:close_descriptors([fd])
    print(json.dumps(dict(state=report['state'],rows=report['raw_samples_retained'],runtime_invoked=False)))


if __name__=='__main__':main()
