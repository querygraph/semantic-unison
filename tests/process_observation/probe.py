"""Pinned metadata probe with independently retained/reaped probe children."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from private_camera_receiving.close import close_descriptors
from shared_child import invoke


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate probe field')
        result[key]=value
    return result


class Probe:
    def __init__(self,path,sha256,*,pass_fds=(),limit=128):
        self.path=Path(path)
        if not self.path.is_absolute() or len(sha256)!=64 or any(c not in '0123456789abcdef' for c in sha256):
            raise ValueError('absolute pinned probe required')
        if type(limit) is not int or not 1<=limit<=1024:raise ValueError('bounded probe calls required')
        self.sha256=sha256;self.pass_fds=tuple(pass_fds);self.limit=limit;self.outcomes=[]
        self.identity=self.verify()

    def verify(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid() or before.st_nlink!=1 or not 0<before.st_size<=2**20:
                raise ValueError('probe file identity refused')
            identity=(before.st_dev,before.st_ino,before.st_mode,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
            digest=hashlib.sha256();remaining=before.st_size
            while remaining:
                block=os.read(fd,min(65536,remaining))
                if not block:raise ValueError('short probe read')
                digest.update(block);remaining-=len(block)
            after=os.fstat(fd)
            if identity!=(after.st_dev,after.st_ino,after.st_mode,after.st_size,after.st_mtime_ns,after.st_ctime_ns) or digest.hexdigest()!=self.sha256:
                raise ValueError('probe artifact changed')
            return identity
        finally:close_descriptors([fd])

    def __call__(self,pid):
        if type(pid) is not int or not 0<pid<2**31 or len(self.outcomes)>=self.limit:
            raise ValueError('bounded positive observed PID required')
        if self.verify()!=self.identity:raise ValueError('probe replaced before call')
        outcome=invoke([str(self.path),str(pid)],dict(os.environ),time.monotonic()+2,
                       pass_fds=self.pass_fds,capture_limit=4096)
        # Preserve actual child settlement even if subsequent parsing/pin checks fail.
        self.outcomes.append(outcome)
        if self.verify()!=self.identity:raise ValueError('probe replaced after call')
        if outcome['returncode']!=0 or outcome['capture_truncated'] or outcome['stderr']:
            raise ValueError('probe did not return a bounded normal frame')
        value=json.loads(outcome['stdout'],object_pairs_hook=unique)
        if type(value) is not dict or type(value.get('pid')) is not int or value['pid']!=pid or type(value.get('available')) is not bool:
            raise ValueError('probe frame does not bind observed PID')
        return value
