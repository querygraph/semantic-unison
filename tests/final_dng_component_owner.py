"""Retained current DNG component/publication controls; original tiny fixtures."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from shared_child import start
from sdk_merge_receiving.store import Store
from final_profile_owner import sha,closed


def audit_calls(result):
    calls=result['calls'];counts={0:0,2:0};summaries=[]
    if type(calls) is not list or not 0<len(calls)<=150:raise ValueError('bounded original suite calls required')
    for out in calls:
        argv=out['command'];code=0
        if not (type(argv) is list and argv and all(type(x) is str and x for x in argv)):
            raise ValueError('exact nonempty child command required')
        cleanup=out['client_cleanup'];pid=cleanup['pid']
        if not (type(pid) is int and 0<pid<2**31
                and out['aggregate_or_parent_terminal_proved'] is False
                and out['io_cpu_release_authorized'] is False):
            raise ValueError('direct child identity and non-authorizing producer required')
        if Path(argv[0]).name=='dng-component-ablation':
            code=2
            if 'changed named record escaped lookup before reader retirement' not in out['stderr']:raise ValueError('designated ablation failed for wrong reason')
        elif '-c' in argv and Path(argv[-1]).name in ('owner_only_cache_capture.ml','owner_only_owner_index_publication.ml'):
            code=2
            if not any(x in out['stderr'] for x in ('nonportable','contended')):raise ValueError('designated owner-only type refusal differs')
        closed(out,code);counts[code]+=1
        if Path(argv[0]).name in ('dng-component-controls','archive-reference-fault'):
            summaries.append(dict(command=argv,stdout=out['stdout']))
    if counts[2]!=4 or len(summaries)!=4:raise ValueError('both compiler normal and expected-negative outcomes required')
    return dict(calls=len(calls),zero=counts[0],expected_two=counts[2],summaries=summaries)


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact DNG controls plan required')
    packet=json.loads(raw)
    if packet['schema']!='unison-final-dng-component-plan/1' or packet['repository']!=str(ROOT) or sys.executable!=packet['interpreter']['path']:raise ValueError('exact original suite context required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('DNG source changed '+name)
        if sha(packet['interpreter']['path'],64*1048576)!=packet['interpreter']['sha256']:raise ValueError('interpreter changed')
        for ref in packet['compilers'].values():
            if str(Path(ref['invocation']).resolve())!=ref['path'] or sha(ref['path'],128*1048576)!=ref['sha256']:raise ValueError('compiler alias/artifact changed')
    sources();root=Path(packet['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-dng-components-'):raise ValueError('fresh private controls workspace required')
    policy=ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
    if authorized_unison_tokens(read_bytes(str(policy),1048576))!=tuple(range(8)):raise ValueError('standing8 differs')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd');bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
    if bundle is None:return 2
    io,cpu=bundle;store=None;attempted=False;settled=False;nested_verified=False
    try:
        root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));sources()
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1');command=[sys.executable,'-B',str(ROOT/'tests/semantic/dng_component_controls.py'),'--compiler-scope','both']
        resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),command=command,resource_rows=resources,SDK_or_Photo_calls=0,purpose='Current original two-compiler DNG partition/cache/archive-reference fault/ablation suite'))
        print('DNG_COMPONENT_START',os.getpid(),str(root),flush=True);attempted=True
        child=start(command,env,pass_fds=(*cpu.fds,*io.fds),capture_limit=262144);out=child.finish(time.monotonic()+600);store.write('RUNNER-CHILD.json',out);closed(out,out['returncode']);settled=True
        if out['returncode']!=0:raise ValueError('suite failed; preserve original outputs, no retry')
        directory=Path(out['stdout'].strip())
        if directory.parent!=Path('/private/tmp') or not directory.name.startswith('unison-dng-component-controls-'):raise ValueError('exact suite private output path required')
        path=directory/'RESULT.json';raw=read_bytes(str(path),16*1048576);result=json.loads(raw)
        if result['complete'] is not True or result['SDK_invoked'] is not False or result['media_payload_opened'] is not False:raise ValueError('complete non-SDK generated controls required')
        for name,digest in result['source_pins'].items():
            if not Path(name).is_relative_to(ROOT) or sha(name)!=digest:raise ValueError('suite source changed')
        audit=audit_calls(result);nested_verified=True
        if set(result['archive_reference_fault_builds'])!={'stock','ox'} or set(result['lookup_guard_ablations'])!={'stock','ox'}:raise ValueError('both publication fault/negative controls required')
        for label in ('stock','ox'):
            fault=result['archive_reference_fault_builds'][label]
            if fault['production_fault_switch'] is not False or fault['macro']!='fsync=unison_record_control_fsync' or sha(directory/label/'archive-reference-fault',64*1048576)!=fault['executable_sha256']:raise ValueError('test-only fault executable binding differs')
            if result['lookup_guard_ablations'][label]['production_source_modified'] is not False:raise ValueError('ablation mutated production')
        sources();store.write('RESULT.json',dict(complete=True,original_result=dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),audit=audit,source_pins=packet['source_pins'],SDK_or_Photo_calls=0,parent_tool_terminal_proved=False,scope='Original generated partition/privatecache/archive-reference publication fault and named-record ablation controls; not receiving/crash/physicalENOSPC/SDK/pixels'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('DNG_COMPONENT_CLOSED',audit['calls'],str(path),flush=True);return 0
    except BaseException as error:
        if isinstance(error,UnresolvedOwnership) or attempted and (not settled or not nested_verified):retain_after_record(lambda:print('DNG_COMPONENT_RETAIN',repr(error),str(root),flush=True))
        try:
            if store is not None and not store.closed:store.write('FAILED.json',dict(error=repr(error),runner_attempted=attempted,runner_settled=settled));store.close()
            for lease in (cpu,io):
                if not lease.closed:
                    if attempted and settled:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                    else:close_unstarted(lease)
        except BaseException as cleanup:retain_after_record(lambda:print('DNG_COMPONENT_CLOSE_RETAIN',repr(cleanup),repr(error),flush=True))
        raise

if __name__=='__main__':raise SystemExit(main())
