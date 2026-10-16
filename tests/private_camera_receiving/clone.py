"""Source-only clone preparation; caller must already own exact IO admission.

No default input, command-line entrypoint, source hash, copy fallback or cleanup
unlink. Failed clones are retained in the owned workspace for evidence.
"""
import ctypes
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared_cpu_pool import close_descriptors
from case import FIELDS, MAX_INPUT, require


def stamp(s):
    return {name:getattr(s,name) for name in FIELDS}


def native_clone(source_fd, directory_fd, name):
    lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    fn=lib.fclonefileat
    fn.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32]
    fn.restype=ctypes.c_int
    if fn(source_fd,directory_fd,os.fsencode(name),0):
        error=ctypes.get_errno()
        raise OSError(error,'fclonefileat refused; no full-copy fallback')


def prepare(source, expected, directory, *, clone=native_clone):
    """Create directory/image.dng; metadata fence source, never read its payload.

    expected is the exact admitted native eight-field identity. The supplied
    clone callback is solely for original disposable unit fixtures, not runtime
    backend selection. An admitted executor must use native_clone only.
    """
    source,directory=Path(source),Path(directory)
    require(source.is_absolute() and directory.is_absolute(),'absolute owned paths required')
    require(set(expected)==set(FIELDS),'exact native identity fields required')
    descriptors=[]
    try:
        src=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        descriptors.append(src)
        def check():
            require(stamp(os.fstat(src))==expected==stamp(os.lstat(source)),
                    'borrowed input native epoch changed')
        check();s=os.fstat(src)
        require(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o400
                and s.st_nlink==1 and s.st_uid==os.getuid()
                and 0<s.st_size<=MAX_INPUT,'readonly owned regular borrowed input required')
        parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        descriptors.append(parent);d=os.fstat(parent)
        require(stat.S_IMODE(d.st_mode)==0o700 and d.st_uid==os.getuid(),
                'private owned sender directory required')
        try:
            os.stat('image.dng',dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError('sender already exists; never overwrite/retry')
        clone(src,parent,'image.dng')
        check()
        target=os.open('image.dng',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        descriptors.append(target);t=os.fstat(target)
        require(stat.S_ISREG(t.st_mode) and t.st_nlink==1 and t.st_uid==os.getuid()
                and t.st_size==s.st_size and (t.st_dev,t.st_ino)!=(s.st_dev,s.st_ino),
                'native clone identity/type/size differs')
        os.fchmod(target,0o600)
        after=os.fstat(target);named=os.stat('image.dng',dir_fd=parent,follow_symlinks=False)
        require(stamp(after)==stamp(named) and stat.S_IMODE(after.st_mode)==0o600,
                'mutable disposable clone binding differs')
        current=os.lstat(directory)
        require((current.st_dev,current.st_ino)==(d.st_dev,d.st_ino),
                'sender directory binding changed')
        check()
        return {'source_identity':expected,'clone_identity':stamp(after),
                'source_payload_read_bytes':0,
                'backend':('native-fclonefileat-only' if clone is native_clone
                           else 'original-disposable-test-double')}
    finally:
        # Shared close protocol retains all remaining/uncertain descriptions;
        # an owning executor must retain that carrier, never retry numeric FDs.
        close_descriptors(descriptors)
