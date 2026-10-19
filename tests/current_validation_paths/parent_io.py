"""Parent-owned read-only adapters for `parent.replay`; no writes or release.

The workspace directory FD is opened once with NOFOLLOW and identity-checked;
every later read descends by openat from it. Each read checks regular type,
owner, single link and an unchanged epoch inside private 0700 directories. Unknown close propagates the
qualified carrier and retains the workspace FD; there is no retry.
"""
import os,re,stat
from shared_cpu_pool import UnresolvedOwnership
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.metadata import document
from sdk_merge_receiving.store import stamp

COUNTERS={'client':'client-validator.calls.jsonl','server':'server-validator.calls.jsonl',
    'copy':'external-copy.calls.jsonl','merge':'merge.calls.jsonl'}
NAME=re.compile('[A-Za-z0-9][A-Za-z0-9._-]{0,95}')
CALL=re.compile(r'(call-[0-9]{3})(?:-|\.)')
MAXIMUM=2*1048576


def require(value,message):
    if not value:raise ValueError(message)


def private_directory(value,identity=None):
    require(stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode)==0o700 and value.st_uid==os.getuid()
        and (identity is None or (value.st_dev,value.st_ino)==identity),'private named directory changed')


class Reader:
    def __init__(self,workspace,identity,roots):
        require(type(identity) is dict and set(identity)=={'device','inode'}
            and all(type(v) is int and v>0 for v in identity.values()),'exact workspace identity required')
        require(type(roots) is dict and roots and all(type(k) is str and type(v) is str and NAME.fullmatch(v)
            for k,v in roots.items()) and len(set(roots.values()))==len(roots),'exact declared case names required')
        self.workspace=workspace;self.identity=(identity['device'],identity['inode']);self.roots=dict(roots);self.closed=False
        self.fd=os.open(workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:self.fence()
        except BaseException:
            self.closed=True;close_descriptors([self.fd]);raise
    def fence(self):
        require(not self.closed,'parent reader closed')
        private_directory(os.fstat(self.fd),self.identity);private_directory(os.lstat(self.workspace),self.identity)
    def _directory(self,parent,name,fds):
        require(NAME.fullmatch(name) is not None,'bounded single basename required')
        fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
        native=os.fstat(fd);private_directory(native)
        require(stamp(os.stat(name,dir_fd=parent,follow_symlinks=False))[:2]==stamp(native)[:2],'named directory replaced')
        return fd
    def _read(self,parent,name,*,absent=False):
        require(NAME.fullmatch(name) is not None,'bounded single basename required')
        try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        except FileNotFoundError:
            if absent:return None
            raise
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
                and before.st_size<=MAXIMUM,'bounded owned single-link record required')
            raw=bytearray()
            while len(raw)<before.st_size:
                block=os.read(fd,min(65536,before.st_size-len(raw)));require(bool(block),'short record read')
                raw.extend(block)
            require(not os.read(fd,1) and stamp(before)==stamp(os.fstat(fd))==stamp(os.stat(name,dir_fd=parent,follow_symlinks=False)),
                'record epoch changed during parent read')
            return bytes(raw)
        finally:close_descriptors([fd])
    def _case(self,root,action):
        require(root in self.roots,'undeclared case root')
        self.fence();fds=[]
        try:
            fd=self._directory(self.fd,self.roots[root],fds)
            return action(fd)
        finally:
            try:close_descriptors(fds)
            except UnresolvedOwnership as error:self.retain(error);raise
    def retain(self,error):
        if not self.closed and self.fd not in getattr(error,'uncertain_fds',()):
            error.retained_fds=tuple(dict.fromkeys((*error.retained_fds,self.fd)))
        error.parent_reader=self
    def read_case(self,root,name):
        raw=self._case(root,lambda fd:self._read(fd,name))
        require(len(raw)>0,'empty named record');return raw
    def read_root(self,name):
        self.fence();raw=self._read(self.fd,name);require(len(raw)>0,'empty root record')
        return document(raw)
    def case_state(self,root,scripts,profile,proxies):
        require(type(proxies) is dict and all(re.fullmatch(r'call-[0-9]{3}-proxy\.py',n) for n in proxies),'exact proxy script names required')
        def action(fd):
            native=os.fstat(fd)
            names=os.listdir(fd);stems={name[:8] for name in names if CALL.match(name)}
            require(stems<={name[:8] for name in proxies},'case directory holds calls absent from worker inventory')
            current=all(self._read(fd,name)==text.encode() for name,text in {**scripts,**proxies}.items())
            state=[]
            state_fd=self._directory(fd,'server-state',state)
            try:profile_current=self._read(state_fd,'endpoint.prf')==profile.encode()
            finally:close_descriptors(state)
            counters={}
            for key,name in COUNTERS.items():
                raw=self._read(fd,name,absent=True)
                if raw is None or raw==b'':counters[key]=[];continue
                require(raw.endswith(b'\n'),'complete counter lines required')
                counters[key]=[document(line) for line in raw[:-1].split(b'\n')]
                require(all(type(value) is dict for value in counters[key]),'counter objects required')
            return dict(identity=dict(device=native.st_dev,inode=native.st_ino),counters=counters,
                scripts_current=current,profile_current=profile_current)
        return self._case(root,action)
    def close(self):
        require(not self.closed,'parent reader already closed')
        self.closed=True
        try:close_descriptors([self.fd])
        except UnresolvedOwnership as error:error.parent_reader=self;raise
