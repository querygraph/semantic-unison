"""Owned observation for the original extended-profile qualification calls."""
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests/sdk_host_matrix')]
from private_camera_receiving.close import close_descriptors
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership


def execute(argv, directory, env, log, timeout=120, *, observer=invoke):
    """Observe without signaling; caller must retain on any unresolved result."""
    started = time.monotonic()
    previous = Path.cwd()
    try:
        os.chdir(directory)
        outcome = observer(argv, env, started + timeout)
    finally:
        os.chdir(previous)
    cleanup = outcome['client_cleanup']
    if not (cleanup['reaped'] is True
            and cleanup['other_group_members_absent_before_reap'] is True):
        error = UnresolvedOwnership('extended-profile child/group unresolved')
        error.outcome = outcome
        raise error
    if outcome['capture_truncated']:
        raise ValueError('extended-profile capture truncated; qualification refused')
    output = outcome['stdout'] + outcome['stderr']
    data = output.encode('utf-8')
    descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        pending = memoryview(data)
        while pending:
            count = os.write(descriptor, pending)
            if count <= 0:
                raise OSError('extended-profile log write made no progress')
            pending = pending[count:]
        os.fsync(descriptor)
    finally:
        try:
            close_descriptors([descriptor])
        except UnresolvedOwnership as error:
            # The child is known closed, but that does not settle its log FD.
            error.outcome = outcome
            raise
    if outcome['returncode']:
        print(output[-12000:], end='', flush=True)
    elif output.strip():
        print(output.strip().splitlines()[-1], flush=True)
    import hashlib
    return {'argv': argv, 'cwd': str(directory), 'exit_code': outcome['returncode'],
            'elapsed_seconds': time.monotonic() - started,
            'log': str(log), 'log_sha256': hashlib.sha256(data).hexdigest(),
            'stdout': outcome['stdout'], 'stderr': outcome['stderr'],
            'outcome': outcome}
