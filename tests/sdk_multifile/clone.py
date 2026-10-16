"""Named generated-fixture clones; exact caller IO admission required.

No source payload reads, source chmod, copy fallback, overwrite or cleanup.
The syscall adapter is test-harness preparation, not a new Unison clone engine.
"""
import ctypes
import os
import re
from pathlib import Path
import stat
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from private_camera_receiving.close import close_descriptors
FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')


def stamp(value):return {k:getattr(value,k) for k in FIELDS}


def native_clone(source,parent,name):
    lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    fn=lib.fclonefileat;fn.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32];fn.restype=ctypes.c_int
    if fn(source,parent,os.fsencode(name),0):raise OSError(ctypes.get_errno(),'fclonefileat refused; no copy fallback')


def prepare(source,expected,directory,name,*,clone=native_clone):
    source,directory=Path(source),Path(directory)
    if not source.is_absolute() or not directory.is_absolute() or name not in ('uncompressed.dng','jpeg.dng'):
        raise ValueError('absolute owned paths and fixed generated candidate name required')
    if type(expected) is not dict or set(expected)!=set(FIELDS) or any(type(v) is not int for v in expected.values()):
        raise ValueError('exact native eight-field source metadata required')
    fds=[]
    try:
        src=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);fds.append(src)
        def check():
            if stamp(os.fstat(src))!=expected or stamp(os.lstat(source))!=expected:raise ValueError('generated source epoch changed')
        check();s=os.fstat(src)
        if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) not in (0o400,0o644) or s.st_nlink!=1 or s.st_uid!=os.getuid() or not 0<s.st_size<=128*1048576:
            raise ValueError('retained generated source identity refused')
        parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent);d=os.fstat(parent)
        if d.st_uid!=os.getuid() or stat.S_IMODE(d.st_mode)!=0o700:raise ValueError('owned private receiving directory required')
        try:os.stat(name,dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:pass
        else:raise ValueError('candidate name already consumed; no overwrite')
        clone(src,parent,name);check()
        target=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(target);t=os.fstat(target)
        if not stat.S_ISREG(t.st_mode) or t.st_uid!=os.getuid() or t.st_nlink!=1 or t.st_size!=s.st_size or (t.st_dev,t.st_ino)==(s.st_dev,s.st_ino):
            raise ValueError('distinct disposable clone identity required')
        os.fchmod(target,0o600);after=os.fstat(target)
        if stamp(after)!=stamp(os.stat(name,dir_fd=parent,follow_symlinks=False)) or stat.S_IMODE(after.st_mode)!=0o600:
            raise ValueError('clone mode/name binding differs')
        now=os.lstat(directory)
        if (now.st_dev,now.st_ino)!=(d.st_dev,d.st_ino):raise ValueError('receiving directory replaced')
        check()
        return dict(source_identity=dict(expected),clone_identity=stamp(after),candidate_id=name,
                    source_payload_read_bytes=0,backend='native-fclonefileat-only' if clone is native_clone else 'original-disposable-test-double')
    finally:close_descriptors(fds)


def prepare_inputs(inputs,sources,directory,*,clone=native_clone):
    """Bind both declared source epochs to the case identities, without hashing.

    The worker hashes only the resulting disposable clones before transport.
    Metadata fences do not replace that byte check or grant input access.
    """
    names=['uncompressed.dng','jpeg.dng']
    if type(inputs) is not list or len(inputs)!=2 or type(sources) is not list or len(sources)!=2:
        raise ValueError('exact two-input/candidate contract required')
    identities=set();digests=set()
    def check_all():
        for item in inputs:
            if stamp(os.lstat(item['path']))!=item['identity']:raise ValueError('input batch epoch changed')
    for item,source,name in zip(inputs,sources,names):
        if type(item) is not dict or set(item)!={'candidate_id','path','sha256','identity'} or item['candidate_id']!=name:
            raise ValueError('fixed typed generated-input ancestry required')
        identity=item['identity'];digest=item['sha256']
        if type(identity) is not dict or set(identity)!=set(FIELDS) or any(type(v) is not int for v in identity.values()):
            raise ValueError('typed full input identity required')
        if type(digest) is not str or re.fullmatch('[0-9a-f]{64}',digest) is None:
            raise ValueError('historical generated-input SHA required')
        if type(source) is not dict or type(source.get('bytes')) is not int or source!=dict(candidate_id=name,sha256=digest,bytes=identity['st_size']):
            raise ValueError('source ancestry differs from receiving identity')
        native_id=(identity['st_dev'],identity['st_ino'])
        if native_id in identities or digest in digests:raise ValueError('distinct generated inputs required')
        identities.add(native_id);digests.add(digest)
    check_all();records=[]
    for item in inputs:
        check_all()
        records.append(prepare(item['path'],item['identity'],directory,item['candidate_id'],clone=clone))
    check_all()
    return records
