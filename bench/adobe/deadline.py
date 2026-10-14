"""One native phase deadline; retain an unresolved-ownership marker on ambiguity."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sync'))
from measure import run


class NativeDeadline:
    def __init__(self, workspace, seconds=300, max_calls=None, contained=False):
        if seconds is not None and not 10 < seconds <= 300:
            raise ValueError('native slot must allow cleanup and be at most 300 seconds')
        self.end = time.monotonic() + seconds if seconds is not None else float("inf")
        self.marker = Path(workspace) / 'NATIVE-OWNERSHIP-UNRESOLVED.json'
        self.calls = []
        self.max_calls = max_calls
        self.contained = contained
        self.marker.write_text(json.dumps({'state': 'OWNED', 'seconds': seconds}))

    def remaining(self):
        # Stop new work and cancel existing work before the hard wall deadline.
        remaining = self.end - time.monotonic() - 8
        if remaining <= 0:
            raise TimeoutError('aggregate native slot expired; no new invocation')
        return remaining

    def invoke(self, command, *, timeout, capture_output=True, text=True,
               env=None, cwd=None, settlement=None):
        if not capture_output or not text or cwd is not None:
            raise ValueError('unsupported native capture configuration')
        if self.max_calls is not None and len(self.calls) >= self.max_calls:
            raise RuntimeError('SDK invocation cap reached')
        environment = dict(os.environ if env is None else env)
        if settlement:
            environment['UNISON_BENCH_SETTLEMENT'] = str(settlement)
        if self.contained:
            from phase import invoke_contained
            receipt = invoke_contained(command, environment, min(timeout, self.remaining()))
        else:
            receipt = run(command, environment, min(timeout, self.remaining()), cleanup_grace=4)
        self.calls.append(receipt)
        self.marker.write_text(json.dumps({'state': 'OWNED', 'calls': self.calls}, indent=2))
        if settlement:
            path = Path(settlement)
            if not path.is_file():
                raise RuntimeError('helper settlement absent; ownership remains unresolved')
            proof = json.loads(path.read_text())
            if proof != {'pid': receipt['client_cleanup']['pid'], 'final_children': 0,
                         'final_cpu_permits': 0, 'settled': True}:
                raise RuntimeError('helper settlement mismatch; ownership remains unresolved')
        if receipt['capture_truncated']:
            raise RuntimeError('native output exceeded capture bound')
        if receipt['timed_out']:
            raise TimeoutError('aggregate native call cancelled and leader reaped')
        return subprocess.CompletedProcess(command, receipt['returncode'],
                                           receipt['stdout'], receipt['stderr'])

    def close(self):
        # Called only after all invocations have passed settlement checks.
        if time.monotonic() > self.end:
            raise TimeoutError('native phase exceeded aggregate wall limit')
        self.marker.unlink()
        return {'closed': True, 'calls': self.calls,
                'remaining_seconds': None if self.end == float('inf') else self.end-time.monotonic()}
