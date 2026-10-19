"""Directed exact-native-mtime restoration guard regression; generated only."""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed
from final_clone_interruption_owner import can_close_failed_prefix
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from shared_child import start


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);a=parser.parse_args();raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact restored-mtime plan required')
    p=json.loads(raw)
    if p['schema']!='unison-restored-native-mtime-plan/1' or p['repository']!=str(ROOT) or sys.executable!=p['interpreter']['path']:raise ValueError('qualified generated guard test context required')
    def sources():
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('restored-mtime source changed '+name)
        if sha(p['interpreter']['path'],64*1048576)!=p['interpreter']['sha256']:raise ValueError('interpreter changed')
        for ref in p['prerequisites']:
            if sha(ref['path'],2*1048576)!=ref['sha256']:raise ValueError('prior actual native qualification changed')
        for job in p['jobs']:
            if str(Path(job['compiler']['invocation']).resolve())!=job['compiler']['path'] or sha(job['compiler']['path'],128*1048576)!=job['compiler']['sha256']:raise ValueError('compiler identity changed')
            for ref in (*job['objects'],*job['compiler']['library_pins']):
                if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('qualified native input changed')
    sources();root=Path(p['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-restored-mtime-'):raise ValueError('new generated namespace required')
    root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));io=cpu=None;attempted=False;active=False
    try:
        indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
        if indexes!=tuple(range(8)):raise ValueError('standing8 required')
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd');bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,indexes)
        if bundle is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
        io,cpu=bundle;sources();resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resources,compiler_jobs=1,SDK_or_Photo_calls=0));print('RESTORED_MTIME_START',os.getpid(),str(root),flush=True)
        calls=[];runs=[];deadline=time.monotonic()+180
        for job in p['jobs']:
            work=root/job['label'];work.mkdir(mode=0o700);sources()
            for ref in job['objects']:shutil.copyfile(ref['path'],work/Path(ref['path']).name)
            for name in ('restored_mtime_stubs.c','restored_mtime.ml'):shutil.copyfile(ROOT/'tests/final_publication'/name,work/name)
            environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OCAMLLIB=str(Path(job['compiler']['path']).parent.parent/'lib/ocaml'))
            for key in ('OCAMLPARAM','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):environment.pop(key,None)
            compiler=job['compiler']['invocation'];commands=[[compiler,'-I','+unix','-c','restored_mtime_stubs.c'],[compiler,'-I','+unix','unix.cmxa','finalPublication.cmx','fixture.o','restored_mtime_stubs.o','restored_mtime.ml','-o','mtime-test'],[str(work/'mtime-test'),str(work)]];local=[]
            for index,argv in enumerate(commands):
                if time.monotonic()+65>=deadline:raise TimeoutError('no new child near guard-test observation end')
                attempted=active=True;previous=Path.cwd()
                try:os.chdir(work);child=start(argv,environment,pass_fds=(*cpu.fds,*io.fds))
                finally:os.chdir(previous)
                out=child.finish(time.monotonic()+60);pin=store.write('call-%02d.json'%len(calls),out);calls.append(pin);local.append(pin);closed(out,out['returncode']);active=False
                expected=2 if index==2 and job['negative'] else 0
                if out['returncode']!=expected:raise ValueError('unexpected guard-test child outcome')
            if job['negative']:
                if 'Failure("restored-mtime mutation published")' not in out['stderr']:raise ValueError('designated restored-mtime guard ablation failed for other reason')
            elif 'PASS 2 restored-native-mtime publication mutation cases' not in out['stdout'] or out['stdout'].count('native_mtime=1700000000.000000000 unchanged native_ctime=')!=2:raise ValueError('both exact-native-time fixture cases required')
            record=dict(label=job['label'],negative=job['negative'],calls=local,executable=dict(path=str(work/'mtime-test'),sha256=sha(work/'mtime-test',64*1048576)),test_child=out['client_cleanup']);store.write(job['label']+'-RESULT.json',record);runs.append(record);print('RESTORED_MTIME_RUN_CLOSED',job['label'],flush=True)
        sources();store.write('RESULT.json',dict(complete=True,calls=calls,runs=runs,source_pins=p['source_pins'],SDK_or_Photo_calls=0,parent_tool_terminal_proved=False,scope='Two actual same-size byte changes with exact native mtime restored/ctime changed; candidate/target guards and isolated candidate-guard ablation eachcompiler. Not an uncooperative-writer check-to-rename race cure.'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);print('RESTORED_MTIME_CLOSED',str(root),flush=True);return 0
    except BaseException as error:
        if can_close_failed_prefix(active=active,error=error):
            try:
                store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),attempted_children_settled=True));store.close()
                for lease in (cpu,io):
                    if lease is not None and not lease.closed:
                        if attempted:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                        else:close_unstarted(lease)
            except BaseException as failure:retain_after_record(lambda:print('MTIME_CLOSE_RETAIN',repr(failure),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('MTIME_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
