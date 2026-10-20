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
            def owned_names(self):return owner.names(self)
            def resource_fork(self,data=None):return owner.resource_fork(self,data)
            def xattr(self,key,data=None,*,remove=False):return owner.xattr(self,key,data,remove)
            def xattr_names(self):return owner.xattr_names(self)
            def acl(self,text=None):return owner.acl(self,text)
            def punch_hole(self,offset,length):return owner.punch_hole(self,offset,length)
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
    def names(self,path):
        def action(parent,name,fds):
            if name is None:return sorted(os.listdir(parent))
            fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
            st=os.fstat(fd)
            if not(stat.S_ISDIR(st.st_mode) and st.st_uid==os.getuid()):raise ValueError('owned fixture directory required')
            return sorted(os.listdir(fd))
        return self._operation(path,action)
    def resource_fork(self,path,data=None):
        # Darwin named fork through the held single-link descriptor, never a
        # "..namedfork" pathname that bypasses component traversal checks.
        import ctypes,sys
        if sys.platform!='darwin':raise ValueError('resource forks are a Darwin fixture only')
        if data is not None and (type(data) is not bytes or not 0<len(data)<=65536):raise ValueError('bounded resource fork bytes required')
        libc=ctypes.CDLL(None,use_errno=True);key=b'com.apple.ResourceFork'
        libc.fsetxattr.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
        libc.fgetxattr.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
        libc.fgetxattr.restype=ctypes.c_ssize_t
        def action(parent,name,fds):
            fd,_=self._file(parent,name,os.O_RDONLY if data is None else os.O_WRONLY,fds)
            if data is not None:
                if libc.fsetxattr(fd,key,data,len(data),0,0)!=0:raise OSError(ctypes.get_errno(),'fsetxattr resource fork')
                return len(data)
            buffer=ctypes.create_string_buffer(65536);n=libc.fgetxattr(fd,key,buffer,65536,0,0)
            if n<0:raise OSError(ctypes.get_errno(),'fgetxattr resource fork')
            return buffer.raw[:n]
        return self._operation(path,action)
    # Darwin descriptor-anchored properties for filesystem transition fixtures.
    XATTR='org.unison.fsprop.tag'
    def _libc(self):
        import ctypes,sys
        if sys.platform!='darwin':raise ValueError('xattr/ACL/hole fixtures are Darwin only')
        libc=ctypes.CDLL(None,use_errno=True)
        libc.fsetxattr.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
        libc.fgetxattr.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
        libc.fremovexattr.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int]
        libc.flistxattr.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
        libc.fgetxattr.restype=libc.flistxattr.restype=ctypes.c_ssize_t
        libc.acl_get_fd_np.argtypes=[ctypes.c_int,ctypes.c_int];libc.acl_get_fd_np.restype=ctypes.c_void_p
        libc.acl_set_fd_np.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
        libc.acl_from_text.argtypes=[ctypes.c_char_p];libc.acl_from_text.restype=ctypes.c_void_p
        libc.acl_init.argtypes=[ctypes.c_int];libc.acl_init.restype=ctypes.c_void_p
        libc.acl_to_text.argtypes=[ctypes.c_void_p,ctypes.c_void_p];libc.acl_to_text.restype=ctypes.c_void_p
        libc.acl_free.argtypes=[ctypes.c_void_p]
        libc.fcntl.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_void_p]
        return ctypes,libc
    def xattr(self,path,key,data=None,remove=False):
        if key!=self.XATTR:raise ValueError('declared fixture xattr key only')
        if data is not None and (remove or type(data) is not bytes or not 0<len(data)<=4096):raise ValueError('bounded xattr bytes or removal required')
        ctypes,libc=self._libc();name=key.encode()
        def action(parent,name_,fds):
            fd,_=self._file(parent,name_,os.O_RDONLY if data is None and not remove else os.O_WRONLY,fds)
            if remove:
                if libc.fremovexattr(fd,name,0)!=0:raise OSError(ctypes.get_errno(),'fremovexattr fixture')
                return None
            if data is not None:
                if libc.fsetxattr(fd,name,data,len(data),0,0)!=0:raise OSError(ctypes.get_errno(),'fsetxattr fixture')
                return len(data)
            buffer=ctypes.create_string_buffer(4096);n=libc.fgetxattr(fd,name,buffer,4096,0,0)
            if n<0:raise OSError(ctypes.get_errno(),'fgetxattr fixture')
            return buffer.raw[:n]
        return self._operation(path,action)
    def xattr_names(self,path):
        ctypes,libc=self._libc()
        def action(parent,name,fds):
            fd,_=self._file(parent,name,os.O_RDONLY,fds);buffer=ctypes.create_string_buffer(65536)
            n=libc.flistxattr(fd,buffer,65536,0)
            if n<0:raise OSError(ctypes.get_errno(),'flistxattr fixture')
            return sorted(k.decode() for k in buffer.raw[:n].split(b'\0') if k)
        return self._operation(path,action)
    def acl(self,path,text=None):
        # Extended ACL text; '' clears every entry. Returns the current text or None.
        if text is not None and (type(text) is not str or len(text)>4096):raise ValueError('bounded ACL text required')
        ctypes,libc=self._libc();EXTENDED=0x100
        def action(parent,name,fds):
            fd,_=self._file(parent,name,os.O_RDONLY,fds)
            if text is not None:
                value=libc.acl_from_text(text.encode()) if text else libc.acl_init(0)
                if not value:raise OSError(ctypes.get_errno(),'acl_from_text fixture')
                try:
                    if libc.acl_set_fd_np(fd,value,EXTENDED)!=0:raise OSError(ctypes.get_errno(),'acl_set_fd_np fixture')
                finally:libc.acl_free(value)
            value=libc.acl_get_fd_np(fd,EXTENDED)
            if not value:return None
            try:
                rendered=libc.acl_to_text(value,None)
                if not rendered:raise OSError(ctypes.get_errno(),'acl_to_text fixture')
                try:return ctypes.string_at(rendered).decode()
                finally:libc.acl_free(rendered)
            finally:libc.acl_free(value)
        return self._operation(path,action)
    def punch_hole(self,path,offset,length):
        if not all(type(v) is int and v>0 and v%4096==0 for v in (offset,length)):raise ValueError('aligned positive hole required')
        ctypes,libc=self._libc()
        class Hole(ctypes.Structure):_fields_=[('flags',ctypes.c_uint32),('reserved',ctypes.c_uint32),('offset',ctypes.c_int64),('length',ctypes.c_int64)]
        F_PUNCHHOLE=99
        def action(parent,name,fds):
            fd,before=self._file(parent,name,os.O_RDWR,fds)
            if offset+length>=before.st_size:raise ValueError('hole must stay inside the fixture data')
            hole=Hole(0,0,offset,length)
            if libc.fcntl(fd,F_PUNCHHOLE,ctypes.byref(hole))!=0:raise OSError(ctypes.get_errno(),'F_PUNCHHOLE fixture')
            os.fsync(fd)
            if os.fstat(fd).st_size!=before.st_size:raise ValueError('hole changed fixture length')
            return length
        return self._operation(path,action)
    def close(self):
        self._ready();self.close_attempted=True
        try:self._closer([self.fd])
        except UnresolvedOwnership as error:self._retain(error);raise
        self.closed=True
