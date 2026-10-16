#!/usr/bin/python3
"""Owned synthetic validator; gate files are confined to the retained case."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

control = Path(sys.argv[1]).resolve()
action = sys.argv[2]
arguments = sys.argv[3:]
assert arguments[:1] == ['--unison-dng-validation-v1'], arguments
assert arguments[1] == '--expected-sha256' and arguments[3] == '--expected-size'
assert arguments[5:8] == ['--threads', '1', '--'], arguments
candidate = Path(arguments[8]).resolve()
assert control.parent == candidate.parent
signal.signal(signal.SIGTERM, signal.SIG_IGN)
pid = os.getpid()
owner = os.getppid()
deadline = time.monotonic() + 15
record = {'pid': pid, 'candidate': str(candidate), 'action': action,
          'sha256': hashlib.sha256(candidate.read_bytes()).hexdigest()}
control.with_suffix('.ready.json').write_text(json.dumps(record) + '\n')
while not control.exists():
    # Bound a failed test's child lifetime even if the owner is externally
    # terminated before its production cleanup can run. This is fixture-only.
    if os.getppid() != owner or time.monotonic() >= deadline:
        raise SystemExit(91)
    time.sleep(.005)
if action == 'candidate-mutation':
    candidate.write_bytes(candidate.read_bytes() + b' LATE SYNTHETIC MUTATION')
elif action == 'tool-mutation':
    executable = Path(__file__)
    executable.write_bytes(executable.read_bytes() + b'\n# LATE SYNTHETIC MUTATION\n')
elif action not in ('pass', 'malformed'):
    raise AssertionError(action)
control.with_suffix('.released.json').write_text(json.dumps({'pid': pid, 'action': action}) + '\n')
if action == 'malformed':
    print('synthetic malformed receipt')
else:
    print('UNISON-DNG-VALIDATION 1')
    print('candidate-sha256 ' + arguments[2])
    print('candidate-size ' + arguments[4])
    print('driver-build validation-settlement-synthetic-1')
    print('structure valid')
    print('decode success')
    print('raw-digest missing')
    print('errors 0')
    print('warnings 0')
    print('END')
