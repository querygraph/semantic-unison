"""Bounded captured streams and a subprocess owned through group settlement."""
import os
import subprocess
import threading
import time

from ownership import OwnedGroup


def receipt(usage):
    return {"wait4_user_seconds": usage.ru_utime,
            "wait4_system_seconds": usage.ru_stime,
            "wait4_maxrss_native_units": usage.ru_maxrss,
            "minor_faults": usage.ru_minflt, "major_faults": usage.ru_majflt,
            "block_input_operations": usage.ru_inblock,
            "block_output_operations": usage.ru_oublock}


class CapturedStream:
    """Drain indefinitely without retaining more than the declared byte limit."""

    def __init__(self, stream, limit=4 * 1048576):
        self.stream = stream
        self.limit = limit
        self.chunks = []
        self.total = 0
        self.error = None
        self.thread = threading.Thread(target=self.drain, daemon=True)
        self.thread.start()

    def drain(self):
        try:
            while True:
                data = self.stream.read(65536)
                if not data:
                    return
                previous = self.total
                self.total += len(data)
                if previous < self.limit:
                    self.chunks.append(data[:self.limit - previous])
        except BaseException as error:
            self.error = repr(error)

    def finish(self):
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise RuntimeError("descendant retained captured output after owned group cleanup")
        self.stream.close()
        if self.error:
            raise RuntimeError("captured output failed: " + self.error)
        return {"bytes": self.total, "truncated": self.total > self.limit,
                "text": b"".join(self.chunks).decode("utf-8", "replace")}


def run(command, environment, timeout, max_output=4 * 1048576, cleanup_grace=2):
    start = time.monotonic()
    child = OwnedGroup(command, env=environment, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = stderr = None
    timed_out = False
    fault = None
    try:
        stdout = CapturedStream(child.process.stdout, max_output)
        stderr = CapturedStream(child.process.stderr, max_output)
        timed_out = not child.await_terminal(timeout)
    except BaseException as error:
        fault = error
    finally:
        settled, usage = child.finish(cancel_reason="capture wait interrupted" if fault else
                                      "native client deadline" if timed_out else None, grace=cleanup_grace)
        output = stdout.finish() if stdout else {"bytes": 0, "truncated": False, "text": ""}
        errors = stderr.finish() if stderr else {"bytes": 0, "truncated": False, "text": ""}
        if stdout is None:
            child.process.stdout.close()
        if stderr is None:
            child.process.stderr.close()
    outcome = {"command": command, "returncode": settled["returncode"],
            "wall_seconds": time.monotonic() - start, "timed_out": timed_out,
            "resources": receipt(usage), "client_cleanup": settled,
            "capture_bytes": {"stdout": output["bytes"], "stderr": errors["bytes"]},
            "capture_truncated": output["truncated"] or errors["truncated"],
            "stdout": output["text"], "stderr": errors["text"]}
    if fault:
        # Preserve the original exception identity while carrying actual
        # settlement/capture evidence to the owning invocation wrapper.
        try:
            fault.owned_process_outcome = outcome
        except BaseException:
            pass  # Never replace the first error just to enrich diagnostics.
        raise fault
    return outcome
