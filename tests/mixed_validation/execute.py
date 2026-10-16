"""Exact one-use admitted mixed-work parent/worker entry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

# Import the local plan before sibling test packages that also contain plan.py.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation.plan import commands,path
from mixed_validation.worker import execute_plan
from mixed_validation.artifacts import verify_sources,prepare_input,verify_input,verified_hash
from mixed_validation.boundary import bind,worker_argv
from camera_sdk_concurrency.persistence import save
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import unique_object
from shared_process_owner import retain_after_record
from shared_child import invoke
from mixed_validation.inventory import verify as verify_inventory

PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'


def checked_plan(plan_path,digest):
    path(plan_path)
    plan=document(plan_path,digest)
    commands(plan)
    verify_inventory(plan)
    return plan


def document(path,digest=None):
    """Read bounded metadata with one qualified close; never a media loader."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid()
                or before.st_nlink!=1 or not 0<before.st_size<=1048576):
            raise ValueError('bounded owned metadata required')
        raw=bytearray()
        while len(raw)<before.st_size:
            block=os.read(fd,min(65536,before.st_size-len(raw)))
            if not block:raise ValueError('short metadata read')
            raw.extend(block)
        stamp=lambda s:tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid'))
        if os.read(fd,1) or stamp(before)!=stamp(os.fstat(fd)) or stamp(before)!=stamp(os.lstat(path)):
            raise ValueError('metadata identity changed')
        if digest is not None and hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('frozen metadata SHA differs')
        return json.loads(raw,object_pairs_hook=unique_object)
    finally:close_descriptors([fd])


def worker(args,plan):
    commands(plan)
    if args.workspace!=plan['workspace']:raise ValueError('worker workspace differs')
    if sys.executable!=PYTHON:raise ValueError('qualified interpreter required')
    workspace=Path(args.workspace);until=time.monotonic()+3
    while True:
        try:start=document(workspace/'SHARED-START.json');break
        except FileNotFoundError:
            if time.monotonic()>=until:raise ValueError('actual owning parent START absent')
            time.sleep(.005)
    argv=worker_argv(plan,interpreter=PYTHON,plan_path=args.plan,plan_sha256=args.plan_sha256)
    binding=bind(plan,start,argv,interpreter=PYTHON,plan_path=args.plan,
                 plan_sha256=args.plan_sha256,parent_pid=os.getppid(),worker_pid=os.getpid())
    verified_hash(dict(path=PYTHON,sha256=PYTHON_SHA,bytes=os.lstat(PYTHON).st_size))
    records={};deadline=time.monotonic()+plan['limits']['observation_seconds']
    def prepare(index,command):records[index]=prepare_input(plan,index)
    def call(index,command,end):
        return invoke(command,dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',
                                   UNISON=str(workspace/plan['probes'][index]['label']/'state')),
                      min(end,time.monotonic()+plan['limits']['probe_seconds']),
                      pass_fds=binding['inherited_fds'])
    execute_plan(plan,deadline=deadline,prepare=prepare,invoke=call,
                 persist=lambda r:save(workspace,r),check_sources=lambda:verify_sources(plan),
                 verify_input=lambda index,command:verify_input(plan,index,records[index]))
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    for name in ('plan','plan-sha256'):parser.add_argument('--'+name,required=True)
    for name in ('workspace','admission','admission-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args();path(args.plan)
    plan=checked_plan(args.plan,args.plan_sha256)
    if not args.worker:
        if not args.admission or not args.admission_sha256 or args.workspace:
            raise ValueError('fresh pinned IO admission required for parent mode')
        workspace=Path(plan['workspace'])
        if os.path.lexists(workspace):raise ValueError('workspace consumed; no replay')
        from shared_dispatch import checked_io_request,run,MIXED_TARGET
        argv=worker_argv(plan,interpreter=sys.executable,plan_path=args.plan,plan_sha256=args.plan_sha256)
        admission=dict(path=args.admission,sha256=args.admission_sha256)
        checked_io_request(admission,MIXED_TARGET,argv,workspace,8)
        os.umask(0o077);workspace.mkdir(mode=0o700)
        return run(MIXED_TARGET,argv,workspace,8,io_admission=admission)
    if args.admission or args.admission_sha256:raise ValueError('worker consumes parent START only')
    path(args.workspace)
    if args.workspace!=plan['workspace']:raise ValueError('worker workspace differs')
    try:return worker(args,plan)
    except UnresolvedOwnership:raise
    except BaseException as error:
        # Existing journal may contain INTENT or OUTCOME; never replace it with
        # an invented no-call result after an invocation.
        if not os.path.lexists(Path(args.workspace)/'RESULT.json'):
            save(args.workspace,dict(schema='unison-mixed-validation-worker/1',complete=False,
                 phase='PREPARING_NO_CALL',invocations=[],failure=repr(error)))
        raise


if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='MIXED_OWNERSHIP_RETAINED',
            error=repr(error),retained_fds=error.retained_fds,
            uncertain_closes=getattr(error,'uncertain_closes',()))),file=sys.stderr,flush=True))
