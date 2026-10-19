"""Anchored IO for original disposable named-path fixtures, not source photos.

One retained root descriptor; directory traversal refuses symlinks. All acquired
FDs close through the qualified uncertainty carrier. Once uncertain, the whole
file owner refuses new IO/close attempts until independently recovered.
"""
import os,stat
from pathlib import Path,PosixPath
from shared_cpu_pool import UnresolvedOwnership
from private_camera_receiving.close import close_descriptors

MAX_BYTES=16*1048576
FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')
def epoch(st):return tuple(getattr(st,k) for k in FIELDS)


class Files:
    def __init__(self,root,identity,*,closer=close_descriptors):
        self.root=Path(root);self.identity=tuple(identity);self.fd=None;self.closed=False
        self.close_attempted=False;self.retained=None;self._closer=closer
        if not self.root.is_absolute() or '..' in self.root.parts:raise ValueError('absolute owned root required')
        owner=self
        class Owned(PosixPath):
            def read_bytes(self):return owner.read(self)
            def read_text(self,encoding=None,errors=None):
                if encoding not in (None,'utf-8') or errors not in (None,'strict'):raise ValueError('exact UTF8 fixture text required')
                return self.read_bytes().decode('utf-8')
            def write_bytes(self,data):return owner.write(self,data)
            def write_text(self,data,encoding=None,errors=None,newline=None):
                if type(data) is not str or encoding not in (None,'utf-8') or errors not in (None,'strict') or newline is not None:
                    raise ValueError('exact UTF8 fixture text required')
                owner.write(self,data.encode('utf-8'));return len(data)
            def open(self,*args,**kwargs):raise ValueError('bare file contexts are not an owned fixture interface')
            def mkdir(self,mode=0o777,parents=False,exist_ok=False):return owner.mkdir(self,parents,exist_ok)
            def stat(self,*,follow_symlinks=True):return owner.observe(self)
            def lstat(self):return owner.observe(self)
            def exists(self,*,follow_symlinks=True):
                try:owner.observe(self);return True
                except FileNotFoundError:return False
            def is_file(self,*,follow_symlinks=True):
                try:return stat.S_ISREG(owner.observe(self).st_mode)
                except FileNotFoundError:return False
            def is_dir(self):
                try:return stat.S_ISDIR(owner.observe(self).st_mode)
                except FileNotFoundError:return False
            def chmod(self,mode,*,follow_symlinks=True):return owner.chmod(self,mode)
            def unlink(self,missing_ok=False):return owner.unlink(self,missing_ok)
            def _unsupported(self,*args,**kwargs):raise ValueError('undeclared fixture mutation refused')
            rename=replace=symlink_to=hardlink_to=touch=rmdir=_unsupported
        self.Path=Owned
        self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:self._fence()
        except BaseException:
            self.close();raise

    def _ready(self):
        if self.retained is not None:raise self.retained
        if self.closed or self.close_attempted:raise ValueError('file owner already retired')
    def _fence(self):
        for st in (os.fstat(self.fd),os.lstat(self.root)):
            if not(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700 and st.st_uid==os.getuid()
                and (st.st_dev,st.st_ino)==self.identity):raise ValueError('owned root identity changed')
    def _parts(self,path):
        p=Path(path)
        if not p.is_absolute() or '..' in p.parts:raise ValueError('absolute private fixture path required')
        try:return p.relative_to(self.root).parts
        except ValueError:raise ValueError('fixture path escaped owned root')
    def _retain(self,error):
        self.retained=error;error.named_fixture_files=self
        excluded=set(getattr(error,'uncertain_fds',()))
        if not self.closed and self.fd is not None and self.fd not in excluded:
            error.retained_fds=tuple(dict.fromkeys((*error.retained_fds,self.fd)))
    def _operation(self,path,action,*,create_parents=False):
        self._ready();self._fence();parts=self._parts(path);fds=[];parent=self.fd
        try:
            try:
                for part in parts[:-1]:
                    try:child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
                    except FileNotFoundError:
                        if not create_parents:raise
                        os.mkdir(part,0o700,dir_fd=parent)
                        child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
                    fds.append(child);st=os.fstat(child)
                    if not(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700 and st.st_uid==os.getuid()):
                        raise ValueError('private directory component differs')
                    parent=child
                value=action(parent,parts[-1] if parts else None,fds);self._fence();return value
            finally:self._closer(fds)
        except UnresolvedOwnership as error:self._retain(error);raise
    def _file(self,parent,name,flags,fds):
        if name is None:raise ValueError('root is not a fixture file')
        fd=os.open(name,flags|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,0o600,dir_fd=parent);fds.append(fd)
        st=os.fstat(fd)
        if not(stat.S_ISREG(st.st_mode) and st.st_uid==os.getuid() and st.st_nlink==1 and 0<=st.st_size<=MAX_BYTES):
            raise ValueError('bounded owned single-link fixture required')
        if epoch(st)!=epoch(os.stat(name,dir_fd=parent,follow_symlinks=False)):raise ValueError('fixture name binding changed')
        return fd,st
    def read(self,path):
        def action(parent,name,fds):
            fd,before=self._file(parent,name,os.O_RDONLY,fds);chunks=[];at=0
            while at<before.st_size:
                data=os.pread(fd,min(1048576,before.st_size-at),at)
                if not data:raise ValueError('short fixture read')
                chunks.append(data);at+=len(data)
            after=os.fstat(fd);named=os.stat(name,dir_fd=parent,follow_symlinks=False)
            append=name.endswith('.calls.jsonl') or name.endswith('.events')
            if append:
                stable=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid)
                if stable(before)!=stable(after) or stable(after)!=stable(named) or not before.st_size<=after.st_size<=MAX_BYTES or named.st_size<after.st_size:
                    raise ValueError('owned append snapshot changed identity or shrank')
            elif epoch(before)!=epoch(after) or epoch(after)!=epoch(named):raise ValueError('fixture changed during read')
            return b''.join(chunks)
        return self._operation(path,action)
    def write(self,path,data):
        if type(data) is not bytes or len(data)>MAX_BYTES:raise ValueError('bounded immutable fixture bytes required')
        def action(parent,name,fds):
            fd,before=self._file(parent,name,os.O_WRONLY|os.O_CREAT,fds)
            os.ftruncate(fd,0);at=0
            while at<len(data):
                n=os.write(fd,data[at:at+1048576])
                if n<=0:raise ValueError('fixture write stalled')
                at+=n
            os.fsync(fd);after=os.fstat(fd)
            if after.st_size!=len(data) or (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino) or epoch(after)!=epoch(os.stat(name,dir_fd=parent,follow_symlinks=False)):
                raise ValueError('fixture write binding changed')
            return at
        return self._operation(path,action)
    def mkdir(self,path,parents=False,exist_ok=False):
        def action(parent,name,fds):
            if name is None:
                if exist_ok:return
                raise FileExistsError(str(path))
            try:os.mkdir(name,0o700,dir_fd=parent)
            except FileExistsError:
                if not exist_ok:raise
                st=os.stat(name,dir_fd=parent,follow_symlinks=False)
                if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o700:raise ValueError('existing fixture directory differs')
        return self._operation(path,action,create_parents=parents)
    def observe(self,path):
        def action(parent,name,fds):
            st=os.fstat(parent) if name is None else os.stat(name,dir_fd=parent,follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode) or st.st_uid!=os.getuid():raise ValueError('foreign/symlink fixture metadata refused')
            return st
        return self._operation(path,action)
    def chmod(self,path,mode):
        if mode not in (0o400,0o600,0o700):raise ValueError('declared private fixture modes only')
        def action(parent,name,fds):
            fd,_=self._file(parent,name,os.O_RDONLY,fds);os.fchmod(fd,mode)
        return self._operation(path,action)
    def unlink(self,path,missing_ok=False):
        def action(parent,name,fds):
            if name is None:raise ValueError('cannot unlink owned root')
            try:st=os.stat(name,dir_fd=parent,follow_symlinks=False)
            except FileNotFoundError:
                if missing_ok:return
                raise
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1:raise ValueError('only owned single-link fixture files may be unlinked')
            os.unlink(name,dir_fd=parent)
        return self._operation(path,action)
    def close(self):
        self._ready();self.close_attempted=True
        try:self._closer([self.fd])
        except UnresolvedOwnership as error:self._retain(error);raise
        self.closed=True
