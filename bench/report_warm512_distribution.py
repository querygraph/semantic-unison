"""Empirical distributions of retained historical rows; no benchmarks or filtering."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from report_warm512 import report,ROOT


def empirical(samples):
    if not samples:raise ValueError('at least one retained sample required')
    if any(type(s['seconds']) is not float or not math.isfinite(s['seconds']) or s['seconds']<=0 for s in samples):
        raise ValueError('finite positive actual wall samples required')
    values=sorted(samples,key=lambda s:(s['seconds'],s['source_row']))
    return [dict(s,rank=i,cumulative_fraction=i/len(values)) for i,s in enumerate(values,1)]


def distribution():
    base=report();groups=[]
    for row in base['rows']:
        source=next(i for i in base['inputs'] if f"part{row['part']}" in i['path'])
        raw=json.loads((ROOT/source['path']).read_text());selected=[]
        for index,s in enumerate(raw['samples']):
            if (s['label'],s['mode'],s['workers'],s['phase'])==(row['label'],row['mode'],row['workers'],'measured'):
                selected.append(dict(source_row=index,seconds=s['update_sync']['wall_seconds']))
        assert len(selected)==row['measured_count']
        groups.append(dict(part=row['part'],label=row['label'],mode=row['mode'],workers=row['workers'],
                           partition_complete=row['partition_complete'],measured_count=len(selected),source=source,
                           empirical_samples=empirical(selected),observed_maximum_seconds=max(s['seconds'] for s in selected),
                           population_tail_estimate=None))
    return dict(schema='unison-warm512-empirical-distribution/1',source_head=base['source_head'],
                full_matrix_complete=False,samples_excluded=0,reruns=0,groups=groups,inputs=base['inputs'],
                interpretation=['Each point is one observed measured update and its zero-based source row; warmups remain in raw input.',
                                'Only four or five measured values per configuration. Empirical ranks are not population-tail estimates or confidence bounds.',
                                'Observed maximum is the slowest retained sample, not a predicted worst case. No interpolated/extrapolated p95 or p99.',
                                'Failed part3 is partial and all observed values remain. No replacement/exclusion or complete-six-part claim.'],
                caveats=base['caveats'])


def markdown(d):
    out=['# Frozen warm512 empirical distributions','',
         'Historical observations only. All measured values are retained; there are no new executions, exclusions or replacements.','',
         'Each list is sorted update seconds; bracketed numbers are zero-based rows in the pinned raw partition file. Four or five values cannot establish a population tail.','',
         '| Compiler | Workers | Mode | Retained measured values (seconds [row]) | Partition |',
         '| --- | ---: | --- | --- | --- |']
    for g in d['groups']:
        points=', '.join(f"{s['seconds']:.6f} [{s['source_row']}]" for s in g['empirical_samples'])
        out.append(f"| {g['label']} | {g['workers']} | {g['mode']} | {points} | {g['part']} {'complete' if g['partition_complete'] else 'FAILED/PARTIAL'} |")
    out+=['','Interpretation:','']+['- '+s for s in d['interpretation']]
    out+=['','Timing and measurement limitations:','']+['- '+s for s in d['caveats']]
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-dir',required=True,type=Path);args=parser.parse_args()
    d=distribution();args.report_dir.mkdir(exist_ok=True)
    for name,value in [('warm512-empirical-distribution-v1.json',json.dumps(d,indent=2)+'\n'),('warm512-empirical-distribution-v1.md',markdown(d))]:
        with (args.report_dir/name).open('x') as f:f.write(value)
    print(json.dumps(dict(configurations=len(d['groups']),measured_samples=sum(g['measured_count'] for g in d['groups']),new_benchmark_executions=0,samples_excluded=0)))
