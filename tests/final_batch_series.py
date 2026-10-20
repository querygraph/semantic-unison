"""Finite serial measured cohort; each case owns its own Unison8+EX bundle.

Coordinator performs only metadata orchestration, charged to case owner overhead
while a case runs. It holds no competing pool and cannot release a case's FDs.
Unknown child/capture state retains this coordinator; no retry or successor.
"""
import argparse,hashlib,json,os,sys,time,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from sdk_host_matrix.shared_binding import inventory
from shared_child import start
from final_profile_owner import closed,sha
from batch_series import schedule,summarize


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('cohort plan SHA differs')
    packet=json.loads(raw)
    if packet['state']!='PREPARED_ONE_BATCH_MEASUREMENT_COHORT' or packet['repository']!=str(ROOT):raise ValueError('exact finite cohort required')
    expected=schedule(workers=tuple(packet['workers']))
    if [s['identity'] for s in packet['samples']]!=expected:raise ValueError('cohort matrix shrank or reordered')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('cohort source changed: '+name)
    sources()
    root=Path(packet['workspace']);root.mkdir(mode=0o700);st=root.stat()
    store=Store(str(root),dict(device=st.st_dev,inode=st.st_ino));current=None;attempted=False;io=cpu=None
    try:
        # Once-only artifact read before native cases: no child while these
        # independently acquired preflight descriptions are held.
        canonical=inventory()
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,(0,))
        if bundle is None:raise ValueError('preflight IO/CPU contention, cohort consumed unstarted')
        io,cpu=bundle
        if sha(packet['interpreter']['path'],64*1048576)!=packet['interpreter']['sha256']:raise ValueError('interpreter changed')
        metadata=[]
        for command in (['/usr/sbin/sysctl','-n','hw.physicalcpu','hw.memsize'],
                        ['/usr/sbin/diskutil','info','-plist','/System/Volumes/Data']):
            attempted=True
            getter=start(command,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),pass_fds=(*cpu.fds,*io.fds))
            observed=getter.finish(time.monotonic()+15);closed(observed,observed['returncode'])
            metadata.append(observed)
        store.write('HOST-METADATA.json',dict(observations=metadata,
            scope='read-only premeasurement OS metadata; no physical leaf independence/attestation'))
        close_unstarted(cpu);close_unstarted(io)
        attempted=False
        rows=[];pins=[];deadline=time.monotonic()+1200
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,samples=len(expected),
            host=dict(system=platform.system(),release=platform.release(),machine=platform.machine(),logical_cpus=os.cpu_count(),
                device=os.stat(root).st_dev,available_bytes=os.statvfs(root).f_bavail*os.statvfs(root).f_frsize),
            cache_state='warm by generation/seed/hash per row; no cacheflush',
            background='Photo source/CPU8 and other host activity uncontrolled; not quiet timing',
            cpu_scope='each case independently reserves Unison00..07; coordinator metadata overhead included in reserved owner budget'))
        print('SERIES_START',os.getpid(),str(root),len(expected),flush=True)
        for item in packet['samples']:
            sources()
            if time.monotonic()>=deadline:raise TimeoutError('cohort observation expired before next case')
            identity=item['identity'];ref=item['plan'];data=read_bytes(ref['path'],2*1048576)
            if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('case plan changed')
            case=json.loads(data)
            if (case['roles']!=dict(client=identity['label'],server=identity['label'])
                    or case['mode']!=identity['mode'] or case['workers']!=identity['workers']
                    or case['corpus']!=packet['corpus'] or case.get('sample_kind','corpus')!=packet['sample_kind']
                    or case['cleanup_generated_payloads'] is not True):raise ValueError('case declaration differs')
            target=Path(case['workspace'])
            if target.exists():raise ValueError('case namespace already consumed; no replay')
            command=[packet['interpreter']['path'],str(ROOT/'tests/final_batch_owner.py'),'--plan',ref['path'],'--sha256',ref['sha256']]
            attempted=True
            current=start(command,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            outcome=current.finish(min(deadline,time.monotonic()+600));closed(outcome,0)
            if outcome['command']!=command:raise ValueError('case owner command differs')
            result=json.loads(read_bytes(str(target/'OWNER-RESULT.json'),2*1048576));report=result['audit']
            cleaned=json.loads(read_bytes(str(target/'PAYLOADS-CLEANED.json'),16384))
            begin=json.loads(read_bytes(str(target/'START.json'),16384))
            if (result['complete'] is not True or report['external_children_settled'] is not True
                    or report['fresh_exact_left_right'] is not True or report['unchanged_receiver_noop'] is not True
                    or cleaned.get('generated_left_right_removed') is not True
                    or any((target/name).exists() for name in ('left','right'))
                    or tuple((r['device'],r['inode']) for r in begin['resource_rows'])!=canonical):
                raise ValueError('case output/resource/payload-cleanup proof differs')
            update=report['peer_reports'][1]
            observed=update['observations'];metric=dict(pair_elapsed_ns=observed['elapsed_ns'],
                client_elapsed_ns=observed['client']['wall_to_terminal_ns'],
                client_wait4=observed['client']['wait4'],proxy_wait4=observed['proxy']['wait4'],
                protocol_bytes=update['protocol_bytes'],counters=report['counters'])
            row=dict(identity=identity,complete=True,update=metric,case_plan=ref,
                owner_cleanup=outcome['client_cleanup'],owner_result=dict(path=str(target/'OWNER-RESULT.json'),
                    sha256=sha(target/'OWNER-RESULT.json',2*1048576)))
            pins.append(store.write('SAMPLE-%03d.json'%identity['index'],dict(row=row,outcome=outcome,report=report)))
            rows.append(row)
            print('SAMPLE_CLOSED',identity['index'],identity['phase'],identity['label'],identity['mode'],
                  identity['workers'],metric['client_elapsed_ns']/1e9,flush=True)
        sources();summary=summarize(rows,workers=tuple(packet['workers']))
        store.write('RESULT.json',dict(complete=True,rows=rows,sample_pins=pins,summary=summary,
            wall_scope='client spawn-to-terminal-observed; pair includes wrapper/evidence persistence',
            raw_resource_scope='per-process wait4; may include reaped descendants; no aggregate tree peak/hardcap',
            no_sdk_or_photos=True,parent_tool_terminal_proved=False))
        store.close();print('SERIES_CLOSED',str(root),flush=True);return 0
    except BaseException as error:
        if not attempted and not isinstance(error,UnresolvedOwnership):
            try:
                store.write('PREENTRY-REFUSED.json',dict(child_attempted=False,error=repr(error)))
                store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('SERIES_PREENTRY_RETAIN',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('SERIES_RETAIN',repr(error),str(root),flush=True))


if __name__=='__main__':raise SystemExit(main())
