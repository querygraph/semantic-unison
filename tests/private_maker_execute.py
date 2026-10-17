"""Admitted slice worker, launched only by the retained shared dispatcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

from private_camera_receiving.close import close_descriptors
from private_maker_plan import check,worker_argv,TARGET,ROOT
from private_maker_slice import read_source,stamp
from private_maker_audit import audit
from shared_cpu_pool import UnresolvedOwnership,unique_object
from shared_process_owner import retain_after_record

PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'


def sources():
    return [ROOT/'tests'/name for name in (
        'private_maker_execute.py','private_maker_plan.py','private_maker_audit.py',
        'private_maker_slice.py','private_maker_shape.py','private_camera_receiving/close.py',
        'sdk_host_matrix/shared_binding.py','shared_io_pool.py','shared_cpu_pool.py',
        'shared_process_owner.py')]


def document(path,digest=None):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid()
                or before.st_nlink!=1 or not 0<before.st_size<=65536):
            raise ValueError('bounded owned slice metadata required')
        raw=bytearray()
        while len(raw)<before.st_size:
            chunk=os.read(fd,min(8192,before.st_size-len(raw)))
            if not chunk:raise ValueError('short slice metadata read')
            raw.extend(chunk)
        if (os.read(fd,1) or stamp(before)!=stamp(os.fstat(fd))
                or stamp(before)!=stamp(os.lstat(path))):
            raise ValueError('slice metadata changed')
        if digest is not None and hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('slice metadata digest differs')
        return json.loads(raw,object_pairs_hook=unique_object)
    finally:close_descriptors([fd])


def checked_plan(path,digest):return check(document(path,digest))


def save(path,value):
    raw=(json.dumps(value,indent=2)+'\n').encode()
    # A sanitized 256-entry table exceeds the smaller plan/START read ceiling.
    if len(raw)>262144:raise ValueError('slice result exceeds metadata ceiling')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        remaining=memoryview(raw)
        while remaining:
            count=os.write(fd,remaining)
            if count<=0:raise OSError('short result write')
            remaining=remaining[count:]
        os.fsync(fd)
    finally:close_descriptors([fd])


def worker(args,plan):
    if sys.executable!=PYTHON or args.workspace!=plan['workspace']:
        raise ValueError('qualified worker interpreter/namespace differs')
    sys.path.insert(0,str(ROOT/'tests/sdk_host_matrix'))
    from shared_binding import verify
    workspace=Path(args.workspace);until=time.monotonic()+3
    while True:
        try:start=document(workspace/'SHARED-START.json');break
        except FileNotFoundError:
            if time.monotonic()>=until:raise ValueError('actual shared owner START absent')
            time.sleep(.005)
    command=worker_argv(plan,interpreter=sys.executable,plan_path=args.plan,plan_sha256=args.plan_sha256)
    binding=verify(start,command,parent_pid=os.getppid(),worker_pid=os.getpid(),target=TARGET)
    result=dict(schema='unison-private-maker-worker/1',complete=False,diagnostic=None,
        failure=None,parent_pid=os.getppid(),worker_pid=os.getpid(),
        canonical_metadata_bound=binding['canonical_metadata_bound'],external_children_started=0)
    try:
        result['diagnostic']=read_source(plan['source'],plan['geometry'],
                                         deadline=time.monotonic()+plan['worker_seconds'])
        audit(result['diagnostic'],plan['geometry'])
        result['complete']=True
    except UnresolvedOwnership:raise
    except Exception as error:result['failure']=repr(error)
    save(workspace/'RESULT.json',result)
    return 0 if result['complete'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',required=True,action='store_true')
    parser.add_argument('--plan',required=True)
    parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--workspace',required=True)
    args=parser.parse_args()
    try:return worker(args,checked_plan(args.plan,args.plan_sha256))
    except UnresolvedOwnership as error:
        retain_after_record(lambda:save(Path(args.workspace)/'SLICE-OWNERSHIP-RETAINED.json',
            dict(error=repr(error),worker_pid=os.getpid(),retained_fds=list(error.retained_fds),
                 uncertain_closes=list(getattr(error,'uncertain_closes',())))))


if __name__=='__main__':raise SystemExit(main())
