"""Finite pilot containment. Only use with helpers compiled to inherit this group."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sync'))
from ownership import OwnedGroup, NativeChild
from measure import CapturedStream


class PhaseCancelled(BaseException):
    pass


def invoke_contained(command, environment, timeout):
    """The phase owns the group; this runner owns and reaps its direct child."""
    child = NativeChild(command, env=environment, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = CapturedStream(child.process.stdout)
    errors = CapturedStream(child.process.stderr)
    fault = None
    expired = False
    try:
        expired = not child.await_reap(timeout)
    except BaseException as error:
        fault = error
    finally:
        closure, _ = child.finish(cancel_reason='phase cancellation' if fault else
                                  'call deadline' if expired else None, grace=4)
        stdout = output.finish()
        stderr = errors.finish()
    if fault:
        raise fault
    return {'returncode': closure['returncode'], 'timed_out': expired,
            'client_cleanup': closure, 'capture_truncated': stdout['truncated'] or stderr['truncated'],
            'stdout': stdout['text'], 'stderr': stderr['text']}


def group_members(group):
    query = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,stat='],
                           capture_output=True, text=True, timeout=1)
    if query.returncode or query.stderr:
        raise RuntimeError('cannot establish owned group closure')
    result = []
    for line in query.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            raise RuntimeError('unqualified process observation')
        if int(fields[1]) == group:
            result.append({'pid': int(fields[0]), 'stat': fields[2]})
    return result


def supervise(function, workspace, seconds=300):
    """Aggregate wall owner, including Python generation/hashing and native work.

    PID remains reserved through group cleanup and absence observation. Helpers
    must not create sessions/groups; the compiled pilot backend enforces that
    for its own spawns. An uncooperative descendant escaping remains unsupported.
    """
    if not 2 < seconds <= 300 or threading.active_count() != 1:
        raise ValueError('finite single-threaded pre-native phase required')
    workspace = Path(workspace)
    marker = workspace/'AGGREGATE-OWNERSHIP-UNRESOLVED.json'
    if marker.exists():
        raise RuntimeError('previous aggregate ownership unresolved')
    start = time.monotonic()
    marker.write_text(json.dumps({'state': 'OWNED', 'seconds': seconds}))
    ready_read, ready_write = os.pipe()
    start_read, start_write = os.pipe()
    sys.stdout.flush(); sys.stderr.flush()
    pid = os.fork()
    if pid == 0:
        os.close(ready_read); os.close(start_write)
        try:
            os.setsid()
            os.write(ready_write, b'R'); os.close(ready_write)
            if os.read(start_read, 1) != b'S':
                os._exit(125)
            os.close(start_read)
            def cancel(_signal, _frame):
                # Suppress repeated cancellation while direct children drain.
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                raise PhaseCancelled()
            signal.signal(signal.SIGTERM, cancel)
            signal.signal(signal.SIGINT, cancel)
            function()
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
    marker.write_text(json.dumps({'state': 'OWNED', 'seconds': seconds, 'pid': pid}))
    receipt = {'pid': pid, 'seconds': seconds, 'closed': False, 'scope': 'finite contained pilot only'}
    previous_term = previous_int = None
    try:
        # Readiness is bounded independently; no native work occurs before ACK.
        import select
        readable, _, _ = select.select([ready_read], [], [], min(1, seconds/4))
        if not readable or os.read(ready_read, 1) != b'R':
            raise RuntimeError('phase did not establish containment')
        os.close(ready_read); ready_read = -1
        previous_term = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(PhaseCancelled()))
        previous_int = signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(PhaseCancelled()))
        os.write(start_write, b'S'); os.close(start_write); start_write = -1
        cleanup_margin = min(8, seconds/2)
        expired = not owner.await_terminal(max(0, start+seconds-cleanup_margin-time.monotonic()))
        receipt['timed_out'] = expired
    except BaseException as error:
        receipt['fault'] = repr(error)
    finally:
        # Keep cleanup from being interrupted by repeated ordinary cancellation.
        if previous_term is not None:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if previous_int is not None:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        for fd in (ready_read, start_write):
            if fd >= 0:
                os.close(fd)
        # Graceful cancellation allows the contained benchmark to reap helpers.
        if not owner.terminal():
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            owner.await_terminal(min(4, max(0, start+seconds-2-time.monotonic())))
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Darwin zombie-only groups can report EPERM. Observation below
            # must still prove every other member gone; never assume closure.
            pass
        deadline = min(start+seconds, time.monotonic()+2)
        while True:
            members = group_members(pid)
            others = [member for member in members if member['pid'] != pid]
            if not others and owner.terminal():
                break
            if time.monotonic() >= deadline:
                marker.write_text(json.dumps(dict(receipt, observed_members=members), indent=2))
                if previous_term is not None:
                    signal.signal(signal.SIGTERM, previous_term)
                if previous_int is not None:
                    signal.signal(signal.SIGINT, previous_int)
                raise RuntimeError('aggregate descendants unresolved; ownership not released')
            time.sleep(.005)
        waited, status, usage = os.wait4(pid, 0)
        assert waited == pid
        owner.reaped = True
        receipt.update(closed=True, reaped=True, returncode=os.waitstatus_to_exitcode(status),
                       group_members_before_leader_reap=members, other_members_absent=True,
                       wall_seconds=time.monotonic()-start,
                       child_user_seconds=usage.ru_utime, child_system_seconds=usage.ru_stime)
        receipt['within_wall_limit'] = receipt['wall_seconds'] <= seconds
        (workspace/'AGGREGATE-CLOSED.json').write_text(json.dumps(receipt, indent=2)+'\n')
        marker.unlink()
        if previous_term is not None:
            signal.signal(signal.SIGTERM, previous_term)
        if previous_int is not None:
            signal.signal(signal.SIGINT, previous_int)
    if receipt.get('fault') or receipt.get('timed_out') or receipt['returncode'] or not receipt['within_wall_limit']:
        raise RuntimeError('native phase failed after genuine group closure')
    return receipt
