"""Retained standalone SDK2768 fixture-writer build; never executes its output."""
import argparse,hashlib,json,os,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from batch_child import start
from final_profile_owner import sha,closed


def tool_sha(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if not(stat.S_ISREG(before.st_mode) and before.st_uid in (0,os.getuid()) and before.st_nlink>0 and 0<before.st_size<=512*1048576):raise ValueError('bounded installed tool required')
        digest=hashlib.sha256();at=0
        while at<before.st_size:
            data=os.read(fd,min(1048576,before.st_size-at))
            if not data:raise ValueError('short installed tool read')
            at+=len(data);digest.update(data)
        fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode)
        if os.read(fd,1) or fields(before)!=fields(os.fstat(fd)) or fields(before)!=fields(os.lstat(path)):raise ValueError('installed tool changed')
        return digest.hexdigest()
    finally:close_descriptors([fd])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);a=parser.parse_args()
    data=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(data).hexdigest()!=a.sha256:raise ValueError('build plan SHA differs')
    p=json.loads(data)
    if p['schema']!='unison-standalone-sdk2768-fixture-build-plan/1' or p['repository']!=str(ROOT) or sys.executable!=p['interpreter']['path']:raise ValueError('exact standalone builder context required')
    def artifacts():
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('build source changed '+name)
        for ref in (*p['tools'].values(),p['interpreter']):
            if tool_sha(ref['path'])!=ref['sha256']:raise ValueError('installed tool changed')
        if Path(p['environment']['CXX']).resolve()!=Path(p['tools']['clang++']['path']):raise ValueError('C++ invocation alias changed')
        if sha(p['preserved_validator']['path'],16*1048576)!=p['preserved_validator']['sha256']:raise ValueError('qualified2724validator changed')
    artifacts();ref=p['sdk_manifest'];raw=read_bytes(ref['path'],2*1048576)
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('unpacked SDK ancestry changed')
    sdk_manifest=json.loads(raw);sdk=Path(sdk_manifest['sdk_root']);source_parent=Path(ref['path']).parent/'extracted'
    def sdk_sources():
        for row in sdk_manifest['files']:
            path=source_parent/row['path'];s=path.lstat()
            if not(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and s.st_size==row['bytes']):raise ValueError('SDK source census changed')
            digest=sha(path,64*1048576) if s.st_size else hashlib.sha256(b'').hexdigest()
            if digest!=row['sha256']:raise ValueError('SDK source changed '+row['path'])
    root=Path(p['workspace'])
    if root.parent!=Path(ref['path']).parent or not root.name.startswith('fixture-build-owner-'):raise ValueError('fresh private build sibling required')
    policy=ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
    if authorized_unison_tokens(read_bytes(str(policy),1048576))!=tuple(range(8)):raise ValueError('standing8 differs')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd');bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
    if bundle is None:return 2
    io,cpu=bundle;store=None;attempted=False;settled=False
    try:
        root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));sdk_sources();artifacts()
        for name in ('home','tmp'):(root/name).mkdir(mode=0o700)
        env=dict(PATH=p['environment']['PATH'],HOME=str(root/'home'),TMPDIR=str(root/'tmp'),LANG='C',LC_ALL='C',PYTHONNOUSERSITE='1',SDKROOT=p['environment']['SDKROOT'],CC=p['tools']['clang']['path'],CXX=p['environment']['CXX'],CMAKE_GENERATOR='Unix Makefiles',CMAKE_BUILD_PARALLEL_LEVEL='2')
        command=[p['interpreter']['path'],'-B',str(ROOT/'tools/adobe-validator/build.py'),'--sdk-root',str(sdk),'--build-dir',str(root/'build'),'--jobs','2','--fixture-writer-build-only']
        resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),command=command,environment=env,resource_rows=resources,compiler_jobs=2,SDK_fixture_or_validator_calls=0,scope='SDK dependencies/fixturewriter compile-link only; standard configure toolchain probes may execute'))
        print('FIXTURE_BUILD_START',os.getpid(),str(root),flush=True);attempted=True
        child=start(command,env,pass_fds=(*cpu.fds,*io.fds),capture_limit=4*1048576);out=child.finish(time.monotonic()+900)
        store.write('BUILDER-CHILD.json',out);closed(out,out['returncode']);settled=True
        if out['returncode']!=0:raise ValueError('fixture build failed; preserve source/output and normal failed prefix')
        manifest_path=root/'build/fixture-writer-build-manifest.json';manifest=json.loads(read_bytes(str(manifest_path),8*1048576))
        if not(manifest['sdk_root']==str(sdk) and manifest['reviewed_release']['build']==2768 and manifest['build_id']=='unison-sdk171-2768-fixture-writer-build-v1' and manifest['validator_written'] is False and manifest['runtime_qualified'] is False and manifest['SDK_fixture_generation_calls']==0):raise ValueError('fixture-only build manifest differs')
        if (root/'build/build-manifest.json').exists() or (root/'build/unison-adobe-validator').exists():raise ValueError('unexpected validator artifact')
        if sha(manifest['executable'],32*1048576)!=manifest['executable_sha256']:raise ValueError('fixturewriter binary hash differs')
        for name,digest in manifest['linked_objects'].items():
            if sha(name,128*1048576)!=digest:raise ValueError('linked SDK object/library differs')
        sdk_sources();artifacts();store.write('RESULT.json',dict(complete=True,build_manifest=dict(path=str(manifest_path),sha256=sha(manifest_path,8*1048576),bytes=manifest_path.stat().st_size),fixture_writer=dict(path=manifest['executable'],sha256=manifest['executable_sha256']),linked_artifacts=len(manifest['linked_objects']),SDK_source_files=len(sdk_manifest['files']),SDK_source_bytes=sum(r['bytes'] for r in sdk_manifest['files']),source_pins=p['source_pins'],qualified2724validator_unchanged=True,fixture_writer_or_validator_executions=0,parent_tool_terminal_proved=False,scope='Build-only2768fixturewriter; not newvalidator/fixture/decode/merge/runtimequalification'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('FIXTURE_BUILD_CLOSED',str(root),manifest['executable_sha256'],flush=True);return 0
    except BaseException as error:
        if isinstance(error,UnresolvedOwnership) or attempted and not settled:retain_after_record(lambda:print('FIXTURE_BUILD_RETAIN',repr(error),str(root),flush=True))
        try:
            if store is not None and not store.closed:store.write('FAILED.json',dict(error=repr(error),child_attempted=attempted,child_settled=settled,no_fixture_execution=True));store.close()
            for lease in (cpu,io):
                if not lease.closed:
                    if attempted and settled:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                    else:close_unstarted(lease)
        except BaseException as cleanup:retain_after_record(lambda:print('FIXTURE_BUILD_CLOSE_RETAIN',repr(cleanup),repr(error),flush=True))
        raise

if __name__=='__main__':raise SystemExit(main())
