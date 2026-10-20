"""Actual disposable nine-FD worker control; no canonical IO or camera access."""
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

import private_maker_identity_entry as entry
from private_maker_identity_test import shape
from private_maker_identity_entry_test import plan as template
from private_maker_slice import stamp
from private_maker_lifecycle import Lease
from private_camera_receiving.close import close_descriptors
import shared_dispatch as dispatch

HERE = Path(__file__).resolve()


def command(path, digest, workspace):
    return [sys.executable, str(HERE), '--worker', '--plan', str(path),
            '--plan-sha256', digest, '--workspace', str(workspace)]


def child():
    from sdk_host_matrix import shared_binding
    args = SimpleNamespace(plan=sys.argv[3], plan_sha256=sys.argv[5], workspace=sys.argv[7])
    value = entry.document(args.plan, args.plan_sha256)
    inventory = entry.document(Path(args.workspace) / 'DISPOSABLE-INVENTORY.json')
    # These explicit substitutions are fixture scope, never canonical proof.
    with patch.object(entry, 'check', side_effect=lambda v: v), \
         patch.object(entry, 'child_argv', side_effect=command), \
         patch.object(shared_binding, 'inventory', return_value=tuple(tuple(r) for r in inventory)):
        return entry.worker(args, value)


def controls():
    root = Path(tempfile.mkdtemp(prefix='unison-model-disposable-', dir='/private/tmp'))
    work = root / 'worker'; work.mkdir(mode=0o700)
    for name in ('cpu', 'io'): (root / name).mkdir(mode=0o700)
    cpu = Lease(root / 'cpu', 8); io = Lease(root / 'io', 1)
    source = root / 'authored-only'; source.write_bytes(b'\0' * 11440 + b'MODEL123\0'); source.chmod(0o400)
    saved = root / 'synthetic-saved.json'
    entry.save(saved, dict(schema='unison-private-maker-worker/1', complete=True,
                          diagnostic=dict(outcome='CANDIDATE_SHAPE', shape=shape())))
    value = template(); value.update(workspace=str(work),
        source=dict(path=str(source), identity=stamp(os.lstat(source))),
        saved_result=dict(path=str(saved), sha256=hashlib.sha256(saved.read_bytes()).hexdigest()))
    packet = root / 'synthetic-plan.json'; entry.save(packet, value)
    digest = hashlib.sha256(packet.read_bytes()).hexdigest()
    fds = cpu.fds + io.fds
    entry.save(work / 'DISPOSABLE-INVENTORY.json',
               [[os.fstat(fd).st_dev, os.fstat(fd).st_ino] for fd in fds])
    class CPU:
        def try_acquire(self, indexes):
            assert indexes == tuple(range(8)); return cpu
    class IO:
        def try_acquire(self): return io
    with ExitStack() as stack:
        stack.enter_context(patch.object(dispatch.Pool, 'read', return_value=CPU()))
        stack.enter_context(patch.object(dispatch, 'checked_io_request', return_value=(IO(), time.time()+60)))
        stack.enter_context(patch.object(entry, 'checked_plan', return_value=value))
        stack.enter_context(patch.object(entry, 'check', side_effect=lambda v: v))
        status = dispatch.run(entry.TARGET, command(packet, digest, work), work, 8,
                              io_admission=dict(path='/inert-disposable-only', sha256='0'*64))
    assert status == 0 and cpu.closed and io.closed
    result = entry.document(work / 'RESULT.json')
    closed = entry.document(work / 'SHARED-CLOSED.json')
    assert result['complete'] and result['diagnostic']['candidate_text'] == 'MODEL123'
    assert closed['child']['reaped'] and closed['child']['returncode'] == 0
    assert closed['child']['other_group_members_absent_before_reap']
    assert closed['tokens_closed'] and closed['io_barrier_acquired_and_closed']
    # Actual fresh disposable descriptions prove the old copies released locks.
    import fcntl
    for folder, count in (('cpu', 8), ('io', 1)):
        for index in range(count):
            fd = os.open(root / folder / str(index), os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
            try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally: close_descriptors([fd])
    entry.save(root / 'CONTROL-RESULT.json', dict(complete=True, worker=str(work),
        disposable_nine_FD_inheritance=True, independent_parent_audit=True,
        fresh_disposable_reacquisition=True, canonical_inventory_substituted=True,
        canonical_IO_acquired=False, media_payload_opened=False, SDK_invoked=False))
    print(root, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(child() if len(sys.argv) > 1 and sys.argv[1] == '--worker' else controls())
