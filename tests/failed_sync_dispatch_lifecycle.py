"""Actual Python peer/dispatcher closure with disposable inner leases.

The outer dispatcher holds real Unison CPU tokens. The inner IO/CPU objects
are disposable FD leases, not canonical IO admission or physical isolation.
"""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

import shared_dispatch as dispatch

HERE = Path(__file__).resolve()


class DisposableLease:
    def __init__(self, path):
        self.fds = (os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600),)
        self.closed = False

    def close_after_verified_settlement(self, **proof):
        assert proof and all(value is True for value in proof.values())
        assert not self.closed
        self.closed = True
        for fd in self.fds:
            os.close(fd)


def peer_worker(output):
    from journal_lifecycle_test import main
    stream = io.StringIO()
    with redirect_stdout(stream):
        main()
    peer = json.loads(stream.getvalue())
    result = json.loads(Path(peer['journal']).read_text())
    (output/'RESULT.json').write_text(json.dumps(result)+'\n')
    print(json.dumps(peer), flush=True)
    return 7


def worker():
    output = Path(tempfile.mkdtemp(prefix='unison-failed-sync-inner-'))
    cpu = DisposableLease(output/'cpu-disposable')
    io_lease = DisposableLease(output/'io-disposable')
    class Pool:
        def try_acquire(self, *args):
            return cpu
    class IOPool:
        def try_acquire(self):
            return io_lease
    pool, io_pool = Pool(), IOPool()
    deadline = time.time()+60
    # Admission authentication and real physical IO are deliberately excluded;
    # the actual source audit, child groups and settlement are not mocked.
    with patch.object(dispatch.Pool, 'read', return_value=pool), \
         patch.object(dispatch, 'checked_io_request', return_value=(io_pool, deadline)):
        code = dispatch.run('sync-functional',
            [sys.executable, str(HERE), '--peer-worker', str(output)], output, 8,
            io_admission={'path': '/disposable-only', 'sha256': '0'*64})
    assert code == 7 and cpu.closed and io_lease.closed
    closed = json.loads((output/'SHARED-CLOSED.json').read_text())
    proof = json.loads((output/'SHARED-SERVER-AUDIT.json').read_text())
    assert closed['child']['returncode'] == 7 and closed['child']['reaped']
    assert closed['child']['other_group_members_absent_before_reap']
    assert proof['functional_result'] == 'FAILED'
    assert proof['attempted_cli_invocations'] == 3
    assert proof['server_not_created_invocations'] == 1
    print(json.dumps({'workspace': str(output), 'inner_result': code,
                      'disposable_leases_closed': True, 'audit': proof,
                      'scope': 'actual peer/dispatcher settlement; inner IO/CPU leases disposable'}))
    return 0


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--peer-worker':
        raise SystemExit(peer_worker(Path(sys.argv[2])))
    if sys.argv[1:] == ['--worker']:
        raise SystemExit(worker())
    if len(sys.argv) != 1:
        raise ValueError('fixed lifecycle command only')
    os.umask(0o077)
    output = Path(tempfile.mkdtemp(prefix='unison-failed-sync-outer-'))
    print('Outer owner workspace: '+str(output), flush=True)
    raise SystemExit(dispatch.run('shared-io-controls',
        [sys.executable, str(HERE), '--worker'], output, 8))
