#!/usr/bin/python3
"""Synthetic actual-CLI receiving validator with an owned external gate."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

here = Path(__file__)
control = json.loads(here.with_suffix('.control.json').read_text())
args = sys.argv[1:]
assert len(args) == 9 and args[0] == '--unison-dng-validation-v1', args
assert args[1] == '--expected-sha256' and args[3] == '--expected-size'
assert args[5:8] == ['--threads', '1', '--']
candidate = Path(args[8])
data = candidate.read_bytes()
assert hashlib.sha256(data).hexdigest() == args[2] and len(data) == int(args[4])
owned = Path(control['owned'])
assert owned == here.parent and candidate.is_absolute()
assert candidate.is_relative_to(owned.parent / 'right'), candidate
pid, parent = os.getpid(), os.getppid()
signal.signal(signal.SIGTERM, signal.SIG_IGN)
record = {'pid': pid, 'candidate': str(candidate), 'sha256': args[2],
          'size': len(data), 'action': control['action']}
(owned / (str(pid) + '.call.json')).write_text(json.dumps(record) + '\n')
pending = owned / (str(pid) + '.pending')
pending.write_text(str(candidate) + '\n')
pending.rename(owned / (str(pid) + '.ready'))
gate = owned / 'release.control'
deadline = time.monotonic() + 20
while not gate.exists():
    if os.getppid() != parent or time.monotonic() >= deadline:
        raise SystemExit(91)
    time.sleep(.005)
if control['action'] == 'candidate-mutation':
    candidate.write_bytes(data + b' LATE SYNTHETIC MUTATION')
elif control['action'] == 'tool-mutation':
    here.write_bytes(here.read_bytes() + b'\n# LATE SYNTHETIC MUTATION\n')
elif control['action'] != 'pass':
    raise AssertionError(control['action'])
(owned / (str(pid) + '.released')).write_text('released\n')
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 ' + args[2])
print('candidate-size ' + args[4])
print('driver-build validation-settlement-synthetic-1')
print('structure valid')
print('decode success')
print('raw-digest missing')
print('errors 0')
print('warnings 0')
print('END')
