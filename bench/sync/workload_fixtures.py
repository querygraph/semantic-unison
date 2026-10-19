"""Owned generated-file consumer for pure workload recipes; never camera editing."""
import hashlib
import os
from pathlib import Path
import random
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tests'))
from private_camera_receiving.close import close_descriptors
from workloads import initial_writes, layout, recipe

INVERT = bytes(range(255, -1, -1))
FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_uid')


def epoch(value):
    return {k: getattr(value, k) for k in FIELDS}


def write_at(fd, data, offset):
    pending = memoryview(data)
    while pending:
        count = os.pwrite(fd, pending, offset)
        if count <= 0:
            raise OSError('generated fixture write made no progress')
        pending = pending[count:]
        offset += count


def digest(fd, count):
    value = hashlib.sha256()
    at = 0
    while at < count:
        block = os.pread(fd, min(1048576, count-at), at)
        if not block:
            raise ValueError('generated fixture ended during hash')
        at += len(block)
        value.update(block)
    if os.pread(fd, 1, count):
        raise ValueError('generated fixture grew during hash')
    return value.hexdigest()


def fence(fd, path, expected):
    actual = os.fstat(fd)
    if not (stat.S_ISREG(actual.st_mode) and stat.S_IMODE(actual.st_mode) == 0o600
            and actual.st_uid == os.getuid() and actual.st_nlink == 1
            and epoch(actual) == expected == epoch(os.lstat(path))):
        raise ValueError('generated fixture identity changed')


def create(path, size, packet_bytes, index):
    shape = layout(size, packet_bytes)
    if type(index) is not int or not 0 <= index <= 255:
        raise ValueError('bounded generated fixture seed required')
    path = Path(path)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        seed = 0x51DE0000 + index
        rng = random.Random(seed)
        at = 0
        while at < size:
            amount = min(1048576, size-at)
            write_at(fd, rng.randbytes(amount), at)
            at += amount
        for change in initial_writes(shape):
            write_at(fd, change.data, change.offset)
        os.fsync(fd)
        before = epoch(os.fstat(fd))
        value = digest(fd, size)
        fence(fd, path, before)
        return dict(schema=shape.schema, name=path.name, size_bytes=size,
                    packet_offset=shape.packet_offset, packet_bytes=packet_bytes,
                    protected_image_offset=shape.image_offset,
                    preview_offset=shape.preview_offset, preview_bytes=shape.preview_bytes,
                    seed=seed, before_sha256=value, source_identity=before)
    finally:
        close_descriptors([fd])


def edit(path, metadata, kind):
    if metadata.get('schema') != 'unison-generated-workload-tiff/1':
        raise ValueError('generated workload schema required')
    shape = layout(metadata['size_bytes'], metadata['packet_bytes'], metadata['preview_bytes'])
    changes = recipe(shape, kind)
    path = Path(path)
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        fence(fd, path, metadata['source_identity'])
        if digest(fd, shape.size) != metadata['before_sha256']:
            raise ValueError('generated source bytes changed before edit')
        fence(fd, path, metadata['source_identity'])
        if changes.full_xor:
            at = 0
            while at < shape.size:
                data = os.pread(fd, min(1048576, shape.size-at), at)
                if not data:
                    raise ValueError('full generated replacement ended early')
                write_at(fd, data.translate(INVERT), at)
                at += len(data)
        for change in changes.writes:
            data = change.data
            if change.xor:
                before = os.pread(fd, len(data), change.offset)
                if len(before) != len(data):
                    raise ValueError('generated XOR read was short')
                data = bytes(a ^ b for a, b in zip(before, data))
            write_at(fd, data, change.offset)
        os.ftruncate(fd, changes.target_size)
        os.fsync(fd)
        after = epoch(os.fstat(fd))
        expected = digest(fd, changes.target_size)
        fence(fd, path, after)
        metadata.update(workload=kind, after_size_bytes=changes.target_size,
                        expected_transfer=changes.expected_transfer)
        return expected
    finally:
        close_descriptors([fd])
