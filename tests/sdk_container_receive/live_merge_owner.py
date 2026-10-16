"""Retained CLI-group owner for the live receiving pilot.

No native command-line entry or admission is provided. Production helpers use
separate groups: this module certifies only its own CLI group. Required helper
proofs are audited separately by live_merge_cases; ambiguous failure leaves the
HELPER-OWNERSHIP-UNRESOLVED marker, never a historical-PID cleanup attempt.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import prepare_merged as prep
sys.path.insert(0, str(prep.ROOT / 'bench/sync'))
from ownership import OwnedGroup
from measure import CapturedStream


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def group_members(pid):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,stat='],
                            capture_output=True, text=True, timeout=1)
    if result.returncode or result.stderr:
        raise RuntimeError('process group observation failed')
    output = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            raise RuntimeError('unqualified process group observation')
        if int(fields[1]) == pid:
            output.append({'pid': int(fields[0]), 'state': fields[2]})
    return output


def finish_group(owner, deadline, cancel=False):
    """Never signal after wait4. Refuse to reap while other members remain."""
    if owner.reaped:
        raise RuntimeError('group settled twice')
    if cancel or not owner.terminal():
        try:
            os.killpg(owner.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        owner.await_terminal(max(0, min(2, deadline - time.monotonic())))
    # A terminal direct leader still reserves its PID until the observation and
    # final wait4 below. EPERM is not success: the group query must prove absence.
    try:
        os.killpg(owner.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    while True:
        members = group_members(owner.pid)
        others = [item for item in members if item['pid'] != owner.pid]
        if not others and owner.terminal():
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('CLI group unresolved; retained owner not reaped')
        time.sleep(.005)
    pid, status, usage = os.wait4(owner.pid, 0)
    if pid != owner.pid:
        raise RuntimeError('wrong direct-child reap')
    owner.reaped = True
    owner.process.returncode = os.waitstatus_to_exitcode(status)
    return {'pid': pid, 'returncode': owner.process.returncode, 'reaped': True,
            'other_cli_group_members_absent_before_reap': True,
            'members_before_reap': members,
            'scope': 'CLI group only; separate helper proofs required'}


class Runner:
    def __init__(self, workspace, aggregate_deadline):
        if not hasattr(os, 'waitid') or not hasattr(os, 'WNOWAIT') or not hasattr(os, 'wait4'):
            raise RuntimeError('qualified waitid/wait4 Python required')
        self.workspace = Path(workspace)
        self.deadline = aggregate_deadline
        self.calls = 0
        self.active_owner = None
        self.marker = self.workspace / 'HELPER-OWNERSHIP-UNRESOLVED.json'
        write(self.marker, {'state': 'NOT_YET_PROVED', 'scope': 'all production helper groups'})

    def run_sync(self, command, environment, log_path):
        if self.active_owner is not None:
            raise RuntimeError('previous CLI owner not retired')
        remaining = self.deadline - time.monotonic()
        if self.calls >= 9 or remaining < 10:
            raise RuntimeError('aggregate time/call budget exhausted before dispatch')
        self.calls += 1
        entry = self.workspace / ('CLI-%02d-START.json' % self.calls)
        terminal = self.workspace / ('CLI-%02d-CLOSED.json' % self.calls)
        child = OwnedGroup(command, env=environment, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.active_owner = child
        output = errors = None
        fault = None
        expired = False
        closure = None
        try:
            write(entry, {'pid': child.pid, 'command': command})
            output = CapturedStream(child.process.stdout)
            errors = CapturedStream(child.process.stderr)
            expired = not child.await_terminal(min(80, remaining - 8))
        except BaseException as error:
            fault = error
        finally:
            # Even capture setup failure retains child ownership. If settlement
            # fails, the unresolved marker and direct owner are not retired.
            closure = finish_group(child, min(self.deadline, time.monotonic() + 5),
                                   cancel=bool(fault or expired))
            stdout = output.finish() if output else {'text': '', 'truncated': False}
            stderr = errors.finish() if errors else {'text': '', 'truncated': False}
            if output is None:
                child.process.stdout.close()
            if errors is None:
                child.process.stderr.close()
            write(terminal, dict(closure, timed_out=expired, fault=repr(fault) if fault else None))
            self.active_owner = None
        log = stdout['text'] + stderr['text']
        Path(log_path).write_text(log)
        if fault:
            raise fault
        if expired:
            raise RuntimeError('CLI timed out; helper ownership remains unresolved')
        return {'returncode': closure['returncode'], 'direct_child_reaped': closure['reaped'],
                'capture_truncated': stdout['truncated'] or stderr['truncated'], 'log': log}

    def accept_complete_proofs(self, results):
        # Clear only after all9 CLI runs and exactly6 complete helper proofs.
        if self.active_owner is not None:
            raise ValueError('active CLI owner cannot release helper hold')
        if self.calls != 9 or [item['codec'] for item in results] != list(prep.CODECS):
            raise ValueError('incomplete receiving matrix')
        for index in range(1, 10):
            start = json.loads((self.workspace / ('CLI-%02d-START.json' % index)).read_text())
            closed = json.loads((self.workspace / ('CLI-%02d-CLOSED.json' % index)).read_text())
            if (start['pid'] != closed['pid'] or not closed['reaped']
                    or not closed['other_cli_group_members_absent_before_reap']
                    or closed['returncode'] != 0 or closed['timed_out'] or closed['fault'] is not None):
                raise ValueError('CLI owner closure incomplete')
        for item in results:
            proofs = item['receipts']
            if len(proofs) != 2 or {p['endpoint'] for p in proofs} != {'client', 'server'}:
                raise ValueError('incomplete endpoint proofs')
            if any(p['retained_group_other_members'] != 0 for p in proofs):
                raise ValueError('helper group unresolved')
        write(self.workspace / 'HELPER-PROOFS-COMPLETE.json', {'cli_runs': 9, 'sdk_calls': 6,
              'scope': 'six retained helper-group observations plus actual CLI ownership receipts',
              'results': results})
        self.marker.unlink()
