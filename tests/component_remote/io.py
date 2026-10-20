"""Bounded owner files; every uncertain close retains its pre-close identity."""
import hashlib
import json
import os
from pathlib import Path
import stat
from shared_cpu_pool import close_descriptors, unique_object, require

MAX_JSON=128*1024*1024
FIELDS=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid')
def identity(path):
    value=os.lstat(path)
    require(stat.S_ISREG(value.st_mode) and value.st_uid==os.getuid(), 'owned regular input required')
    return {key:getattr(value,key) for key in FIELDS}

def read(path,limit=MAX_JSON):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and 0<=before.st_size<=limit,
                'bounded owned regular file required')
        data=bytearray()
        while len(data)<before.st_size:
            chunk=os.read(fd,min(1048576,before.st_size-len(data)))
            require(bool(chunk),'short owner-file read');data.extend(chunk)
        after=os.fstat(fd)
        require(all(getattr(before,k)==getattr(after,k) for k in FIELDS),'owner file changed during read')
        return bytes(data)
    finally:close_descriptors([fd])

def sha(path):return hashlib.sha256(read(path)).hexdigest()
def load(path):return json.loads(read(path),object_pairs_hook=unique_object)
def write(path,data):
    require(type(data) is bytes and len(data)<=MAX_JSON,'bounded owner write required')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        view=memoryview(data)
        while view:
            count=os.write(fd,view);require(count>0,'short owner-file write');view=view[count:]
        os.fsync(fd)
    finally:close_descriptors([fd])
def save(path,value):write(path,(json.dumps(value,indent=2)+'\n').encode())
