"""Existing private metadata namespace; pinned directory FD, one-use records.

No automatic cleanup/context manager. Unknown close retains its pre-close
identity and all other known descriptors, including the directory owner. This
store never proves process settlement or authorizes CPU/IO release.
"""
import hashlib
import json
import os
import re
import stat
from shared_cpu_pool import UnresolvedOwnership
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.evidence import unique
from sdk_merge_receiving.plan import require, path

FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')
MAXIMUM=2*1048576


def stamp(value):return tuple(getattr(value,k) for k in FIELDS)


class Store:
    def __init__(self,root,identity):
        path(root)
        require(type(identity) is dict and set(identity)=={'device','inode'}
            and all(type(v) is int and v>0 for v in identity.values()),'exact directory identity required')
        self.root=root;self.identity=dict(identity);self.closed=False
        self.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:self.fence()
        except BaseException:
            self.closed=True
            close_descriptors([self.fd])
            raise

    def fence(self):
        require(not self.closed,'metadata directory owner closed')
        native=os.fstat(self.fd);visible=os.lstat(self.root)
        for value in (native,visible):
            require(stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode)==0o700
                and value.st_uid==os.getuid() and value.st_dev==self.identity['device']
                and value.st_ino==self.identity['inode'],'private metadata directory changed')

    def name(self,name):
        require(type(name) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,95}',name) is not None,
                'bounded single record basename required')
        self.fence()

    def retain(self,error):
        if self.fd not in getattr(error,'uncertain_fds',()) and not self.closed:
            error.retained_fds=tuple(dict.fromkeys((*error.retained_fds,self.fd)))
        error.metadata_store=self

    def write(self,name,value):
        self.name(name)
        data=(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode()
        require(0<len(data)<=MAXIMUM,'bounded metadata record required')
        try:
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                       0o600,dir_fd=self.fd)
            try:
                initial=os.fstat(fd)
                require(stat.S_ISREG(initial.st_mode) and stat.S_IMODE(initial.st_mode)==0o600
                    and initial.st_uid==os.getuid() and initial.st_nlink==1,
                    'new private single-link metadata file required')
                offset=0
                while offset<len(data):
                    count=os.write(fd,data[offset:]);require(count>0,'metadata write stalled')
                    offset+=count
                os.fsync(fd)
                published=os.fstat(fd)
                require(published.st_size==len(data) and published.st_nlink==1
                    and published.st_mode==initial.st_mode and published.st_uid==initial.st_uid
                    and stamp(published)==stamp(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),
                    'metadata name replaced during publication')
            finally:close_descriptors([fd])
            require(stamp(published)==stamp(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),
                    'metadata publication changed after file close')
            os.fsync(self.fd);self.fence()
        except UnresolvedOwnership as error:
            self.retain(error);raise
        return dict(name=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))

    def read(self,name,*,expected_sha256=None,maximum=MAXIMUM):
        self.name(name)
        require(type(maximum) is int and 0<maximum<=MAXIMUM,'bounded metadata read required')
        if expected_sha256 is not None:
            require(type(expected_sha256) is str and re.fullmatch('[0-9a-f]{64}',expected_sha256),
                    'exact optional record SHA required')
        try:
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=self.fd)
            try:
                before=os.fstat(fd)
                require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode)==0o600
                    and before.st_uid==os.getuid() and before.st_nlink==1
                    and 0<before.st_size<=maximum,'bounded single-link private metadata required')
                raw=bytearray()
                while len(raw)<before.st_size:
                    block=os.read(fd,min(65536,before.st_size-len(raw)))
                    require(bool(block),'short metadata record');raw.extend(block)
                require(not os.read(fd,1) and stamp(before)==stamp(os.fstat(fd))
                    ==stamp(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),
                    'metadata epoch changed during read')
            finally:close_descriptors([fd])
            self.fence()
        except UnresolvedOwnership as error:
            self.retain(error);raise
        data=bytes(raw)
        require(expected_sha256 is None or hashlib.sha256(data).hexdigest()==expected_sha256,
                'metadata record SHA differs')
        return data

    def read_json(self,name,*,expected_sha256):
        return json.loads(self.read(name,expected_sha256=expected_sha256),object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata JSON')))

    def close(self):
        require(not self.closed,'directory close already attempted; no retry')
        self.closed=True
        try:close_descriptors([self.fd])
        except UnresolvedOwnership as error:
            self.retain(error);raise
