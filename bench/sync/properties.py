"""Darwin-only properties of tiny generated fixtures, never camera inputs.

Old readers deliberately ignore ctime/link count: unlinking a replaced target
can change both while the held inode's data, fork and selected properties survive.
"""
import errno
import ctypes
from functools import lru_cache
import hashlib
import os
import stat

NAME = 'org.firstpair.synthetic-clone-removal'
FORK = 'com.apple.ResourceFork'
OLD_VALUE = b'generated-old-xattr'
OLD_FORK = b'generated-old-native-fork'
MAX_DATA = 2 * 1048576


MAX_ATTRIBUTE = 4096

@lru_cache(maxsize=1)
def native():
    # Darwin public xattr ABI; loaded lazily so disabled/other-platform benchmark
    # callers execute no metadata operation or Darwin library load.
    lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    for name, first in [('getxattr',ctypes.c_char_p),('fgetxattr',ctypes.c_int)]:
        fn=getattr(lib,name)
        fn.argtypes=[first,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
        fn.restype=ctypes.c_ssize_t
    lib.setxattr.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int]
    lib.setxattr.restype=ctypes.c_int
    lib.removexattr.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]
    lib.removexattr.restype=ctypes.c_int
    return lib


def attribute(path_or_fd, name):
    fn=native().fgetxattr if isinstance(path_or_fd,int) else native().getxattr
    source=path_or_fd if isinstance(path_or_fd,int) else os.fsencode(path_or_fd)
    size=fn(source,name.encode('ascii'),None,0,0,0)
    if size < 0:
        error=ctypes.get_errno()
        if error in {getattr(errno,'ENODATA',-1),getattr(errno,'ENOATTR',93)}:return None
        raise OSError(error,os.strerror(error))
    require(size <= MAX_ATTRIBUTE, 'generated attribute size exceeds bounded control')
    buffer=ctypes.create_string_buffer(max(1,size))
    actual=fn(source,name.encode('ascii'),buffer,size,0,0)
    if actual < 0:
        error=ctypes.get_errno();raise OSError(error,os.strerror(error))
    require(actual==size, 'attribute changed while reading')
    return buffer.raw[:actual]


def set_attribute(path,name,value):
    require(len(value) <= 65536, 'bounded generated attribute required')
    buffer=ctypes.create_string_buffer(value,max(1,len(value)))
    if native().setxattr(os.fsencode(path),name.encode('ascii'),buffer,len(value),0,0) < 0:
        error=ctypes.get_errno();raise OSError(error,os.strerror(error))


def remove_attribute(path,name):
    if native().removexattr(os.fsencode(path),name.encode('ascii'),0) < 0:
        error=ctypes.get_errno();raise OSError(error,os.strerror(error))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def initialise(path):
    require(stat.S_ISREG(os.lstat(path).st_mode), 'generated regular source required')
    os.chmod(path, 0o640)
    set_attribute(path, NAME, OLD_VALUE)
    set_attribute(path, FORK, OLD_FORK)
    verify_initial(path)


def verify_initial(path_or_fd):
    s = os.fstat(path_or_fd) if isinstance(path_or_fd, int) else os.lstat(path_or_fd)
    require(stat.S_IMODE(s.st_mode) == 0o640 and attribute(path_or_fd, NAME) == OLD_VALUE
            and attribute(path_or_fd, FORK) == OLD_FORK, 'initial generated properties differ')


def remove_source(path):
    verify_initial(path)
    remove_attribute(path, NAME)
    remove_attribute(path, FORK)
    os.chmod(path, 0o400)
    verify_removed(path)


def verify_removed(path):
    s = os.lstat(path)
    require(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode) == 0o400,
            'source-selected readonly mode differs')
    require(attribute(path, NAME) is None, 'inherited selected xattr was not removed')
    require(attribute(path, FORK) in (None, b''), 'inherited native fork remains nonempty')


def old_reader_snapshot(fd):
    verify_initial(fd)
    before = os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_DATA,
            'bounded generated old reader required')
    digest = hashlib.sha256()
    offset = 0
    while offset < before.st_size:
        block = os.pread(fd, min(65536, before.st_size-offset), offset)
        require(bool(block), 'old reader short read')
        offset += len(block)
        digest.update(block)
    after = os.fstat(fd)
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_mode')
    require(all(getattr(before, k) == getattr(after, k) for k in fields), 'old reader changed')
    return {**{k:getattr(after, k) for k in fields}, 'sha256':digest.hexdigest(),
            'xattr_hex':OLD_VALUE.hex(), 'fork_hex':OLD_FORK.hex()}


def noop_snapshot(path):
    verify_removed(path)
    s = os.lstat(path)
    return {k:getattr(s, k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode')}
