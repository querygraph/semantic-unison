"""Descriptive analysis of retained warm512 rows; never runs or replaces a sample."""
import argparse,hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def report():
    rows=[];inputs=[];parts=[]
    for index in range(6):
        name=f'warm-512MiB-4files-part{index}'+('-incomplete' if index==3 else '')+'-20261015.json'
        path=ROOT/'bench/sync/results'/name;raw=path.read_bytes();d=json.loads(raw)
        assert d['partition']['index']==index and d['partition']['count']==6
        assert d['repository_head']=='a6f0b695159b3bdb5c3e73d57c0a54900fe86d6d'
        inputs.append(dict(path=str(path.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        grouped=defaultdict(list)
        for sample in d['samples']:
            assert sample['exact_result_and_unchanged_basis'] and sample['noop_preserved_receiver_inode']
            assert all(sample[k]['returncode']==0 for k in ['seed_sync','update_sync','noop_sync'])
            grouped[(sample['label'],sample['mode'],sample['workers'])].append(sample)
        for label,mode,workers in d['partition']['configurations']:
            samples=grouped[(label,mode,workers)]
            measured=[s['update_sync']['wall_seconds'] for s in samples if s['phase']=='measured']
            assert all(type(x) is float and x>0 for x in measured)
            row=dict(part=index,label=label,mode=mode,workers=workers,
                partition_complete=d['complete'],completed_rows=len(samples),measured_count=len(measured),
                update_seconds=dict(median=statistics.median(measured),minimum=min(measured),maximum=max(measured)) if measured else None)
            rows.append(row)
            if d['complete']:
                prior=[x for x in d['summary'] if (x['label'],x['mode'],x['workers'])==(label,mode,workers)]
                assert len(prior)==1 and prior[0]['samples']==len(measured)
                assert prior[0]['wall_seconds']==row['update_seconds']
        parts.append(dict(index=index,complete=d['complete'],completed_rows=len(d['samples'])))
    add=ROOT/'bench/sync/results/warm512-part0-timing-overlap-addendum-20261015.json';raw=add.read_bytes()
    inputs.append(dict(path=str(add.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return dict(schema='unison-warm512-descriptive-report/1',source_head='a6f0b695159b3bdb5c3e73d57c0a54900fe86d6d',
        full_matrix_complete=False,samples_excluded=0,reruns=0,parts=parts,rows=rows,inputs=inputs,
        caveats=['Part3 failed after16completedrows/49actualCLI; remaining rows absent, not zero or imputed.',
        'Part0 static objdump overlap definitely affected zero-based row5 and possibly row4 boundary; impact/carryover unknown. Mandatory e311d5f6 addendum retained.',
        'Part3 user brew/neomutt make and source review disclosure; part5 bounded source-edit disclosures retained. No absolute quiet or timing-clean cohort claim.',
        'Four512MiB generated files; warm/uncontrolled caches, loopback protocol on one APFS host. No cold/network/physical IO savings, RSS hard-cap or camera throughput inference.',
        'Medians use all retained measured update rows, including partial partition rows; warmups retained in original input, not measured statistics.',
        'Frozen historical source, not current-code performance. Per-process wait4 values are not summed into tree RSS/CPU.'])

def markdown(d):
    out=['# Frozen warm512 observed results','','This is a descriptive report of retained samples, not a completed six-part benchmark. No sample was removed, replaced or rerun.','','Update wall time in seconds; each configuration uses four512MiB generated files.','',
        '| Compiler | Workers | Mode | Measured rows | Median | Min–max | Partition |',
        '| --- | ---: | --- | ---: | ---: | --- | --- |']
    for r in d['rows']:
        t=r['update_seconds'];out.append(f"| {r['label']} | {r['workers']} | {r['mode']} | {r['measured_count']} | {t['median']:.3f} | {t['minimum']:.3f}–{t['maximum']:.3f} | {r['part']} {'complete' if r['partition_complete'] else 'FAILED/INCOMPLETE'} |")
    out+=['','Limitations:','']+['- '+x for x in d['caveats']]
    out+=['','The machine-readable companion pins all six input reports and the mandatory part0 timing addendum. Resource closure is established by the separately retained owner/aggregate acceptance receipts, not by these timing statistics.','']
    return '\n'.join(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report-dir',required=True,type=Path);a=p.parse_args()
    d=report();a.report_dir.mkdir(exist_ok=True)
    for name,text in [('warm512-observed-results.json',json.dumps(d,indent=2)+'\n'),('warm512-observed-results.md',markdown(d))]:
        with (a.report_dir/name).open('x') as f:f.write(text)
    print('Recomputed18configuration summaries; all complete-part medians match retained summaries; no sample exclusions or executions.')
