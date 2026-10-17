"""Fresh disposable-root verification under caller-owned IO, never source IO.

No mutations, path following, SDK, process management or release authority.
All FD close uncertainty escapes through the qualified retained carrier.
"""
import hashlib
import os
from pathlib import Path
import stat
from sdk_multifile.clone import FIELDS, stamp
from private_camera_receiving.close import close_descriptors


def verify_roots(directory, preparation, *, source):
    directory = Path(directory)
    rows = preparation.get('replicas')
    if (not directory.is_absolute() or type(rows) is not list or len(rows) != 2
            or [r.get('side') for r in rows] != ['left', 'right']):
        raise ValueError('exact owned pair preparation required')
    if (type(source) is not dict or type(source.get('bytes')) is not int
            or not 0 < source['bytes'] <= 256 * 1048576
            or type(source.get('sha256')) is not str or len(source['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in source['sha256'])):
        raise ValueError('exact admitted source byte/hash identity required')
    borrowed = preparation.get('source_identity')
    if (type(borrowed) is not dict or set(borrowed) != set(FIELDS)
            or any(type(v) is not int for v in borrowed.values())
            or borrowed['st_size'] != source['bytes']):
        raise ValueError('bound preparation source metadata required')
    for row in rows:
        for name in ('identity', 'directory_identity'):
            value = row.get(name)
            if (type(value) is not dict or set(value) != set(FIELDS)
                    or any(type(v) is not int for v in value.values())):
                raise ValueError('full typed replica/file directory identities required')
        digest = row.get('sha256')
        if (type(digest) is not str or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('exact historical clone hash required')
        if digest != source['sha256'] or row['identity']['st_size'] != source['bytes']:
            raise ValueError('replica declaration differs from admitted source')
    fds, observations, proofs = [], [], []
    try:
        root = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        fds.append(root)
        root_info = os.fstat(root)
        if root_info.st_uid != os.getuid() or stat.S_IMODE(root_info.st_mode) != 0o700:
            raise ValueError('private owned case namespace required')
        seen = {(borrowed['st_dev'], borrowed['st_ino'])}
        for row in rows:
            parent = os.open(row['side'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root)
            fds.append(parent)
            d = os.fstat(parent)
            if (stamp(d) != row['directory_identity'] or d.st_uid != os.getuid()
                    or stat.S_IMODE(d.st_mode) != 0o700
                    or os.listdir(parent) != ['image.dng']):
                raise ValueError('replica directory identity or exact roster changed')
            fd = os.open('image.dng', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
            fds.append(fd)
            info = os.fstat(fd)
            inode = (info.st_dev, info.st_ino)
            if (stamp(info) != row['identity'] or not stat.S_ISREG(info.st_mode)
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                    or info.st_uid != os.getuid() or not 0 < info.st_size <= 256 * 1048576
                    or inode in seen):
                raise ValueError('distinct mutable disposable file identity changed')
            seen.add(inode)
            digest = hashlib.sha256(); offset = 0
            while offset < info.st_size:
                block = os.pread(fd, min(1048576, info.st_size - offset), offset)
                if not block: raise ValueError('short disposable verification read')
                digest.update(block); offset += len(block)
            if digest.hexdigest() != row['sha256']:
                raise ValueError('disposable file bytes changed')
            observations.append((row, parent, fd))
            proofs.append(dict(side=row['side'], identity=stamp(info), sha256=digest.hexdigest()))
        # Fence BOTH held pairs after the last read. Retain descriptors until
        # these cross-pair observations and the outer namespace check complete.
        for row, parent, fd in observations:
            if (stamp(os.fstat(fd)) != row['identity']
                    or stamp(os.stat('image.dng', dir_fd=parent, follow_symlinks=False)) != row['identity']
                    or stamp(os.fstat(parent)) != row['directory_identity']
                    or stamp(os.stat(row['side'], dir_fd=root, follow_symlinks=False)) != row['directory_identity']
                    or os.listdir(parent) != ['image.dng']):
                raise ValueError('replica pair binding changed during verification')
        visible = os.lstat(directory)
        if (visible.st_dev, visible.st_ino) != (root_info.st_dev, root_info.st_ino):
            raise ValueError('case namespace replaced during verification')
        return dict(schema='unison-all-scanned-sdk-root-verification/1', replicas=proofs,
                    payload_read_bytes=sum(r['identity']['st_size'] for r in rows),
                    source_payload_opened=False, resource_release_authorized=False)
    finally:
        close_descriptors(fds)
