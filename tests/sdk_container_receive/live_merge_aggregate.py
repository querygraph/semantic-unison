"""Finite aggregate owner; separate production helpers need independent proofs.

No SDK entry point or admission is supplied. Aggregate closure certifies only
its retained worker group. A separate unresolved marker survives unless the
worker returns all expected helper proofs and clean CLI receipts. No signal is
ever sent to historical helper PIDs read from those receipts.
"""
import json
import os
from pathlib import Path
import select
import signal
import sys
import threading
import time
import traceback
from types import SimpleNamespace

from live_merge_owner import OwnedGroup, finish_group, write


class Cancelled(BaseException):
    pass


def require_worker_ownership_support():
    # This owner is constructed with __new__ after fork, so OwnedGroup's
    # constructor preflight does not protect this path. Reject an interpreter
    # without retained-child observation/reaping BEFORE creating any resource.
    methods = ('fork', 'setsid', 'waitid', 'wait4', 'waitstatus_to_exitcode', 'killpg')
    constants = ('P_PID', 'WEXITED', 'WNOHANG', 'WNOWAIT')
    if (any(not callable(getattr(os, name, None)) for name in methods)
            or any(not isinstance(getattr(os, name, None), int) for name in constants)):
        raise RuntimeError('qualified POSIX waitid(WNOWAIT)/wait4 Python required before worker dispatch')


def supervise(function, workspace, *, seconds=300, expected_helper_calls=6,
              maximum_seconds=300):
    # SDK callers retain the default300s ceiling. A separately pinned non-SDK
    # benchmark controller may explicitly request at most two hours.
    if type(maximum_seconds) is not int or not 5 <= maximum_seconds <= 7200:
        raise ValueError('invalid explicit aggregate ceiling')
    if threading.active_count() != 1 or not 5 <= seconds <= maximum_seconds:
        raise ValueError('single-threaded finite aggregate required')
    if expected_helper_calls not in (0, 6):
        raise ValueError('only zero-helper fixtures or exact six-helper pilot allowed')
    require_worker_ownership_support()
    work = Path(workspace)
    aggregate_marker = work / 'AGGREGATE-OWNERSHIP-UNRESOLVED.json'
    external_marker = work / 'EXTERNAL-HELPERS-UNRESOLVED.json'
    write(aggregate_marker, {'state': 'PREPARING', 'seconds': seconds})
    write(external_marker, {'state': 'PROOFS_PENDING', 'expected_calls': expected_helper_calls})
    start = time.monotonic()
    deadline = start + seconds
    ready_read = ready_write = start_read = start_write = None
    try:
        ready_read, ready_write = os.pipe()
        start_read, start_write = os.pipe()
        sys.stdout.flush(); sys.stderr.flush()
        pid = os.fork()
    except BaseException:
        for fd in (ready_read, ready_write, start_read, start_write):
            if fd is not None:
                # A failed close must neither skip sibling descriptors nor
                # replace the original acquisition/flush/fork exception.
                try:
                    os.close(fd)
                except BaseException:
                    pass
        raise
    if pid == 0:
        os.close(ready_read); os.close(start_write)
        try:
            os.setsid()
            os.write(ready_write, b'R'); os.close(ready_write)
            if os.read(start_read, 1) != b'S':
                os._exit(125)
            os.close(start_read)
            def cancel(*_args):
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                raise Cancelled()
            signal.signal(signal.SIGTERM, cancel)
            signal.signal(signal.SIGINT, cancel)
            function(deadline)
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(0)
        except BaseException:
            traceback.print_exc()
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(1)
    os.close(ready_write); os.close(start_read)
    owner = OwnedGroup.__new__(OwnedGroup)
    owner.process = SimpleNamespace(pid=pid, returncode=None)
    owner.reaped = False
    previous = {}
    fault = None
    expired = False
    closure = None
    try:
        write(work / 'AGGREGATE-START.json', {'pid': pid, 'seconds': seconds})
        readable, _, _ = select.select([ready_read], [], [], 1)
        if not readable or os.read(ready_read, 1) != b'R':
            raise RuntimeError('worker failed pre-dispatch group readiness')
        os.close(ready_read); ready_read = -1
        def cancel(*_args):
            raise Cancelled()
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, cancel)
        os.write(start_write, b'S'); os.close(start_write); start_write = -1
        # Leave8s for owned CLI cancellation, worker group observation and reap.
        expired = not owner.await_terminal(max(0, deadline - 8 - time.monotonic()))
    except BaseException as error:
        fault = repr(error)
    finally:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        for fd in (ready_read, start_write):
            if fd >= 0:
                os.close(fd)
        try:
            closure = finish_group(owner, deadline, cancel=bool(fault or expired))
            closure.update(wall_seconds=time.monotonic() - start, seconds=seconds,
                           timed_out=expired, fault=fault,
                           scope='aggregate worker group only; external helper proof gate is separate')
            closure['within_wall_limit'] = closure['wall_seconds'] <= seconds
            write(work / 'AGGREGATE-CLOSED.json', closure)
            aggregate_marker.unlink()
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    if fault or expired or closure['returncode'] or not closure['within_wall_limit']:
        raise RuntimeError('worker failed; external helper hold retained')
    if expected_helper_calls:
        proof = json.loads((work / 'HELPER-PROOFS-COMPLETE.json').read_text())
        if (proof['cli_runs'] != 9 or proof['sdk_calls'] != 6
                or (work / 'HELPER-OWNERSHIP-UNRESOLVED.json').exists()
                or len(proof['results']) != 3
                or sum(len(item['receipts']) for item in proof['results']) != 6):
            raise RuntimeError('external helper proof incomplete; hold retained')
        for index in range(1, 10):
            receipt = json.loads((work / ('CLI-%02d-CLOSED.json' % index)).read_text())
            if (not receipt['reaped'] or not receipt['other_cli_group_members_absent_before_reap']
                    or receipt['returncode'] or receipt['timed_out'] or receipt['fault']):
                raise RuntimeError('CLI closure incomplete; hold retained')
        if any(item['retained_group_other_members'] != 0
               for result in proof['results'] for item in result['receipts']):
            raise RuntimeError('external helper observation unresolved; hold retained')
    external_marker.unlink()
    write(work / 'SUPERVISOR-CLOSED.json', {'aggregate': closure,
          'expected_helper_calls': expected_helper_calls, 'external_proofs_accepted': True,
          'scope': 'bounded owned worker plus separately audited retained helper observations'})
    return closure
