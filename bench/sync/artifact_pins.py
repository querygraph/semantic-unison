"""Optional exact artifact admission before executing benchmark binaries.

Private trusted snapshot paths only; native epoch fencing is cooperative and
cannot defeat a hostile same-UID writer between hashing and executable launch.
"""
import hashlib
import os
from pathlib import Path
import stat

MAX_BYTES = 64 * 1048576
FIELDS = ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_mtime_ns', 'st_ctime_ns')


def parse(values):
    result = {}
    for value in values:
        label, separator, digest = value.partition('=')
        if not separator or not label or label in result or len(digest) != 64 or any(
                c not in '0123456789abcdef' for c in digest):
            raise ValueError('unique label=lowercase-SHA256 artifact pins required')
        result[label] = digest
    return result


def stable_sha(path):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    def identity(s):
        return tuple(getattr(s, field) for field in FIELDS)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_BYTES:
            raise ValueError('bounded nonempty regular artifact required')
        digest = hashlib.sha256()
        total = 0
        while total <= MAX_BYTES:
            block = os.read(fd, min(1048576, MAX_BYTES + 1 - total))
            if not block:
                break
            total += len(block)
            digest.update(block)
        if total != before.st_size or identity(before) != identity(os.fstat(fd)) or \
                identity(before) != identity(os.lstat(path)):
            raise ValueError('artifact native epoch changed while hashing')
        return digest.hexdigest()
    finally:
        os.close(fd)


def verify(paths, pins):
    if not pins:
        return {}  # Legacy caller has requested no admission; no new IO.
    if set(paths) != set(pins):
        raise ValueError('artifact labels must exactly cover the executable set')
    actual = {label: stable_sha(path) for label, path in paths.items()}
    if actual != pins:
        raise ValueError('artifact content differs from admitted SHA256')
    return actual
