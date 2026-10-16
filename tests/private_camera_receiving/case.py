"""Prepared case kernel, NOT an executor or IO admission.

Only an independently admitted outer owner may supply a disposable sender
clone and invoke this case. No originals or Photo paths are opened here.
"""
import hashlib
import os
from pathlib import Path
import stat
import time

from close import close_descriptors, UnresolvedOwnership

TRAILER = b'UNISON-ORIGINAL-DISPOSABLE-RECEIVING-CONTROL\n' * 64
MAX_INPUT = 256 * 1048576
FIELDS = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns',
          'st_mode', 'st_nlink', 'st_uid')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def identity(path):
    observed = os.lstat(path)
    return {name: getattr(observed, name) for name in FIELDS}


def hash_fd(fd, size):
    require(type(size) is int and 0 < size <= MAX_INPUT + len(TRAILER),
            'bounded disposable receiving file required')
    digest = hashlib.sha256()
    offset = 0
    while offset < size:
        data = os.pread(fd, min(1048576, size-offset), offset)
        require(bool(data), 'short disposable receiving read')
        digest.update(data)
        offset += len(data)
    require(os.fstat(fd).st_size == size, 'receiving file changed size')
    return digest.hexdigest()


def sha(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        value = hash_fd(fd, before.st_size)
        after = os.fstat(fd)
        require(all(getattr(before,k)==getattr(after,k) for k in FIELDS),
                'disposable receiving file changed during hash')
        return value
    finally:
        close_descriptors([fd])


def exercise(directory, *, initial_sha256, check_borrowed, invoke, save,
             deadline_monotonic):
    """Exercise one already-owned disposable clone, using supplied owner hooks.

    Required input left/image.dng must already be an independently verified
    native clone, with its own writable inode. check_borrowed performs metadata
    fencing only; invoke must journal before dispatch and settle every separate
    client/server/group. save must persist outcome before verification can fail.
    This function does not confer ownership or implement either hook's contract.
    """
    directory = Path(directory)
    require(directory.is_absolute() and not directory.is_symlink(), 'owned absolute case required')
    source, target = directory/'left/image.dng', directory/'right/image.dng'
    require(source.is_file() and not source.is_symlink() and not target.exists(),
            'prepared disposable sender and unused receiver required')
    before = identity(source)
    require(stat.S_ISREG(before['st_mode']) and stat.S_IMODE(before['st_mode'])==0o600
            and before['st_nlink']==1 and before['st_uid']==os.getuid()
            and 0 < before['st_size'] <= MAX_INPUT, 'sender ownership or size differs')
    require(sha(source)==initial_sha256, 'prepared sender historical identity differs')
    result = {'complete': False, 'calls': {}, 'initial_sha256': initial_sha256,
              'mutation': 'append original synthetic trailer to disposable sender only',
              'photographic_validity_claimed': False, 'semantic_eligibility_claimed': False}
    old = None
    def call(stage):
        require(time.monotonic()+35 < deadline_monotonic, 'no new call near case deadline')
        check_borrowed()
        outcome = invoke(stage)
        result['calls'][stage] = outcome
        save(result)
        check_borrowed()
        require(outcome['returncode']==0 and outcome.get('fault') is None
                and outcome['timed_out'] is False and outcome['capture_truncated'] is False,
                'receiving call failed; preserve original outcome')
        return outcome
    try:
        call('seed')
        require(sha(target)==initial_sha256, 'seed receiving bytes differ')
        old = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        old_stat = os.fstat(old)
        require((old_stat.st_dev,old_stat.st_ino)!=(before['st_dev'],before['st_ino']),
                'receiving inode aliases sender')
        # Never chmod, write, link or rename the borrowed camera-derived input.
        # The independently disposable sender is the sole mutation target.
        fd = os.open(source, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        try:
            current = os.fstat(fd)
            require(all(getattr(current,k)==before[k] for k in FIELDS), 'sender epoch changed before edit')
            data = memoryview(TRAILER)
            while data:
                n = os.write(fd,data)
                require(n>0,'short trailer write')
                data=data[n:]
            os.fsync(fd)
        finally:
            close_descriptors([fd])
        expected=sha(source)
        call('update')
        require(sha(target)==expected, 'updated receiving bytes differ')
        require(hash_fd(old,old_stat.st_size)==initial_sha256, 'retained old receiver data changed')
        updated=identity(target)
        call('noop')
        require(identity(target)==updated and sha(target)==expected and sha(source)==expected,
                'no-op target epoch or exact bytes changed')
        require(hash_fd(old,old_stat.st_size)==initial_sha256, 'old receiver changed after no-op')
        require({p.name for p in (directory/'right').iterdir()}=={'image.dng'}, 'receiver staging residue')
        check_borrowed()
        result.update(complete=True,expected_sha256=expected,exact_receiving=True,
                      retained_old_receiver_unchanged=True,noop_epoch_unchanged=True)
        save(result)
        return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result['failure']=repr(error)
        save(result)
        raise
    finally:
        if old is not None:
            close_descriptors([old])
