"""Retain child PID reservations until cleanup; reap each owned child once."""
import os
import signal
import subprocess
import sys
import time


class OwnedGroup:
    """Own a new-session leader; never release its PID before group cleanup."""

    def __init__(self, command, **arguments):
        if not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT"):
            raise RuntimeError("benchmark ownership requires waitid(WNOWAIT)")
        self.process = subprocess.Popen(command, start_new_session=True, **arguments)
        self.reaped = False

    @property
    def pid(self):
        return self.process.pid

    def terminal(self):
        if self.reaped:
            raise RuntimeError("owned process already reaped")
        # WNOWAIT leaves even an exited leader as our unreaped child. Its PID
        # cannot be reassigned before killpg, including a crashed supervisor.
        return os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None

    def await_terminal(self, timeout):
        deadline = time.monotonic() + timeout
        while not self.terminal():
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.005)
        return True

    def finish(self, timeout=0, cancel_reason=None, grace=2):
        if self.reaped:
            raise RuntimeError("owned group settled twice")
        terminal = False
        cancellation = cancel_reason
        observation_error = None
        group_result = None
        try:
            terminal = self.await_terminal(timeout)
            if not terminal:
                cancellation = cancellation or "owned supervisor settlement deadline"
                try:
                    os.kill(self.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                terminal = self.await_terminal(grace)
        except BaseException as error:
            observation_error = repr(error)
            cancellation = cancellation or observation_error
        finally:
            # Retain even a terminal leader until group cleanup. This path
            # also runs after an exception during non-reaping observation.
            try:
                os.killpg(self.pid, signal.SIGKILL)
                group_result = "signal_sent"
            except ProcessLookupError:
                group_result = "absent"
            except PermissionError:
                # Darwin returns EPERM for a group containing only zombies.
                # Probe only this reserved group, and never turn EPERM with
                # a living member into evidence that cleanup succeeded.
                if sys.platform != "darwin" or not terminal:
                    raise
                deadline = time.monotonic() + 0.2
                while True:
                    query = subprocess.run(["/bin/ps", "-g", str(self.pid), "-o", "pid=,pgid=,stat="],
                                           capture_output=True, text=True, timeout=1)
                    rows = [row.split() for row in query.stdout.splitlines()]
                    if query.returncode not in (0, 1) or query.stderr or any(
                            len(row) != 3 or not row[0].isdigit() or not row[1].isdigit() or
                            int(row[1]) != self.pid or not row[2].startswith("Z") for row in rows):
                        raise RuntimeError("owned group signal denied with unqualified members: " + repr(rows))
                    if not rows:
                        group_result = "no_members_darwin"
                        break
                    if len(rows) == 1 and int(rows[0][0]) == self.pid:
                        group_result = "only_owned_leader_zombie_darwin"
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("unattested zombie descendants persisted: " + repr(rows))
                    time.sleep(0.005)
            waited, status, usage = os.wait4(self.pid, 0)
            assert waited == self.pid
            self.reaped = True
            self.process.returncode = os.waitstatus_to_exitcode(status)
        return {"pid": self.pid, "returncode": self.process.returncode,
                "reaped": True, "cancel_reason": cancellation,
                "hard_kill_required": not terminal,
                "observation_error": observation_error,
                "group_cleanup_result": group_result,
                "group_cleanup_before_leader_reap": True}, usage


class NativeChild:
    """The supervisor's one native child, with no implicit Popen reap."""

    def __init__(self, command, **arguments):
        self.process = subprocess.Popen(command, **arguments)
        self.status = None
        self.usage = None

    @property
    def pid(self):
        return self.process.pid

    def try_reap(self):
        if self.status is not None:
            return True
        waited, status, usage = os.wait4(self.pid, os.WNOHANG)
        if not waited:
            return False
        assert waited == self.pid
        self.status, self.usage = status, usage
        self.process.returncode = os.waitstatus_to_exitcode(status)
        return True

    def signal(self, number):
        if self.status is None:
            # An exited but unreaped child still reserves this exact PID.
            try:
                os.kill(self.pid, number)
            except ProcessLookupError:
                pass

    def await_reap(self, timeout):
        deadline = time.monotonic() + timeout
        while not self.try_reap():
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.005)
        return True

    def finish(self, cancel_reason=None, grace=0.2, normal_exit_timeout=None):
        # Output EOF is not wait4 evidence: the process may still be shutting
        # down, or merely descheduled. Keep normal exit separate from the
        # short TERM grace. Existing callers retain their original policy.
        normal_wait = grace if normal_exit_timeout is None else normal_exit_timeout
        if normal_wait < 0:
            raise ValueError("negative normal-exit timeout")
        before = time.monotonic()
        reason = cancel_reason
        if reason:
            self.signal(signal.SIGTERM)
        reaped = self.await_reap(grace if reason else normal_wait)
        if not reaped and not reason:
            reason = "native child did not settle after output EOF"
            self.signal(signal.SIGTERM)
            reaped = self.await_reap(grace)
        forced = not reaped
        if forced:
            self.signal(signal.SIGKILL)
            waited, self.status, self.usage = os.wait4(self.pid, 0)
            assert waited == self.pid
            self.process.returncode = os.waitstatus_to_exitcode(self.status)
        return {"pid": self.pid, "returncode": self.process.returncode,
                "reaped": self.status is not None, "cancel_reason": reason,
                "hard_kill_required": forced,
                "normal_exit_timeout_seconds": normal_wait,
                "settlement_wall_seconds": time.monotonic() - before}, self.usage
