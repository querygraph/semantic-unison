"""Clone-only private pair preparation; caller owns exact IO/CPU admission.

No original/Photo path defaults, copy fallback, overwrite or cleanup unlink.
The injected clone is only for original disposable tests, not runtime selection.
"""
import hashlib
import os
from pathlib import Path
import stat
from sdk_multifile.clone import native_clone, FIELDS, stamp
from private_camera_receiving.close import close_descriptors


def prepare(source, expected, historical_sha256, directory, *, clone=native_clone):
    source, directory = Path(source), Path(directory)
    if (not source.is_absolute() or not directory.is_absolute()
            or type(expected) is not dict or set(expected) != set(FIELDS)
            or any(type(v) is not int for v in expected.values())
            or type(historical_sha256) is not str or len(historical_sha256) != 64
            or any(c not in '0123456789abcdef' for c in historical_sha256)):
        raise ValueError('exact absolute borrowed source and full historical identity required')
    fds = []
    try:
        src = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        fds.append(src)
        def fence():
            if stamp(os.fstat(src)) != expected or stamp(os.lstat(source)) != expected:
                raise ValueError('borrowed source metadata changed')
        fence()
        s = os.fstat(src)
        if (not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o400
                or s.st_uid != os.getuid() or s.st_nlink != 1 or not 0 < s.st_size <= 256 * 1048576):
            raise ValueError('readonly retained private source required')
        identities = {(s.st_dev, s.st_ino)}
        rows = []
        for side in ('left', 'right'):
            parent_path = directory / side
            parent = os.open(parent_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            fds.append(parent)
            d = os.fstat(parent)
            if d.st_uid != os.getuid() or stat.S_IMODE(d.st_mode) != 0o700:
                raise ValueError('private owned replica directory required')
            try: os.stat('image.dng', dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError: pass
            else: raise ValueError('replica name already consumed; never overwrite')
            fence(); clone(src, parent, 'image.dng'); fence()
            target = os.open('image.dng', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
            fds.append(target)
            t = os.fstat(target)
            if (not stat.S_ISREG(t.st_mode) or t.st_nlink != 1 or t.st_uid != os.getuid()
                    or t.st_size != s.st_size or (t.st_dev, t.st_ino) in identities):
                raise ValueError('distinct disposable replica inode required')
            identities.add((t.st_dev, t.st_ino))
            os.fchmod(target, 0o600)
            before = stamp(os.fstat(target)); digest = hashlib.sha256(); offset = 0
            while offset < t.st_size:
                block = os.pread(target, min(1048576, t.st_size - offset), offset)
                if not block: raise ValueError('short disposable clone read')
                digest.update(block); offset += len(block)
            if digest.hexdigest() != historical_sha256:
                raise ValueError('disposable clone hash differs')
            if before != stamp(os.fstat(target)) or before != stamp(os.stat('image.dng', dir_fd=parent, follow_symlinks=False)):
                raise ValueError('disposable replica binding changed during hash')
            visible = os.lstat(parent_path)
            if (visible.st_dev, visible.st_ino) != (d.st_dev, d.st_ino):
                raise ValueError('replica directory replaced')
            fence()
            rows.append(dict(side=side, identity=before, sha256=digest.hexdigest()))
        return dict(replicas=rows, source_identity=dict(expected), source_payload_read_bytes=0,
                    clone_read_bytes=2 * s.st_size,
                    backend='native-fclonefileat-only' if clone is native_clone else 'original-disposable-test-double')
    finally:
        close_descriptors(fds)
