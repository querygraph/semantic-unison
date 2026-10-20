"""Finite original tiny worker controls; inherited standing8 and EXglobal only.

Source preparation never reserves Photo. Acquire immediately before execution;
ordinary known-settled failures close, uncertain child/FD ownership retains.
"""
import argparse,contextlib,hashlib,io,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed
from sdk_fixture_build_owner import tool_sha
from final_clone_interruption_owner import can_close_failed_prefix
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from shared_child import start


def driver_source(original):
    # Inject only process/tempdir ownership, preserve original fixture bodies.
    for line in ('import tempfile\n','from shared_child import invoke\n'):
        if original.count(line)!=1:raise ValueError('original worker driver import changed')
        original=original.replace(line,'',1)
    return original


class Temporary:
    def __init__(self,path):self.path=path;self.used=False
    def mkdtemp(self,*,prefix,dir):
        if self.used or prefix!='unison-component-worker-controls-' or dir!='/private/tmp':
            raise ValueError('one exact generated controls directory required')
        self.path.mkdir(mode=0o700);self.used=True
        return str(self.path)


def command_check(command,expected):
    if (type(command) is not list or any(type(x) is not str or not x for x in command)
            or command!=expected):raise ValueError('frozen original child command differs')


def audit_calls(calls,expected):
    if len(calls)!=len(expected) or len(calls)!=14:raise ValueError('all fourteen original calls required')
    pids=[];summaries=[]
    for out,argv in zip(calls,expected):
        command_check(out['command'],argv);closed(out,0)
        c=out['client_cleanup'];pid=c['pid']
        if (type(pid) is not int or not 0<pid<2**31 or pid in pids
                or out['aggregate_or_parent_terminal_proved'] is not False
                or out['io_cpu_release_authorized'] is not False):raise ValueError('distinct child/non-authorizing producer required')
        pids.append(pid)
        name=Path(argv[0]).name
        if name=='late_cancel':
            for mode in ('success','cancel','shutdown'):
                if f'PASS completed-before-owner {mode}:' not in out['stdout']:raise ValueError('late delivery mode missing')
        if name=='restored_mutation' and 'PASS active worker same-size mutation with exact restored native mtime refused;' not in out['stdout']:
            raise ValueError('mutation refusal proof missing')
        if name in ('components','late_cancel','restored_mutation'):summaries.append(dict(command=argv,stdout=out['stdout']))
    if len(summaries)!=6:raise ValueError('both compilers/all three programs required')
    return dict(calls=len(calls),distinct_children=pids,summaries=summaries)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);a=parser.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact worker state plan required')
    p=json.loads(raw)
    if p['schema']!='unison-final-worker-state-plan/1' or p['repository']!=str(ROOT) or sys.executable!=p['interpreter']['path']:raise ValueError('qualified original worker context required')
    root=Path(p['workspace']);work=root/'original';expected=p['commands']
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-worker-state-') or len(expected)!=14:raise ValueError('finite fresh private worker namespace required')
    def sources():
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('worker source changed '+name)
        for ref in p['artifact_pins']:
            if sha(ref['path'],128*1048576)!=ref['sha256']:raise ValueError('linked artifact/build/library changed '+ref['path'])
        if sha(p['interpreter']['path'],64*1048576)!=p['interpreter']['sha256']:raise ValueError('interpreter changed')
        for tool in p['installed_tools']:
            if str(Path(tool['invocation']).resolve())!=tool['path'] or tool_sha(tool['path'])!=tool['sha256']:raise ValueError('installed C tool changed')
        for job in p['compilers']:
            if str(Path(job['invocation']).resolve())!=job['path']:raise ValueError('compiler alias changed')
    sources();root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));cpu=io_lease=None;active=False;attempted=False;calls=[];pins=[]
    try:
        policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
        if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('exact standing8 policy required')
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
        if bundle is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
        io_lease,cpu=bundle;sources();resources=[]
        for fd in (*cpu.fds,*io_lease.fds):
            st=os.fstat(fd);resources.append(dict(fd=fd,device=st.st_dev,inode=st.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resources,compiler_jobs=1,environment=p['environment'],SDK_or_Photo_calls=0))
        print('WORKER_STATE_START',os.getpid(),str(root),flush=True);deadline=time.monotonic()+300
        def invoke(argv,environment,child_deadline):
            nonlocal active,attempted
            if len(calls)>=len(expected):raise ValueError('extra child refused')
            command_check(argv,expected[len(calls)])
            if time.monotonic()+65>=deadline:raise TimeoutError('no new worker child near observation end')
            active=attempted=True
            child=start(argv,dict(environment,**p['environment']),pass_fds=(*cpu.fds,*io_lease.fds),capture_limit=262144)
            out=child.finish(min(deadline,child_deadline));pin=store.write('call-%02d.json'%len(calls),out);pins.append(pin);calls.append(out)
            closed(out,out['returncode']);active=False
            return out
        script=ROOT/'tests/workers/component_controls.py';original=read_bytes(str(script),65536).decode();filtered=driver_source(original)
        namespace=dict(__name__='__main__',__file__=str(script),tempfile=Temporary(work),invoke=invoke);old=sys.argv;log=io.StringIO()
        argv=[str(script),'--stock-build',p['build_receipts']['stock'],'--ox-build',p['build_receipts']['ox'],'--state-controls']
        try:
            sys.argv=argv
            with contextlib.redirect_stdout(log):exec(compile(filtered,str(script),'exec'),namespace)
        finally:sys.argv=old
        if log.getvalue().strip()!=str(work):raise ValueError('original output directory binding differs')
        result_raw=read_bytes(str(work/'RESULT.json'),16*1048576);result=json.loads(result_raw)
        if not (result['complete'] is True and result['state_controls'] is True and result['SDK_invoked'] is False and result['real_media_opened'] is False and result['calls']==calls):raise ValueError('original suite result differs')
        for name,digest in result['source_pins'].items():
            if not Path(name).is_relative_to(ROOT) or p['source_pins'].get(str(Path(name).relative_to(ROOT)))!=digest:raise ValueError('original source binding differs')
        expected_artifacts={x['path']:x['sha256'] for x in p['artifact_pins']}
        for name,digest in result['linked_artifacts'].items():
            if expected_artifacts.get(name)!=digest:raise ValueError('original linked object not frozen')
        audit=audit_calls(calls,expected);sources()
        artifacts=[]
        for label in ('stock','ox'):
            for relative in ('components','late_cancel/late_cancel','restored_mutation/restored_mutation','restored_mutation/restored_mtime_stubs.o'):
                path=work/label/relative;artifacts.append(dict(path=str(path),sha256=sha(path,64*1048576)))
        store.write('RESULT.json',dict(complete=True,audit=audit,calls=pins,artifacts=artifacts,original_result=dict(path=str(work/'RESULT.json'),bytes=len(result_raw),sha256=hashlib.sha256(result_raw).hexdigest()),source_pins=p['source_pins'],SDK_or_Photo_calls=0,parent_tool_terminal_proved=False))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io_lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('WORKER_STATE_CLOSED',len(calls),str(root),flush=True);return 0
    except BaseException as error:
        if can_close_failed_prefix(active=active,error=error):
            try:
                store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),attempted_children_settled=True,calls=pins));store.close()
                for lease in (cpu,io_lease):
                    if lease is not None and not lease.closed:
                        if attempted:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                        else:close_unstarted(lease)
            except BaseException as failure:retain_after_record(lambda:print('WORKER_STATE_CLOSE_RETAIN',repr(failure),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('WORKER_STATE_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
