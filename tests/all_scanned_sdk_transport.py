"""One-use all-scanned transport; caller owns admission, journal and grants.

Construction is pure. Calling requires an already admitted exact plan, owned
EXglobal/CPU descriptors and a coordinator that retains unknown child outcomes.
"""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'bench/sync'))
sys.path.insert(0, str(ROOT / 'tests/camera_sdk_concurrency'))
from all_scanned_sdk_plan import plan
from camera_sdk_concurrency.invocation import artifact_sha, SCRIPT_NAMES
from run import measure_invocation, InvocationFailure


class Invoker:
    def __init__(self, directory, *, binary, tool, phase, journal, script_pins, deadline):
        contract = plan(binary, tool, directory)
        if phase not in ('baseline', 'validate'):
            raise ValueError('exact baseline or validate phase required')
        if (set(script_pins) != set(SCRIPT_NAMES)
                or any(type(v) is not str or len(v) != 64
                       or any(c not in '0123456789abcdef' for c in v)
                       for v in script_pins.values())):
            raise ValueError('all four transport script SHA pins required')
        if type(deadline) not in (int, float) or not 0 < deadline < float('inf'):
            raise ValueError('finite monotonic observation deadline required')
        self.directory = Path(directory)
        self.binary, self.tool = dict(binary), dict(tool)
        self.phase, self.journal = phase, journal
        self.pins, self.deadline = dict(script_pins), deadline
        self.contract, self.used = contract, False

    def __call__(self):
        if self.used:
            raise ValueError('one phase only; never retry')
        self.used = True
        if time.monotonic() + 255 >= self.deadline:
            raise ValueError('insufficient phase observation headroom')
        for item in (self.binary, self.tool):
            if artifact_sha(item['path']) != item['sha256']:
                raise ValueError('execution artifact changed')
        for name, digest in self.pins.items():
            if artifact_sha(self.directory / name) != digest:
                raise ValueError('transport source changed')
        call = self.contract[self.phase]
        env = dict(os.environ)
        env.pop('UNISON_CONCURRENT_SYNTHETIC_ROOT', None)
        env.update(UNISON=str(self.directory / 'state'),
                   UNISON_SYNC_BENCH_BINARY=self.binary['path'],
                   UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(call['server_flags']),
                   UNISON_SYNC_BENCH_PROXY_RECEIPT=str(self.directory / (self.phase + '-proxy.json')),
                   UNISON_SYNC_BENCH_SOCKET=str(self.directory / 'scan.sock'),
                   UNISON_SYNC_BENCH_DEADLINE_SECONDS='245')
        self.journal.begin(dict(label=self.binary['label'], mode='validation', workers=3,
                                directory=str(self.directory), stage=self.phase), call['argv'])
        try:
            outcome = measure_invocation(call['argv'], env, 240,
                                         self.directory / 'proxy.py', strict_group_settlement=True)
        except InvocationFailure as error:
            self.journal.finish(error.outcome)
            raise
        self.journal.finish(outcome)
        return outcome
