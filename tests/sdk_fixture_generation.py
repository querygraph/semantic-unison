"""Owned original generated-state installation, separate from SDK execution.

Call only inside an admitted IO/CPU owner. No retained source mutation, copy
fallback, cleanup retry, or process/resource-release authority.
"""
import hashlib,os,re,stat
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.data import hash_fd,stamp
from sdk_fixture_states import MAX_BYTES,COMPRESSION,VALUES


def write_state(parent,directory,identity,codec,state,data):
    if (codec not in COMPRESSION or state not in VALUES or type(data) is not bytes
            or not 0<len(data)<=MAX_BYTES):raise ValueError('exact bounded generated state required')
    name=codec+'-'+state+'.dng';fd=None
    def fence():
        for s in (os.fstat(parent),os.lstat(directory)):
            if not(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700 and s.st_uid==os.getuid()
                    and (s.st_dev,s.st_ino)==identity):raise ValueError('owned generated directory changed')
    fence()
    try:
        fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=parent)
        before=os.fstat(fd)
        if not(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode)==0o600
                and before.st_uid==os.getuid() and before.st_nlink==1):raise ValueError('new owned single-link generated file required')
        at=0
        while at<len(data):
            block=data[at:at+1048576];n=os.write(fd,block)
            if type(n) is not int or not 0<n<=len(block):raise ValueError('generated write stalled or malformed')
            at+=n
        os.fsync(fd);os.fchmod(fd,0o400);epoch=stamp(os.fstat(fd));digest=hash_fd(fd,len(data))
        if (digest!=hashlib.sha256(data).hexdigest() or epoch['st_size']!=len(data)
                or epoch['st_mode']!=0o100400 or epoch['st_nlink']!=1
                or epoch!=stamp(os.fstat(fd)) or epoch!=stamp(os.stat(name,dir_fd=parent,follow_symlinks=False))):
            raise ValueError('generated state readback or name binding differs')
    finally:
        if fd is not None:close_descriptors([fd])
    os.fsync(parent);fence()
    return dict(path=str(directory)+'/'+name,bytes=len(data),sha256=digest,identity=epoch)
