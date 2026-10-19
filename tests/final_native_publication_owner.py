"""Retained current native publication/lease original drivers, two compilers."""
import argparse,contextlib,hashlib,io,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed
from final_clone_interruption_owner import can_close_failed_prefix
from native_publication_driver_bridge import Commands,Temporary,driver_source
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from shared_child import start


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);a=parser.parse_args();raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact native publication plan required')
    p=json.loads(raw)
    if p['schema']!='unison-final-native-publication-plan/1' or p['repository']!=str(ROOT) or sys.executable!=p['interpreter']['path']:raise ValueError('qualified native original-driver context required')
    def sources():
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('native publication source changed '+name)
        if sha(p['interpreter']['path'],64*1048576)!=p['interpreter']['sha256']:raise ValueError('interpreter changed')
        for job in p['compilers']:
            if str(Path(job['invocation']).resolve())!=job['path'] or sha(job['path'],128*1048576)!=job['sha256']:raise ValueError('compiler alias/artifact changed')
            for ref in job['library_pins']:
                if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('compiler library changed')
    sources();root=Path(p['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-native-publish-'):raise ValueError('new private generated namespace required')
    root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));io_lease=cpu=None;attempted=False;active=False
    try:
        indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
        if indexes!=tuple(range(8)):raise ValueError('standing8 required')
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd');bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,indexes)
        if bundle is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
        io_lease,cpu=bundle;sources();resources=[]
        for fd in (*cpu.fds,*io_lease.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resources,compiler_jobs=1,SDK_or_Photo_calls=0))
        print('NATIVE_PUBLICATION_START',os.getpid(),str(root),flush=True);deadline=time.monotonic()+600;calls=[];runs=[]
        for job in p['compilers']:
            for mode in ('normal','timed','candidate-negative','producer-negative','lease'):
                sources();label=job['label']+'-'+mode;work=root/label
                script=ROOT/('tests/clone_lease/run.py' if mode=='lease' else 'tests/final_publication/run.py');original=read_bytes(str(script),65536).decode();filtered=driver_source(original);capture=io.StringIO();local_calls=[]
                def invoke(argv,environment,cwd,seconds):
                    nonlocal attempted,active
                    if time.monotonic()+65>=deadline:raise TimeoutError('no new child near native suite observation end')
                    attempted=active=True;previous=Path.cwd()
                    try:
                        if cwd is not None:os.chdir(cwd)
                        child=start(argv,dict(os.environ) if environment is None else environment,pass_fds=(*cpu.fds,*io_lease.fds))
                    finally:os.chdir(previous)
                    out=child.finish(min(deadline,time.monotonic()+seconds));name='call-%03d.json'%len(calls);pin=store.write(name,out);calls.append(pin);local_calls.append(pin);closed(out,out['returncode']);active=False
                    return out
                bridge=Commands(job['invocation'],work,invoke);temporary=Temporary(work,'unison-clone-lease-' if mode=='lease' else 'unison-final-publication-')
                argv=[str(script),'--ocamlopt',job['invocation']]
                if mode!='lease':argv+=['--keep-work']
                if mode=='timed':argv+=['--timed']
                if mode=='candidate-negative':argv+=['--negative-control']
                if mode=='producer-negative':argv+=['--producer-negative-control']
                namespace=dict(__name__='__main__',__file__=str(script),subprocess=bridge,tempfile=temporary);previous_argv=sys.argv
                try:
                    sys.argv=argv
                    with contextlib.redirect_stdout(capture):exec(compile(filtered,str(script),'exec'),namespace)
                finally:sys.argv=previous_argv
                log=capture.getvalue()
                if len(log.encode())>262144:raise ValueError('bounded original driver log required')
                store.write(label+'-LOG.json',dict(text=log,original_driver_sha256=sha(script),filtered_import_binding_sha256=hashlib.sha256(filtered.encode()).hexdigest()))
                native_calls=[]
                for pin in local_calls:
                    out=store.read_json(pin['name'],expected_sha256=pin['sha256'])
                    if Path(out['command'][0]).name in ('publication-test','lease-test'):native_calls.append(out)
                    elif out['returncode']!=0:raise ValueError('compiler/metadata call failed')
                if len(native_calls)!=1:raise ValueError('one exact original test program required')
                out=native_calls[0];expected=2 if mode in ('candidate-negative','producer-negative') else 0
                closed(out,expected)
                if mode=='candidate-negative' and ('PASS negative control: late candidate mutation detected by harness' not in log or 'candidate mutation was published' not in out['stderr']):raise ValueError('designated candidate baseline negative differs')
                if mode=='producer-negative' and ('PASS producer negative control: original output descriptor is required' not in log or 'wrong producer descriptor admitted' not in out['stderr']):raise ValueError('designated producer FD negative differs')
                if mode=='lease' and 'independent native/injected bridge tests passed' not in out['stdout']:raise ValueError('native lease suite not qualified')
                if mode in ('normal','timed') and ('PASS' not in out['stdout'] or 'SKIP' in log):raise ValueError('native publication suite skipped')
                artifacts=[]
                for path in sorted(work.iterdir()):
                    if path.is_file() and path.suffix in ('.ml','.mli','.c','.cmx','.cmi','.o') or path.name in ('publication-test','lease-test'):
                        artifacts.append(dict(path=str(path),sha256=sha(path,64*1048576)))
                record=dict(compiler=job['label'],mode=mode,driver=str(script),driver_argv=argv,calls=local_calls,test_pid=out['client_cleanup']['pid'],test_exit=expected,log_record=label+'-LOG.json',artifacts=artifacts)
                store.write(label+'-RESULT.json',record);runs.append(record);print('NATIVE_PUBLICATION_RUN_CLOSED',label,len(local_calls),flush=True)
        sources();store.write('RESULT.json',dict(complete=True,runs=runs,calls=calls,source_pins=p['source_pins'],SDK_or_Photo_calls=0,parent_tool_terminal_proved=False,scope='Original current native publication ordinary/timed/two specific private guard ablations and native clone-lease bridge; not full transport/powerloss/physicalENOSPC/SDK/photos'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io_lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('NATIVE_PUBLICATION_CLOSED',len(calls),str(root),flush=True);return 0
    except BaseException as error:
        if can_close_failed_prefix(active=active,error=error):
            try:
                store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),native_attempted=attempted,attempted_children_settled=True));store.close()
                for lease in (cpu,io_lease):
                    if lease is not None and not lease.closed:
                        if attempted:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                        else:close_unstarted(lease)
            except BaseException as failure:retain_after_record(lambda:print('NATIVE_PUBLICATION_CLOSE_RETAIN',repr(failure),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('NATIVE_PUBLICATION_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
