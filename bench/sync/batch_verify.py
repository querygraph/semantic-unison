"""Independent exact recursive verifier for an owned generated-corpus replica.

No process or FD release authority is supplied by the returned observations.
Unknown close propagates through the qualified carrier; no retry or cleanup.
"""
import os
import re
import stat
from pathlib import Path
from batch_inventory import validate
from workload_fixtures import digest, epoch
from private_camera_receiving.close import close_descriptors


def directory(fd):
    value = os.fstat(fd)
    if not (stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode) == 0o700
            and value.st_uid == os.getuid()):
        raise ValueError('owned private replica directory required')
    return value


def verify(root, rows, *, phase, maximum_file_bytes=262144):
    validate(rows,maximum_file_bytes=maximum_file_bytes)
    if phase not in ('before', 'target'):
        raise ValueError('explicit replica verification phase required')
    expected = [dict(path=r['path'], sha256=r['target_sha256' if phase == 'target' else 'before_sha256'],
                     bytes=r['target_bytes'])
                for r in rows if phase == 'target' or r['before_present']]
    return verify_expected(root, expected, maximum_file_bytes=maximum_file_bytes)


def verify_expected(root, expected, *, maximum_file_bytes=262144):
    """Exact seed or target expectation; empty seed is explicit, not shrinkage."""
    if type(maximum_file_bytes) is not int or not 262144 <= maximum_file_bytes <= 2*1024**3+2*1048576:
        raise ValueError('trusted bounded file ceiling required')
    if type(expected) is not list or len(expected) > 16384:
        raise ValueError('bounded exact file expectations required')
    mapping = {}
    for row in expected:
        if (type(row) is not dict or set(row) != {'path', 'sha256', 'bytes'}
                or type(row['path']) is not str
                or re.fullmatch(r'group-[0-9]{3}/image-[0-9]{5}\.dng', row['path']) is None
                or row['path'] in mapping
                or type(row['sha256']) is not str or re.fullmatch('[0-9a-f]{64}', row['sha256']) is None
                or type(row['bytes']) is not int or not 32768 <= row['bytes'] <= maximum_file_bytes):
            raise ValueError('exact distinct generated file expectation required')
        mapping[row['path']] = row
    if sum(row['bytes'] for row in mapping.values()) > 8*1024**3:
        raise ValueError('declared replica extent exceeded')
    root = Path(root)
    if not root.is_absolute(): raise ValueError('absolute owned replica required')
    groups = {}
    for path, row in mapping.items():
        group, leaf = path.split('/')
        groups.setdefault(group, {})[leaf] = row
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    observations = []
    identities = set()
    try:
        initial = directory(fd)
        if set(os.listdir(fd)) != set(groups):
            raise ValueError('replica directory set differs')
        for group in sorted(groups):
            gfd = os.open(group, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            try:
                native = directory(gfd)
                if set(os.listdir(gfd)) != set(groups[group]):
                    raise ValueError('replica file set differs')
                for leaf, row in sorted(groups[group].items()):
                    ffd = os.open(leaf, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=gfd)
                    try:
                        before = os.fstat(ffd)
                        key = (before.st_dev, before.st_ino)
                        if not (stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o600
                                and before.st_uid == os.getuid() and before.st_nlink == 1
                                and before.st_size == row['bytes'] and key not in identities):
                            raise ValueError('distinct private bounded replica file required')
                        identities.add(key)
                        sha = digest(ffd, before.st_size)
                        if (sha != row['sha256']
                                or epoch(before) != epoch(os.fstat(ffd))
                                or epoch(before) != epoch(os.stat(leaf, dir_fd=gfd, follow_symlinks=False))):
                            raise ValueError('replica bytes or epoch differ')
                        observations.append(dict(path=row['path'], sha256=sha, identity=epoch(before)))
                    finally: close_descriptors([ffd])
                if (epoch(native) != epoch(os.fstat(gfd))
                        or epoch(native) != epoch(os.stat(group, dir_fd=fd, follow_symlinks=False))):
                    raise ValueError('replica group changed during verification')
            finally: close_descriptors([gfd])
        if epoch(initial) != epoch(os.fstat(fd)) or epoch(initial) != epoch(os.lstat(root)):
            raise ValueError('replica root changed during verification')
    finally: close_descriptors([fd])
    return observations
