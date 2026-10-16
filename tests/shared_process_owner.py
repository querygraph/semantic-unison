"""Retained group settlement for bounded Adobe-free shared entry points."""
import os
import signal
import subprocess
import time


def retain_forever():
    """A coordinated recovery must resolve ownership before this owner exits."""
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, signal.SIG_IGN)
    while True:
        time.sleep(1)


def retain_after_record(record):
    # Disk/log failure must not drop the descriptors that the record describes.
    try:
        record()
    finally:
        retain_forever()


def settle(owner, deadline):
    """Keep the direct leader unreaped until every other group member is gone."""
    if owner.reaped:
        raise RuntimeError('shared child already reaped')
    terminal = owner.await_terminal(max(0, deadline - time.monotonic() - 2))
    if not terminal:
        try:
            os.killpg(owner.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        owner.await_terminal(max(0, min(1, deadline - time.monotonic())))
    try:
        os.killpg(owner.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Neither exception establishes settlement; the retained-PID census
        # below must still succeed before wait4 or token release.
        pass
    while True:
        result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,stat='],
                                capture_output=True, text=True, timeout=1)
        if result.returncode or result.stderr:
            raise RuntimeError('shared group census failed')
        members = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
                raise RuntimeError('shared group census malformed')
            if int(fields[1]) == owner.pid:
                members.append({'pid': int(fields[0]), 'state': fields[2]})
        if not any(row['pid'] != owner.pid for row in members) and owner.terminal():
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('shared child/group outcome unknown; retain owner')
        time.sleep(.005)
    pid, status, _ = os.wait4(owner.pid, 0)
    if pid != owner.pid:
        raise RuntimeError('shared child reap identity differs')
    owner.reaped = True
    owner.process.returncode = os.waitstatus_to_exitcode(status)
    return {'pid': pid, 'returncode': owner.process.returncode, 'reaped': True,
            'other_group_members_absent_before_reap': True,
            'members_before_reap': members, 'timed_out': not terminal,
            'scope': 'owned group only; no separately-sessioned children admitted'}
