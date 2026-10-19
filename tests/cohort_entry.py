"""One admitted auto-worker cohort: retained shared8/EXglobal owner path.

The plan can describe larger cohorts; this entry deliberately refuses them
until a separately reviewed temporary-borrow owner exists. No silent clipping.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'bench/sync'))
import cohort_plan as C
import auto_cohort as A
from cached_benchmark.contract import read_bytes, document, PYTHON, PYTHON_SHA
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership, require, unique_object
from shared_process_owner import retain_after_record
from sdk_host_matrix.shared_binding import verify

TARGET = 'sync-auto-cohort'
COMPILERS = {'stock':'/Users/alexy/.opam/default/bin/ocamlopt.opt',
             'ox':'/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt'}


def checked_plan(path, sha):
    plan = C.checked_metadata(path,sha,repository=ROOT,execution_sources=C.execution_sources(ROOT))
    require(plan['interpreter']==PYTHON and plan['interpreter_sha256']==PYTHON_SHA,
            'qualified interpreter required')
    require(plan['artifact']['compiler']==COMPILERS[plan['cohort']['label']],
            'exact stock/Ox compiler selection required')
    require(all(str(Path(plan['artifact'][key]).resolve())==plan['artifact'][key]
                for key in ('binary','compiler')), 'canonical executable paths required')
    return plan


def worker_argv(plan, path, sha):
    return [plan['interpreter'],str(ROOT/'tests/cohort_entry.py'),'--worker','--plan',str(path),
            '--plan-sha256',sha,'--workspace',plan['workspace']]


def require_shared8(plan):
    require(plan['cohort']['reserved_credits']==8 and plan['cpu_token_indexes']==list(range(8))
            and plan['requires_temporary_borrow'] is False,
            'larger cohort requires a separately coordinated temporary-borrow owner')


def write(path,value):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    require(len(raw)<=1048576,'bounded cohort owner metadata required')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        at=0
        while at<len(raw):
            n=os.write(fd,raw[at:]);require(n>0,'metadata write stalled');at+=n
        os.fsync(fd)
    finally:
        close_descriptors([fd])


def binding(plan,command,workspace,*,parent_pid,worker_pid):
    start=document(workspace/'SHARED-START.json')
    verify(start,command,parent_pid=parent_pid,worker_pid=worker_pid,target=TARGET)
    return start


def read_result(path):
    return json.loads(read_bytes(path,16*1048576),object_pairs_hook=unique_object)


def audit_result(result,plan):
    if result.get('cohort_prebenchmark_failure') is True:
        require(result.get('complete') is False and result.get('invocations')==[]
                and result.get('benchmark_entered') is False
                and type(result.get('failure')) is str and bool(result['failure']),
                'exact prebenchmark failure proof required')
        return dict(attempted_cli_invocations=0,functional_status='PRE_BENCHMARK_FAILED',
                    external_children_settled=True,scope='source-bound metadata-only prefix, not parent terminal')
    root=result.get('temporary_directory')
    require(type(root) is str and Path(root).parent==Path('/private/tmp')
            and Path(root).name.startswith('unison-sync-bench-'), 'bounded synthetic fixture root required')
    if result.get('complete') is True:
        proof=A.audit_bound(result,plan['cohort'],plan['artifact'],fixture_root=root)
        return dict(proof,functional_status='PASSED')
    require(type(result.get('failure')) is str and bool(result['failure']), 'original failure required')
    return dict(A.audit_bound_prefix(result,plan['cohort'],plan['artifact'],fixture_root=root),
                functional_status='FAILED_PREFIX')


def parent_audit(result,command,workspace,*,parent_pid,worker_pid):
    plan=checked_plan(command[4],command[6]);require_shared8(plan)
    require(command==worker_argv(plan,command[4],command[6]),'exact owner worker command differs')
    start=binding(plan,command,workspace,parent_pid=parent_pid,worker_pid=worker_pid)
    record=document(workspace/'COHORT-BINDING.json')
    require(record['parent_pid']==parent_pid and record['worker_pid']==worker_pid
            and record['inherited_resource_fds']==start['inherited_resource_fds'],
            'worker actual inherited binding differs')
    # No child can start on metadata-only prebenchmark failures. Otherwise
    # independently rebind the plan's current production/artifacts before close.
    if result.get('cohort_prebenchmark_failure'):
        failure=document(workspace/'COHORT-FAILURE.json')
        require(failure.get('benchmark_entered') is False and failure.get('error')==result.get('failure'),
                'prebenchmark failure record differs')
    else:
        C.verify_build(plan,document(plan['build_receipt']),repository=str(ROOT))
        C.verify_artifacts(plan)
    return audit_result(result,plan)


def worker(args,plan):
    workspace=Path(plan['workspace']);require_shared8(plan)
    require(sys.executable==plan['interpreter'] and args.workspace==str(workspace),'exact worker context required')
    command=worker_argv(plan,args.plan,args.plan_sha256)
    deadline=time.monotonic()+3
    while not (workspace/'SHARED-START.json').exists():
        require(time.monotonic()<deadline,'actual parent START absent');time.sleep(.005)
    start=binding(plan,command,workspace,parent_pid=os.getppid(),worker_pid=os.getpid())
    write(workspace/'COHORT-BINDING.json',dict(parent_pid=os.getppid(),worker_pid=os.getpid(),
          inherited_resource_fds=start['inherited_resource_fds']))
    entered=False
    try:
        C.verify_build(plan,document(plan['build_receipt']),repository=str(ROOT))
        C.verify_artifacts(plan)
        for name in ('home','tmp'):
            (workspace/name).mkdir(mode=0o700)
        os.environ.clear()
        os.environ.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',
                          HOME=str(workspace/'home'),TMPDIR=str(workspace/'tmp'))
        sys.argv=plan['launch_argv'][1:]
        entered=True
        runpy.run_path(str(ROOT/'bench/sync/run.py'),run_name='__main__')
        proof=audit_result(read_result(workspace/'RESULT.json'),plan)
        require(proof['functional_status']=='PASSED','cohort incomplete')
        write(workspace/'WORKER-COHORT-AUDIT.json',proof)
        return 0
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        write(workspace/'COHORT-FAILURE.json',dict(error=repr(error),benchmark_entered=entered))
        if not entered:
            write(workspace/'RESULT.json',dict(complete=False,cohort_prebenchmark_failure=True,
                  benchmark_entered=False,invocations=[],failure=repr(error)))
        # Once benchmark code has entered, absent/unknown journal evidence
        # deliberately forces parent retention, never an invented empty prefix.
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    for name in ('plan','plan-sha256'):
        parser.add_argument('--'+name,required=True)
    for name in ('workspace','admission','admission-sha256'):
        parser.add_argument('--'+name)
    args=parser.parse_args()
    plan=checked_plan(args.plan,args.plan_sha256);require_shared8(plan)
    if args.worker:
        require(not args.admission and not args.admission_sha256,'worker receives parent binding only')
        return worker(args,plan)
    require(args.admission and args.admission_sha256 and not args.workspace,'fresh exact IO admission required')
    workspace=Path(plan['workspace']);require(not os.path.lexists(workspace),'workspace consumed; no replay')
    from shared_dispatch import checked_io_request,run
    command=worker_argv(plan,args.plan,args.plan_sha256)
    admission=dict(path=args.admission,sha256=args.admission_sha256)
    checked_io_request(admission,TARGET,command,workspace,8)
    os.umask(0o077);workspace.mkdir(mode=0o700)
    return run(TARGET,command,workspace,8,io_admission=admission)


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='COHORT_OWNERSHIP_RETAINED',
            error=repr(error),retained_fds=list(error.retained_fds),
            uncertain_closes=list(getattr(error,'uncertain_closes',())))),flush=True))
