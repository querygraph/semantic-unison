"""Source-bound grouped-line supplement; original RESULT and payload never changed."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from grouped_trace import decode,ROOT
sys.path.insert(0,str(ROOT/'tests'))
from cached_benchmark.contract import read_bytes
from cached_benchmark.entry import write
from shared_cpu_pool import unique_object
sys.path.insert(0,str(ROOT/'bench/sync'))
from shared_audit import audit_shared
from run import diagnostic_text
import phase_stats


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('--input-sha256',required=True)
    p.add_argument('--runtime-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=read_bytes(a.input.resolve(),16*1024**2)
    if sha(raw)!=a.input_sha256:raise ValueError('saved source SHA changed')
    result=json.loads(raw,object_pairs_hook=unique_object);audit=audit_shared(result)
    for label,binary in result['binaries'].items():
        manifest=binary['snapshot_source_manifest']
        if manifest['src/semanticRuntime.ml']!=a.runtime_sha256:raise ValueError('runtime source binding differs')
        source=read_bytes(Path(binary['path']).parent/'semanticRuntime.ml',1048576)
        if sha(source)!=a.runtime_sha256:raise ValueError('retained runtime snapshot changed')
        text=source.decode()
        anchor='if measure_stages then Trace.debug "semantic-timings" (fun () ->'
        if text.count(anchor)!=1 or text.count('| Some samples -> List.iter (fun sample ->')!=1:
            raise ValueError('not the known grouped callback source')
    journal={}
    for index,entry in enumerate(result['invocations']):
        identity=entry['identity'];key=identity['label'],identity['mode'],identity['workers'],identity['stage']
        if entry['index']!=index or entry['state']!='OUTCOME' or key in journal:
            raise ValueError('journal outcome ordering/identity differs')
        if entry['command']!=entry['outcome']['command']:
            raise ValueError('journal argv differs from actual outcome')
        journal[key]=entry['outcome']
    if len(journal)!=54:raise ValueError('exact54 journal outcomes required')
    for sample in result['samples']:
        for stage,name in (('seed','seed_sync'),('update','update_sync'),('noop','noop_sync')):
            key=sample['label'],sample['mode'],sample['workers'],stage
            if journal.get(key)!=sample[name]:raise ValueError('journal outcome not bound to row')
    rows=[];total=Counter();inherited=0
    for sample in result['samples']:
        outcome=sample['update_sync'];records=[]
        expected=phase_stats.parse(diagnostic_text(outcome),required_workers=sample['mode']=='semantic')
        if expected!=sample['counters']['semantic_phase_observations']:
            raise ValueError('original strict counters differ from captured streams')
        for stream,endpoint in (('stdout','client'),('stderr','client'),('supervisor_output','server')):
            records+=decode(outcome[stream],endpoint=endpoint,stream=stream)
        for record in records:
            value=record['decoded'];total[value.get('stage',value['kind'])]+=1
            inherited+=int(record['inherited_prefix'])
        phases={r['decoded'].get('stage') for r in records if r['decoded']['kind']=='worker'}
        if sample['mode']=='semantic' and phases!={'hash','parse','verify','write'}:
            raise ValueError('semantic saved raw phase coverage incomplete')
        rows.append(dict(label=sample['label'],mode=sample['mode'],workers=sample['workers'],
                         records=records,observed_worker_stages=sorted(phases),
                         original_prefixed_record_count=len(expected['records'])))
    report=dict(schema='unison-source-bound-grouped-phase-supplement/1',state='SAVED_RAW_GROUPS_AUDITED_NOT_RERUN',
        input=dict(path=str(a.input.resolve()),bytes=len(raw),sha256=sha(raw)),runtime_source_sha256=a.runtime_sha256,
        functional_audit=audit,journal_outcomes_bound=54,rows=rows,observation_counts=dict(total),inherited_prefix_records=inherited,
        original_RESULT_unchanged=True,scope='Legacy source-specific synchronous grouped callbacks, per captured stream with adjacency/job/order anchors. Prefix inheritance is derived evidence, not an originally emitted prefix. Inclusive intervals overlap; no total timing, CPU, wholecommit, physical IO, lifecycle or throughput claim.')
    write(a.output.resolve(),report)
    print(json.dumps(dict(state=report['state'],counts=dict(total),inherited=inherited)),flush=True)

if __name__=='__main__':main()
