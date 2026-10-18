"""Interpret saved sync observations only; never run sync or infer owner closure."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from cached_benchmark.contract import read_bytes
from cached_benchmark.entry import write
from phase_stats import validate as phase_observations


def number(value, name):
    if value is None:return None
    try:finite=type(value) in (int,float) and math.isfinite(value)
    except OverflowError:finite=False
    if not finite or value<0:
        raise ValueError('finite nonnegative observation required: '+name)
    return value


def integer(value, name):
    if value is None:return None
    if type(value) is not int or not 0<=value<=(1<<63)-1:
        raise ValueError('nonnegative signed-int64 counter required: '+name)
    return value


def usage(value, system):
    if value is None:return None
    user=number(value.get('wait4_user_seconds'),'user CPU')
    kernel=number(value.get('wait4_system_seconds'),'system CPU')
    rss=number(value.get('wait4_maxrss_native_units'),'native RSS')
    return dict(user_seconds=user,system_seconds=kernel,
        cpu_seconds=None if user is None or kernel is None else number(user+kernel,'summed endpoint CPU'),
        maxrss_bytes=None if rss is None or system not in ('Darwin','Linux') else number(rss*(1024 if system=='Linux' else 1),'normalized RSS'),
        maxrss_native_units=rss,
        block_input_operations=integer(value.get('block_input_operations'),'input operations'),
        block_output_operations=integer(value.get('block_output_operations'),'output operations'))


def build_report(result):
    if result.get('schema')!='unison-synthetic-sync/0' or type(result.get('complete')) is not bool:
        raise ValueError('typed saved sync result required')
    system=result['host']['system'];rows=[]
    for sample in result['samples']:
        update=sample.get('update_sync')
        if update is None:
            rows.append(dict(label=sample['label'],mode=sample['mode'],workers=sample['workers'],
                             availability='NO_COMPLETED_UPDATE_RECEIPT'))
            continue
        proxy=update.get('proxy')
        counters=sample.get('counters') or {}
        if counters.get('hash_parse_verify_commit_seconds') is not None:
            raise ValueError('whole-path phase/commit accounting is not qualified by partial diagnostics')
        reads=counters.get('primary_reader_reads')
        primary=None
        if reads is not None:
            logical=integer(reads['logical_bytes'],'primary read bytes')
            records=reads['records']
            if type(records) is not list:
                raise ValueError('reader record list required')
            delivered=[integer(r['logical_bytes'],'reader bytes') for r in records]
            if (type(reads['reported_jobs']) is not int or reads['reported_jobs']!=len(records)
                    or any(value is None for value in delivered)
                    or (logical is not None and logical!=sum(delivered))):
                raise ValueError('primary-reader aggregate differs from records')
            primary=dict(reported_jobs=reads['reported_jobs'],logical_bytes=logical,
                         scope=reads['scope'],absence=reads.get('absence'))
        protocol=None
        if proxy is not None:
            values=proxy['forwarded_protocol_bytes']
            protocol={k:integer(values[k],k) for k in ('client_to_server_bytes','server_to_client_bytes')}
        rows.append(dict(label=sample['label'],mode=sample['mode'],workers=sample['workers'],
            phase=sample['phase'],repetition=sample['repetition'],availability='SAVED_UPDATE_OBSERVATIONS',
            wall_seconds=number(update['wall_seconds'],'wall'),
            client_wait4=usage(update.get('resources'),system),
            server_wait4=usage(proxy.get('server_resources'),system) if proxy else None,
            forwarded_protocol_bytes=protocol,
            primary_reader=primary,
            returned_semantic_logical_write_bytes=integer(counters.get('semantic_logical_write_bytes'),'semantic writes'),
            semantic_payload_bytes=integer(counters.get('semantic_payload_bytes'),'semantic payload'),
            inherited_same_offset_bytes=integer(counters.get('same_offset_inherited_bytes'),'inherited bytes'),
            non_inherited_output_extent_model_bytes=integer(counters.get('materialization_non_inherited_logical_bytes_model'),'output model'),
            output_extent_model_basis=counters.get('materialization_model_basis'),
            application_read_bytes=integer(counters.get('application_read_bytes'),'application reads'),
            semantic_phase_observations=phase_observations(counters.get('semantic_phase_observations')),
            hash_parse_verify_commit_seconds=counters.get('hash_parse_verify_commit_seconds'),
            physical_storage_write_bytes=integer(counters.get('physical_storage_write_bytes'),'physical writes'),
            descriptor_queue_peaks=counters.get('queue_descriptor_peaks')))
    return dict(schema='unison-saved-sync-resource-report/1',state='SAVED_OBSERVATIONS_ONLY',
        input_complete=result['complete'],repository_head=result.get('repository_head'),
        host=result['host'],parameters=result['parameters'],cache_state=result.get('cache_state'),
        transport=result.get('transport'),rows=rows,
        source_currentness='Not rebound to later checkout; retain exact input/build manifests.',
        actual_parent_terminal_or_resource_release_inferred=False,
        interpretation=[
            'Client/server wait4 CPU may overlap through reaped descendants; never sum these receipts as whole-tree CPU.',
            'maxrss is per-process lifetime high water, not simultaneous tree RSS or a configured hard memory cap.',
            'Forwarded protocol bytes include metadata/RPC overhead and exclude launcher framing; not encrypted or physical network bytes.',
            'Primary-reader bytes exclude nested verification, legacy/helper reads and prefetch; absent counters are unknown, not zero.',
            'Semantic write counts are successful returned logical writes; other output extents are labeled models, not write syscalls or APFS block savings.',
            'Block operations are native operations, never converted into physical bytes.',
            'Inclusive phase records overlap and are not summed; native namespace events do not prove later archive/full transfer success.',
            'Functional single samples are not repeated throughput benchmarks; missing total-commit/physical/peak measurements remain null.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--input-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.input.suffix!='.json' or args.output.suffix!='.json':
        parser.error('explicit metadata JSON paths required')
    raw=read_bytes(args.input.resolve(),16*1048576)
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=args.input_sha256:raise ValueError('saved input SHA differs')
    from shared_cpu_pool import unique_object
    result=json.loads(raw,object_pairs_hook=unique_object)
    report=build_report(result)
    report['input'] = dict(path=str(args.input.resolve()),bytes=len(raw),sha256=digest)
    write(args.output.resolve(),report)
    print(json.dumps(dict(rows=len(report['rows']),state=report['state'],payload_run=False)))


if __name__=='__main__':main()
