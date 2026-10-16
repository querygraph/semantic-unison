"""Exact fresh-admission entry point for original synthetic concurrent receiving."""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
from shared_io_pool import read_manifest
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from invocation import artifact_sha
from persistence import save
import worker
TARGET='synthetic-concurrent-receive'
PARAMETERS=dict(cpu_credits=8,endpoint_workers=3,cases=2,calls=2,synthetic_validator_calls=4,
    sdk_calls=0,observation_seconds=600,worker_seconds=570,per_call_seconds=120,
    declared_logical_io_bytes=8*1073741824,io_budget_enforced=False)
PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'

def require(b,s):
    if not b:raise ValueError(s)

def sources():
    paths=set(HERE.glob('*.py'))|set((ROOT/'bench/sync').glob('*.py'))
    for pkg in ['camera_sdk_receiving','private_camera_receiving']:paths.update((ROOT/'tests'/pkg).glob('*.py'))
    paths.add(ROOT/'tests/validation_process/records.py')
    paths.update(ROOT/'tests'/name for name in ['shared_cpu_pool.py','shared_io_pool.py','shared_process_owner.py','shared_dispatch.py','manual.py'])
    return {str(p):artifact_sha(p) for p in sorted(paths)}

def checked_plan(path,digest):
    require(Path(path).is_absolute() and Path(path).resolve()==Path(path),'canonical plan required')
    plan=read_manifest(path,digest)
    require(set(plan)=={'schema','workspace','parameters','execution_source_sha256','binaries','tool','transport_source_sha256','interpreter'},'exact synthetic plan fields required; no external input')
    require(plan['schema']=='unison-concurrent-synthetic-plan/1' and plan['parameters']==PARAMETERS
        and all(type(plan['parameters'][k]) is type(v) for k,v in PARAMETERS.items()),'fixed finite synthetic parameters required')
    require(plan['execution_source_sha256']==sources(),'current exact source closure differs')
    w=Path(plan['workspace'])
    require(w.parent==Path('/private/tmp') and w.name.startswith('u-crs-') and 8<len(w.name)<=32,'fresh short synthetic namespace required')
    require(sys.executable==PYTHON and set(plan['interpreter'])=={'path','sha256'}
        and plan['interpreter']['path']==PYTHON and type(plan['interpreter']['sha256']) is str
        and len(plan['interpreter']['sha256'])==64 and all(c in '0123456789abcdef' for c in plan['interpreter']['sha256']),'qualified interpreter pin required')
    require(set(plan['binaries'])=={'stock','ox'},'fixed compiler pair required')
    for label,item in plan['binaries'].items():
        require(set(item)=={'label','path','sha256'} and item['label']==label and Path(item['path']).is_absolute()
            and len(item['sha256'])==64 and all(c in '0123456789abcdef' for c in item['sha256']),'exact binary pins required')
    tool=HERE/'fake_validator.py'
    require(type(plan['tool'].get('threads')) is int and plan['tool']==dict(path=str(tool),sha256=artifact_sha(tool),build_id=worker.BUILD,threads=1),'only pinned original fake validator allowed')
    require(plan['transport_source_sha256']=={n:plan['execution_source_sha256'][str(ROOT/'bench/sync'/n)] for n in worker.SCRIPT_NAMES},'exact copied transport source pins required')
    return plan

def child_argv(path,digest,workspace):
    return [sys.executable,str(HERE/'execute.py'),'--worker','--plan',str(path),'--plan-sha256',digest,'--workspace',str(workspace)]

def worker_entry(args,plan):
    w=Path(args.workspace);require(str(w)==plan['workspace'],'worker namespace differs')
    end=time.monotonic()+3
    while True:
        try:start=read_manifest(w/'SHARED-START.json',artifact_sha(w/'SHARED-START.json'));break
        except (OSError,ValueError):
            require(time.monotonic()<end,'actual parent START missing');time.sleep(.005)
    require(start['owner_pid']==os.getppid() and start['child_pid']==os.getpid()
        and start['target']==TARGET and start['command']==child_argv(args.plan,args.plan_sha256,w)
        and start['cpu_credits']==8 and start['token_indexes']==list(range(8)) and start['io_mode']=='EX_GLOBAL','actual parent/resource/command binding differs')
    fds=start['inherited_resource_fds'];require(len(fds)==9 and len({r['fd'] for r in fds})==9,'nine inherited descriptions required')
    for row in fds:
        st=os.fstat(row['fd']);require((st.st_dev,st.st_ino)==(row['device'],row['inode']),'inherited FD identity differs')
    require(artifact_sha(PYTHON)==plan['interpreter']['sha256'],'actual interpreter changed under IO grant')
    worker.execute(plan,w,time.monotonic()+570,persist=lambda value:save(w,value))
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ['plan','plan-sha256']:p.add_argument('--'+flag,required=True)
    for flag in ['admission','admission-sha256','workspace']:p.add_argument('--'+flag)
    p.add_argument('--worker',action='store_true');args=p.parse_args()
    plan=checked_plan(args.plan,args.plan_sha256)
    if args.worker:
        try:return worker_entry(args,plan)
        except UnresolvedOwnership:raise
        except BaseException as error:
            w=Path(plan['workspace'])
            if not (w/'RESULT.json').exists():
                save(w,dict(schema='unison-concurrent-synthetic-worker/1',complete=False,
                    phase='PREPARING_NO_CALL',cases=[],invocations=[],sdk_validation_claimed=False,
                    semantic_eligibility_claimed=False,failure=repr(error)))
            raise
    require(args.admission and args.admission_sha256 and not args.workspace,'fresh exact parent admission required')
    w=Path(plan['workspace']);require(not w.exists() and not w.is_symlink(),'namespace used; no replay')
    from shared_dispatch import checked_io_request,run
    argv=child_argv(args.plan,args.plan_sha256,w);admission=dict(path=args.admission,sha256=args.admission_sha256)
    checked_io_request(admission,TARGET,argv,w,8)
    os.umask(0o077);w.mkdir(mode=0o700)
    return run(TARGET,argv,w,8,io_admission=admission)

if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='UNRESOLVED_RETAINED',error=repr(error),
            retained_fds=list(getattr(error,'retained_fds',())),uncertain_closes=list(getattr(error,'uncertain_closes',())))),file=sys.stderr,flush=True))
