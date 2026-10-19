"""Admitted generated-state clone installation and closed-output verification.

No lock/admission/SDK or source-copy fallback. Call only under retained IO/CPU.
The existing fclonefileat harness primitive is reused; source epochs never change.
"""
import hashlib
from copy import deepcopy
import os
from pathlib import Path
import stat
from private_camera_receiving.close import close_descriptors
from sdk_multifile.clone import native_clone
from sdk_merge_receiving.inputs import FIELDS
from sdk_merge_receiving.plan import CODECS,STAGES,require,digest


def stamp(value):return {key:getattr(value,key) for key in FIELDS}


def directory(fd,path,identity):
    for value in (os.fstat(fd),os.lstat(path)):
        require(stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode)==0o700
            and value.st_uid==os.getuid() and (value.st_dev,value.st_ino)==identity,
            'private endpoint directory identity changed')


def hash_fd(fd,count):
    require(type(count) is int and 0<count<=128*1048576,'bounded generated state required')
    sha=hashlib.sha256();at=0
    while at<count:
        block=os.pread(fd,min(1048576,count-at),at);require(bool(block),'short disposable clone')
        at+=len(block);sha.update(block)
    require(not os.pread(fd,1,count),'disposable clone grew')
    return sha.hexdigest()


def inspect(endpoint,identity,expected):
    """Hash only an owned receiving image, never a retained source."""
    fds=[]
    try:
        parent=os.open(endpoint,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent)
        directory(parent,endpoint,identity)
        fd=os.open('image.dng',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode)==0o600
            and before.st_uid==os.getuid() and before.st_nlink==1
            and before.st_size==expected['bytes'],'private receiving image identity/size differs')
        actual=hash_fd(fd,before.st_size)
        require(actual==expected['sha256'] and stamp(before)==stamp(os.fstat(fd))
            ==stamp(os.stat('image.dng',dir_fd=parent,follow_symlinks=False)),
            'receiving output bytes or epochs differ')
        require(set(os.listdir(parent))=={'image.dng'},'unexpected receiving staging/entries remain')
        directory(parent,endpoint,identity)
        return dict(sha256=actual,bytes=before.st_size,identity=stamp(before))
    finally:close_descriptors(fds)


def install(reference,epoch,endpoint,identity,stage,previous,*,clone=native_clone):
    require(stage in ('seed','update'),'only seed/update may install clones')
    require(set(reference)=={'path','sha256','bytes'} and set(epoch)==set(FIELDS),
            'exact retained source reference and epoch required')
    digest(reference['sha256'])
    fds=[];temporary='INSTALL-'+stage+'.dng'
    try:
        src=os.open(reference['path'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);fds.append(src)
        def fence_source():
            require(stamp(os.fstat(src))==epoch and stamp(os.lstat(reference['path']))==epoch,
                    'retained generated source epoch changed')
        fence_source();native=os.fstat(src)
        require(stat.S_ISREG(native.st_mode) and stat.S_IMODE(native.st_mode)==0o400
            and native.st_uid==os.getuid() and native.st_nlink==1
            and native.st_size==reference['bytes'] and 0<native.st_size<=128*1048576,
            'readonly single-link bounded retained state required')
        parent=os.open(endpoint,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent)
        directory(parent,endpoint,identity)
        def fence_previous():
            try:observed=stamp(os.stat('image.dng',dir_fd=parent,follow_symlinks=False))
            except FileNotFoundError:observed=None
            require(observed==previous,'receiving image replaced since last accepted phase')
        fence_previous()
        try:os.stat(temporary,dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:pass
        else:raise ValueError('clone installation namespace consumed; no overwrite/retry')
        clone(src,parent,temporary);fence_source()
        target=os.open(temporary,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(target)
        copied=os.fstat(target)
        require(stat.S_ISREG(copied.st_mode) and copied.st_uid==os.getuid() and copied.st_nlink==1
            and copied.st_size==native.st_size and (copied.st_dev,copied.st_ino)!=(native.st_dev,native.st_ino),
            'distinct owned disposable clone required before chmod')
        os.fchmod(target,0o600)
        hash_epoch=stamp(os.fstat(target))
        actual=hash_fd(target,copied.st_size)
        require(actual==reference['sha256'] and hash_epoch==stamp(os.fstat(target))
            ==stamp(os.stat(temporary,dir_fd=parent,follow_symlinks=False)),
            'disposable clone hash/epoch differs; no fallback')
        os.fsync(target);fence_previous();fence_source();directory(parent,endpoint,identity)
        os.replace(temporary,'image.dng',src_dir_fd=parent,dst_dir_fd=parent);os.fsync(parent)
        published=stamp(os.fstat(target))
        require(all(published[k]==hash_epoch[k] for k in FIELDS if k!='st_ctime_ns')
            and published==stamp(os.stat('image.dng',dir_fd=parent,follow_symlinks=False)),
                'installed clone name binding differs')
        fence_source();directory(parent,endpoint,identity)
        return dict(source=reference['path'],source_identity=dict(epoch),clone_identity=published,
            clone_sha256=actual,clone_hash_bytes=copied.st_size,
            source_payload_hash_bytes=0 if clone is native_clone else None,
            backend='native-fclonefileat-only' if clone is native_clone else 'original-test-double')
    finally:close_descriptors(fds)


class Cases:
    def __init__(self,packet,*,clone=native_clone):
        self.packet=deepcopy(packet);self.clone=clone;self.index=0;self.active=None;self.expected=None
        self.endpoints={};self.accepted={};self.noop_before={};self.history=[]

    def fence_sources(self):
        for name,epoch in self.packet['source_observations'].items():
            require(stamp(os.lstat(name))==epoch,'generated input batch epoch changed')

    def prepare(self,row):
        require(self.active is None and self.index<9
            and (row['codec'],row['stage'])==(CODECS[self.index//3],STAGES[self.index%3]),
            'exact one-use scalar phase order required')
        self.active=(row['codec'],row['stage']);self.fence_sources()
        codec,stage=self.active
        root=Path(self.packet['workspace'])/codec
        require(row['directory']==str(root),'exact private codec directory required')
        case=next(c for c in self.packet['cases'] if c['codec']==codec)
        candidate=dict((k,v) for k,v in case['states']['base' if stage=='seed' else 'target'].items()
                       if k in ('sha256','bytes'))
        if stage=='seed':
            root.mkdir(mode=0o700)
            for side in ('left','right'):
                endpoint=root/side;endpoint.mkdir(mode=0o700);s=endpoint.stat()
                self.endpoints[codec,side]=(endpoint,(s.st_dev,s.st_ino))
        clones=[]
        for side in ('left','right'):
            endpoint,identity=self.endpoints[codec,side]
            if stage=='seed' and side=='right':continue
            if stage=='noop':
                self.noop_before[codec,side]=inspect(endpoint,identity,candidate)
                require(self.noop_before[codec,side]==self.accepted[codec,side],
                        'receiving image changed before noop')
            else:
                ref=case['states']['base' if stage=='seed' else side]
                previous=None if stage=='seed' else self.accepted[codec,side]['identity']
                clones.append(install(ref,self.packet['source_observations'][ref['path']],
                    endpoint,identity,stage,previous,clone=self.clone))
        self.fence_sources()
        self.history.append(dict(codec=codec,stage=stage,event='PREPARED',candidate=deepcopy(candidate),clones=clones))
        self.expected=deepcopy(candidate)
        return candidate

    def verify(self,row,candidate):
        require(self.active==(row['codec'],row['stage']),'only current phase may verify')
        require(type(candidate) is dict and set(candidate)=={'sha256','bytes'}
            and type(candidate['bytes']) is int and candidate==self.expected,
            'exact manifest-bound output candidate required')
        self.fence_sources();outputs={}
        for side in ('left','right'):
            endpoint,identity=self.endpoints[row['codec'],side]
            value=inspect(endpoint,identity,candidate)
            if row['stage']=='noop':require(value==self.noop_before[row['codec'],side],
                                           'noop changed receiving bytes or eight-field identity')
            outputs[side]=value;self.accepted[row['codec'],side]=value
        self.fence_sources()
        self.history.append(dict(codec=row['codec'],stage=row['stage'],event='VERIFIED',outputs=outputs))
        self.active=None;self.expected=None;self.index+=1
