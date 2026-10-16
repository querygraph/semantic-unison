"""Exact-admission parent/worker entrypoint. Never runs without a fresh grant."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'bench/sync'))
from shared_io_pool import read_manifest
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from artifact_pins import stable_sha
import worker

SOURCE=Path('/private/tmp/unison-dng-da-copy-57c830f336da4ef099150958b2f3d666/source-clone.DNG')
PARAMETERS={'cpu_credits':8,'endpoint_workers':2,'cases':2,'calls':6,
            'observation_seconds':600,'per_call_seconds':60,
            'declared_logical_io_bytes':16*1073741824,'io_budget_enforced':False,
            'adobe_validation':'off','full_copy_fallback':False}


def require(value,reason):
    if not value:raise ValueError(reason)


def sources():
    paths=set(HERE.glob('*.py'))|set((ROOT/'bench/sync').glob('*.py'))
    paths.update(ROOT/'tests'/name for name in (
        'shared_cpu_pool.py','shared_io_pool.py','shared_process_owner.py','shared_dispatch.py','manual.py'))
    return {str(p):stable_sha(p) for p in sorted(paths)}


def checked_plan(path,digest):
    require(Path(path).is_absolute() and Path(path).resolve()==Path(path),'canonical absolute plan required')
    value=read_manifest(path,digest)
    require(value['schema']=='unison-camera-receiving-plan/1'
            and value['parameters']==PARAMETERS
            and all(type(value['parameters'][k]) is type(v) for k,v in PARAMETERS.items()),
            'fixed receiving scope differs')
    require(value['execution_source_sha256']==sources(),'exact receiving source closure differs')
    require(Path(value['source']['path'])==SOURCE
            and value['source']['identity']['st_size']==193851848
            and value['source']['historical_sha256']=='1a4f578ee6f23730afec8495c90b37f5272042331f3375d332a9065ce5bb3ee2',
            'fixed retained Unison clone ancestry required')
    identity=value['source']['identity']
    require(set(identity)==set(worker.case.FIELDS)
            and all(type(v) is int for v in identity.values())
            and identity['st_mode']==0o100400 and identity['st_nlink']==1
            and identity['st_uid']==os.getuid(),'exact readonly native source identity required')
    workspace=Path(value['workspace'])
    require(workspace.parent==Path('/private/tmp') and workspace.name.startswith('u-cr-')
            and 8<len(workspace.name)<=32,'fresh short receiving workspace required')
    require(set(value['binaries'])=={'stock','ox'},'exact compiler binary pair required')
    for label,item in value['binaries'].items():
        require(item['label']==label and Path(item['path']).is_absolute()
                and len(item['sha256'])==64 and all(c in '0123456789abcdef' for c in item['sha256']),
                'pinned binary record required')
    return value


def child_argv(plan_path,plan_sha,workspace):
    return [sys.executable,str(Path(__file__).resolve()),'--worker','--plan',str(plan_path),
            '--plan-sha256',plan_sha,'--workspace',str(workspace)]


def worker_entry(args,plan):
    workspace=Path(args.workspace)
    require(workspace==Path(plan['workspace']),'worker workspace differs')
    marker=workspace/'SHARED-START.json';deadline=time.monotonic()+3
    while True:
        try:
            start=read_manifest(marker,stable_sha(marker))
            break
        except (OSError,ValueError):
            require(time.monotonic()<deadline,'live shared parent START missing or incomplete')
            time.sleep(.005)
    require(start['owner_pid']==os.getppid() and start['child_pid']==os.getpid()
            and start['target']=='camera-receive' and start['cpu_credits']==8
            and start['io_mode']=='EX_GLOBAL' and start['token_indexes']==list(range(8))
            and start['command']==child_argv(args.plan,args.plan_sha256,workspace),
            'worker actual parent/command/resource binding differs')
    descriptors=start['inherited_resource_fds']
    require(len(descriptors)==9 and len({r['fd'] for r in descriptors})==9,
            'nine inherited IO/CPU descriptions required')
    for row in descriptors:
        observed=os.fstat(row['fd'])
        require((observed.st_dev,observed.st_ino)==(row['device'],row['inode']),
                'inherited resource description identity differs')
    with (workspace/'EXECUTOR-START.json').open('x') as out:
        json.dump({'worker_pid':os.getpid(),'parent_pid':os.getppid()},out)
    try:
        worker.execute(plan,workspace,time.monotonic()+570)
        return 0
    except UnresolvedOwnership as error:
        def record():
            with (workspace/'WORKER-OWNERSHIP-RETAINED.json').open('x') as out:
                json.dump({'error':repr(error),'retained_fds':list(error.retained_fds),
                           'uncertain_fd':error.uncertain_fd},out)
        retain_after_record(record)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True)
    parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--admission')
    parser.add_argument('--admission-sha256')
    parser.add_argument('--workspace')
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    plan=checked_plan(args.plan,args.plan_sha256)
    if args.worker:
        try:
            return worker_entry(args,plan)
        except Exception as error:
            # Binding failure before worker.execute starts cannot have launched
            # transport. Preserve that precise phase rather than an absent result.
            result=Path(plan['workspace'])/'RESULT.json'
            if not result.exists():
                from run import save
                save(result,{'schema':'unison-camera-receiving-worker/1','complete':False,
                    'phase':'PREPARING_NO_TRANSPORT_DISPATCH','invocations':[],'cases':[],
                    'camera_validity_claimed':False,'semantic_eligibility_claimed':False,
                    'failure':repr(error)})
            raise
    require(args.admission and args.admission_sha256 and not args.workspace,
            'parent requires exact fresh IO admission')
    workspace=Path(plan['workspace'])
    require(not workspace.exists() and not workspace.is_symlink(),'workspace used; no replay')
    from shared_dispatch import checked_io_request,run
    argv=child_argv(args.plan,args.plan_sha256,workspace)
    admission={'path':args.admission,'sha256':args.admission_sha256}
    checked_io_request(admission,'camera-receive',argv,workspace,8)
    os.umask(0o077);workspace.mkdir(mode=0o700)
    return run('camera-receive',argv,workspace,8,io_admission=admission)


if __name__=='__main__':
    raise SystemExit(main())
