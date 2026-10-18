"""Summarize an exact saved shared-eight matrix; no sync or resource release."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench/sync'))
import timed_shared
import resource_report


def distribution(values):
    for value in values:resource_report.number(value,'distribution value')
    if any(v is None for v in values):
        return dict(samples=values,available=False,median=None,minimum=None,maximum=None,
                    p90_nearest_rank=None)
    ordered=sorted(values)
    if not ordered:raise ValueError('nonempty measured distribution required')
    return dict(samples=values,available=True,median=statistics.median(ordered),
                minimum=ordered[0],maximum=ordered[-1],
                p90_nearest_rank=ordered[math.ceil(.9*len(ordered))-1])


def summarize(result):
    proof=timed_shared.audit(result)
    observations=resource_report.build_report(result)
    groups={}
    for index,row in enumerate(observations['rows']):
        key=(row['label'],row['mode'],row['workers'])
        group=groups.setdefault(key,dict(warmup_rows=[],measured_rows=[]))
        group['warmup_rows' if row['phase']=='warmup' else 'measured_rows'].append(index)
    summaries=[]
    for (label,mode,workers),group in sorted(groups.items()):
        measured=[observations['rows'][i] for i in group['measured_rows']]
        if len(measured)!=5 or len(group['warmup_rows'])!=1:
            raise ValueError('fixed warmup/repetition counts differ')
        def endpoint(name):
            return distribution([None if r[name] is None else r[name]['cpu_seconds'] for r in measured])
        summaries.append(dict(label=label,mode=mode,workers=workers,**group,
            update_wall_seconds=distribution([r['wall_seconds'] for r in measured]),
            client_cpu_seconds=endpoint('client_wait4'),server_cpu_seconds=endpoint('server_wait4'),
            semantic_returned_write_bytes=distribution([r['returned_semantic_logical_write_bytes'] for r in measured]),
            primary_reader_bytes=distribution([None if r['primary_reader'] is None else r['primary_reader']['logical_bytes'] for r in measured])))
    return dict(schema='unison-shared-timed-summary/1',state='SAVED_REPEATED_MATRIX_ONLY',
        lifecycle=proof,observations=observations,groups=summaries,
        raw_rows_retained=len(observations['rows']),warmup_rows_excluded_from_distributions=18,
        actual_parent_terminal_or_resource_release_inferred=False,
        interpretation=[
            'All five measured samples retained; no outlier removal, replacement or retry.',
            'With five samples nearest-rank p90 is the maximum, not a stable population-tail estimate.',
            'Client and server CPU remain separate; wait4 descendant attribution may overlap.',
            'Absent observations stay unknown, not measured zero; no inclusive phase sums.',
            'One shared-host warm generated dataset; not quiet timing, physical IO, hard limits or full SOL matrix.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--input-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from cached_benchmark.contract import read_bytes
    from cached_benchmark.entry import write
    from shared_cpu_pool import unique_object
    raw=read_bytes(args.input.resolve(),16*1048576)
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=args.input_sha256:raise ValueError('saved matrix digest differs')
    value=summarize(json.loads(raw,object_pairs_hook=unique_object))
    value['input']=dict(path=str(args.input.resolve()),bytes=len(raw),sha256=digest)
    write(args.output.resolve(),value)
    print(json.dumps(dict(groups=len(value['groups']),rows=value['raw_rows_retained'],runtime_invoked=False)))

if __name__=='__main__':main()
