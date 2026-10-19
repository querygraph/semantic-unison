"""Reproducible metadata/raw-peer re-audit of a completed measured cohort.

Reads retained proof only; never executes a native child or establishes a tool
terminal. Caller supplies exact cohort plan and independently observed terminal.
"""
import hashlib,json
from pathlib import Path
from batch_series import summarize,schedule
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.parent import pinned
from batch_pair import audit as audit_pair
from batch_observations import pair as measurements
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import UnresolvedOwnership
from final_profile_owner import closed
from batch_commands import schedule as commands


def audit(root,packet):
    if [item['identity'] for item in packet['samples']] != schedule(workers=tuple(packet['workers'])):
        raise ValueError('exact complete measured schedule required')
    root=Path(root);native=root.lstat();store=Store(str(root),dict(device=native.st_dev,inode=native.st_ino))
    try:
        result=store.read_json('RESULT.json',expected_sha256=None)
        if result['complete'] is not True or len(result['sample_pins'])!=len(packet['samples']):
            raise ValueError('cohort incomplete')
        rows=[];pair_count=0;proof_pins=[]
        for item,pin in zip(packet['samples'],result['sample_pins']):
            saved=pinned(store,pin,'SAMPLE-%03d.json'%item['identity']['index']);row=saved['row']
            if row['identity']!=item['identity'] or row['case_plan']!=item['plan']:raise ValueError('sample identity differs')
            raw=read_bytes(item['plan']['path'],2*1048576)
            if len(raw)!=item['plan']['bytes'] or hashlib.sha256(raw).hexdigest()!=item['plan']['sha256']:raise ValueError('case plan pin differs')
            case=json.loads(raw);target=Path(case['workspace']);st=target.lstat();child=Store(str(target),dict(device=st.st_dev,inode=st.st_ino))
            try:
                outcome=saved['outcome'];closed(outcome,0)
                if outcome['command']!=[packet['interpreter']['path'],str(Path(packet['repository'])/'tests/final_batch_owner.py'),'--plan',item['plan']['path'],'--sha256',item['plan']['sha256']]:
                    raise ValueError('actual case owner command differs')
                if outcome['client_cleanup']!=row['owner_cleanup']:
                    raise ValueError('actual case owner settlement differs')
                owner=child.read_json('OWNER-RESULT.json',expected_sha256=None)
                actual=child.read('OWNER-RESULT.json')
                if hashlib.sha256(actual).hexdigest()!=row['owner_result']['sha256'] or owner['audit']!=saved['report']:
                    raise ValueError('case owner result differs')
                runtime=child.read_json('BATCH-RESULT.json',expected_sha256=None)
                binaries={role:case['artifacts'][label]['path'] for role,label in case['roles'].items()}
                expected=commands(binaries['client'],binaries['server'],str(target),mode=case['mode'],workers=case['workers'])
                if runtime['contract']!=expected:raise ValueError('exact production call schedule differs')
                if len(saved['report']['peer_reports'])!=3 or set(runtime['pairs'])!={'seed','update','noop'}:
                    raise ValueError('exact three peer reports required')
                for stage,peer in zip(('seed','update','noop'),saved['report']['peer_reports']):
                    record=pinned(child,runtime['pairs'][stage],stage+'-pair.json')
                    if record['schema']!='unison-batch-pair/2':raise ValueError('measured peer observation missing')
                    intent=child.read_json(stage+'-INTENT.json',expected_sha256=None);contract=intent['row']
                    if contract!=expected['rows'][('seed','update','noop').index(stage)]:
                        raise ValueError('raw command differs from source-selected schedule')
                    command=[packet['interpreter']['path'],'-B',str(target/(stage+'-proxy.py'))]
                    joined=audit_pair(child,record['evidence'],client_command=contract['command'],proxy_command=command,server_command=contract['server_command'])
                    if record['audit']!=joined:raise ValueError('raw pair audit differs')
                    observed=measurements(child,record['measurements'],joined)
                    if observed!=peer['observations']:raise ValueError('saved resource/clock observations differ')
                    if stage=='update':
                        metric=dict(pair_elapsed_ns=observed['elapsed_ns'],client_elapsed_ns=observed['client']['wall_to_terminal_ns'],
                            client_wait4=observed['client']['wait4'],proxy_wait4=observed['proxy']['wait4'],
                            protocol_bytes=peer['protocol_bytes'],counters=saved['report']['counters'])
                        if metric!=row['update']:raise ValueError('row metrics differ from pinned observations')
                    pair_count+=1
                if any((target/name).exists() for name in ('left','right')):raise ValueError('generated payload cleanup not complete')
            except UnresolvedOwnership:
                raise
            except BaseException:
                child.close();raise
            else:child.close()
            rows.append(row);proof_pins.append(pin)
        summary=summarize(rows,workers=tuple(packet['workers']))
        if rows!=result['rows'] or summary!=result['summary']:raise ValueError('reconstructed summary differs')
        report=dict(rows=len(rows),measured_rows=sum(r['identity']['phase']=='measured' for r in rows),
            warmup_rows=sum(r['identity']['phase']=='warmup' for r in rows),raw_peer_pairs_reaudited=pair_count,
            unmeasured=dict(physical_write_bytes=None,application_read_bytes=None,peak_live_descriptors=None,
                peak_queue_depth=None,hash_parse_verify_commit_stage_seconds=None,
                scope='not instrumented by this cohort; logical models, protocol counters and per-process samples are not substitutes'),
            summary=summary,sample_pins=proof_pins,scope='retained raw proof re-audit; payloads already verified before deliberate generated cleanup; no new runtime/terminal proof')
    except UnresolvedOwnership:
        raise
    except BaseException:
        store.close();raise
    else:store.close()
    return report


def markdown(report):
    text=['# Many-small shared-host measurements','',
          'Warm generated corpus: 1,024 × 32 KiB files, 512 B XMP packets. One warmup and five measured samples per configuration. Both endpoints use the named current compiler. No cache flush or quiet-host guarantee.','',
          '| Compiler | Workers per endpoint | Mode | Client median (s) | Observed range (s) | Pair median (s) |','| --- | ---: | --- | ---: | ---: | ---: |']
    for row in report['summary']:
        m=row['client_elapsed_seconds'];p=row['pair_elapsed_seconds']
        text.append(f"| {row['label']} | {row['workers']} | {row['mode']} | {m['median']:.4f} | {m['minimum']:.4f}–{m['maximum']:.4f} | {p['median']:.4f} |")
    groups={}
    for row in report['summary']:
        groups.setdefault((row['label'],row['workers']),{})[row['mode']]=row['client_elapsed_seconds']['median']
    ordinary_fastest=bool(groups) and all(set(g)=={'ordinary','receiver-clone','semantic'}
        and g['ordinary']<min(g['receiver-clone'],g['semantic']) for g in groups.values())
    text+=['',
      ('Ordinary transfer is faster in this dataset. Receiver clones and SDE reduce the logical materialization model, but do not deliver a wall-time win here.'
       if ordinary_fastest else 'The table retains mode-specific observations; it does not establish an isolated algorithm or compiler advantage.')
       +' Do not infer isolated compiler gains from these small, shared-host samples.',
      '',
      'Client time is spawn-to-terminal-observed. Pair time also includes proxy startup and evidence persistence. Per-process wait4 CPU/RSS and protocol-byte observations are retained in JSON. Proxy CPU may include its reaped native server; do not sum overlapping resource observations or call them simultaneous tree peaks/hard caps.',
      '',
      'Application read bytes, peak live descriptors, peak queue depth and separate hash/parse/verify/commit timings were not instrumented by this cohort. These remain unknown, rather than inferred from file sizes or process samples.',
      '',
      'All outputs and no-op identities were verified before generated payload cleanup; raw samples and peer proofs remain. Protocol counts exclude launcher control headers and are not physical-network traffic. Logical materialization models are not physical writes. No SDK/photo/pixel/cold-cache/cross-volume/physical-network/scaling claim. Five observations give a descriptive range, not a reliable population-tail guarantee.']
    return '\n'.join(text)+'\n'
