"""Exact-admission shared8 SDK matrix entry; no implicit or CPU-only native mode."""
import argparse,hashlib,json,os,re,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tests/camera_sdk_concurrency'))
from invocation import artifact_sha
from persistence import save
from shared_io_pool import read_manifest
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from shared_binding import verify,TARGET
from shared_plan import shared_matrix,REFERENCE,EXPERIMENTAL
from shared_kernel import Kernel
from shared_child import invoke
PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PARAMETERS=dict(cpu_credits=8,calls=12,inputs=3,owner_credits=2,native_thread_targets=[1,2,6],
    observation_seconds=600,worker_seconds=570,per_call_seconds=60,declared_logical_io_bytes=8*1073741824,io_budget_enforced=False,fixture_access='read-only-open-preserve-exact-metadata')
FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')
def require(v,s):
    if not v:raise ValueError(s)
def sources():
    paths=set((HERE).glob('*.py'))|set((ROOT/'bench/sync').glob('*.py'))
    for pkg in ['camera_sdk_concurrency','camera_sdk_receiving','private_camera_receiving']:paths.update((ROOT/'tests'/pkg).glob('*.py'))
    paths.add(ROOT/'tests/validation_process/records.py')
    paths.update(ROOT/'tests'/n for n in ['shared_cpu_pool.py','shared_io_pool.py','shared_process_owner.py','shared_dispatch.py','manual.py'])
    paths.update((ROOT/'tools/adobe-validator').glob('*.h'));paths.add(ROOT/'tools/adobe-validator/driver.cpp')
    return {str(p):artifact_sha(p) for p in sorted(paths)}
def checked_plan(path,digest):
    p=Path(path);require(p.is_absolute() and p.resolve()==p,'canonical plan required');d=read_manifest(p,digest)
    require(set(d)=={'schema','workspace','parameters','execution_source_sha256','tools','fixtures','host_memory_bytes','interpreter'},'exact SDK plan fields required')
    require(d['schema']=='unison-shared-sdk-host-plan/1' and d['parameters']==PARAMETERS
        and all(type(d['parameters'][k]) is type(v) for k,v in PARAMETERS.items())
        and all(type(x) is int for x in d['parameters']['native_thread_targets']),'fixed finite SDK limits required')
    require(sys.executable==PYTHON and d['interpreter']==dict(path=PYTHON,sha256='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'),'qualified interpreter required')
    require(d['execution_source_sha256']==sources(),'current source closure differs')
    w=Path(d['workspace']);require(w.parent==Path('/private/tmp') and w.name.startswith('u-shm-') and 8<len(w.name)<=32,'fresh short private namespace required')
    require(set(d['tools'])=={'reference','experimental'},'exact tool pair required')
    for label,build in [('reference',REFERENCE),('experimental',EXPERIMENTAL)]:
        item=d['tools'][label]
        require(set(item)=={'executable','sha256','build_id','manifest','manifest_sha256'} and item['build_id']==build,'exact versioned tool metadata required')
        require(all(type(item[k]) is str and re.fullmatch('[0-9a-f]{64}',item[k]) for k in ['sha256','manifest_sha256']),'exact tool hashes required')
        for k in ['executable','manifest']:
            q=Path(item[k]);require(q.is_absolute() and q.resolve()==q,'canonical tool paths required')
        m=read_manifest(item['manifest'],item['manifest_sha256'])
        require(m['executable']==item['executable'] and m['executable_sha256']==item['sha256'] and m['build_id']==build,'tool manifest binding differs')
        if label=='experimental':
            require(m['source_sha256']==artifact_sha(ROOT/'tools/adobe-validator/driver.cpp'),'experimental driver source differs')
            for name,h in m['adapter_headers_sha256'].items():
                require(Path(name).name==name and artifact_sha(ROOT/'tools/adobe-validator'/name)==h,'experimental header differs')
    require(type(d['fixtures']) is list and len(d['fixtures'])==3,'exact3fixtures required')
    for item in d['fixtures']:
        require(set(item)=={'codec','path','sha256','size','identity'},'exact fixture binding required')
        require(type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['sha256']),'exact fixture SHA required')
        q=Path(item['path']);require(q.is_absolute() and q.resolve()==q and q.is_relative_to('/private/tmp'),'private retained generated fixture path required')
        require(type(item['size']) is int and 0<item['size']<=128*1048576 and set(item['identity'])==set(FIELDS),'bounded fixture identity required')
        st=os.lstat(q);require(all(type(item['identity'][k]) is int and getattr(st,k)==item['identity'][k] for k in FIELDS),'fixture metadata changed')
        require(item['size']==st.st_size and st.st_nlink==1 and st.st_uid==os.getuid() and stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) in (0o400,0o644),'retained generated fixture mode/owner/type differs')
    require(type(d['host_memory_bytes']) is int and 0<d['host_memory_bytes']<=4*1073741824,'bounded covered allocator declaration required')
    shared_matrix(d['tools']['reference'],d['tools']['experimental'],d['fixtures'],d['host_memory_bytes'])
    return d

def child_argv(path,digest,workspace):return [sys.executable,str(HERE/'shared_execute.py'),'--worker','--plan',str(path),'--plan-sha256',digest,'--workspace',str(workspace)]
def worker(args,plan):
    w=Path(args.workspace);require(str(w)==plan['workspace'],'worker namespace differs');end=time.monotonic()+3
    while True:
        try:start=read_manifest(w/'SHARED-START.json',artifact_sha(w/'SHARED-START.json'));break
        except (OSError,ValueError):
            require(time.monotonic()<end,'actual owning parent START absent');time.sleep(.005)
    binding=verify(start,child_argv(args.plan,args.plan_sha256,w),parent_pid=os.getppid(),worker_pid=os.getpid())
    require(artifact_sha(PYTHON)==plan['interpreter']['sha256'],'interpreter changed under IO')
    for item in [*plan['tools'].values(),*plan['fixtures']]:
        require(artifact_sha(item.get('executable',item.get('path')))==item['sha256'],'tool/fixture SHA differs under IO')
    deadline=time.monotonic()+570
    def call(case):
        require(time.monotonic()+65<deadline,'insufficient next-call observation headroom')
        for item in plan['tools'].values():require(artifact_sha(item['executable'])==item['sha256'],'tool changed before call')
        for item in plan['fixtures']:
            st=os.lstat(item['path']);require(all(getattr(st,k)==v for k,v in item['identity'].items()),'fixture epoch changed before call')
        out=invoke(case['command'],dict(LANG='C',LC_ALL='C',PATH='/usr/bin:/bin'),min(deadline,time.monotonic()+60),pass_fds=binding['inherited_fds'])
        try:
            for item in plan['tools'].values():require(artifact_sha(item['executable'])==item['sha256'],'tool changed after call')
            for item in plan['fixtures']:
                st=os.lstat(item['path']);require(all(getattr(st,k)==v for k,v in item['identity'].items()),'fixture epoch changed after call')
        except UnresolvedOwnership:raise
        except BaseException as error:
            failure=RuntimeError('post-call binding failed: '+repr(error));failure.outcome=out
            raise failure from error
        return out
    Kernel(plan['tools']['reference'],plan['tools']['experimental'],plan['fixtures'],plan['host_memory_bytes']).execute(invoke=call,persist=lambda d:save(w,d))
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for f in ['plan','plan-sha256']:p.add_argument('--'+f,required=True)
    for f in ['admission','admission-sha256','workspace']:p.add_argument('--'+f)
    p.add_argument('--worker',action='store_true');a=p.parse_args();plan=checked_plan(a.plan,a.plan_sha256)
    w=Path(plan['workspace'])
    if a.worker:
        try:return worker(a,plan)
        except UnresolvedOwnership:raise
        except BaseException as error:
            if not (w/'RESULT.json').exists():save(w,dict(schema='unison-shared-sdk-kernel/1',complete=False,phase='PREPARING_NO_CALL',rows=[],invocations=[],resource_release_authorized=False,failure=repr(error)))
            raise
    require(a.admission and a.admission_sha256 and not a.workspace,'fresh exact IO admission required')
    require(not w.exists() and not w.is_symlink(),'namespace consumed; no replay')
    from shared_dispatch import checked_io_request,run
    argv=child_argv(a.plan,a.plan_sha256,w);ad=dict(path=a.admission,sha256=a.admission_sha256)
    checked_io_request(ad,TARGET,argv,w,8);os.umask(0o077);w.mkdir(mode=0o700)
    return run(TARGET,argv,w,8,io_admission=ad)
if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='SDK_SHARED_OWNERSHIP_RETAINED',error=repr(error),retained_fds=error.retained_fds,uncertain_closes=getattr(error,'uncertain_closes',()))),file=sys.stderr,flush=True))
