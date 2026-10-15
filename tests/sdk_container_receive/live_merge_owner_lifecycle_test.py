#!/usr/bin/env python3
"""Finite original fake-child ownership checks; no SDK/Photo/native validator."""
import json
from pathlib import Path
import signal
import sys
import tempfile
import time

import live_merge_owner as owner

work = Path(tempfile.mkdtemp(prefix='unison-live-owner-lifecycle-'))
print('Workspace:', work, flush=True)
results = []


def run(name, source, *, timeout=False, capture_fault=False):
    directory = work / name
    directory.mkdir()
    # Shorten only the test's remaining aggregate budget. Production call
    # timeout remains80s; this fixture yields a roughly2s call wait on timeout.
    runner = owner.Runner(directory, time.monotonic() + (10.2 if timeout else 30))
    previous = owner.CapturedStream
    if capture_fault:
        def fail_capture(*_args, **_kwargs):
            raise OSError('original capture-setup fixture')
        owner.CapturedStream = fail_capture
    output, error = None, None
    try:
        output = runner.run_sync([sys.executable, '-c', source], {}, directory / 'output.log')
    except (RuntimeError, OSError) as exception:
        error = str(exception)
    finally:
        owner.CapturedStream = previous
    receipt = json.loads((directory / 'CLI-01-CLOSED.json').read_text())
    assert receipt['reaped'] and receipt['other_cli_group_members_absent_before_reap']
    assert runner.active_owner is None
    try:
        owner.os.waitpid(receipt['pid'], owner.os.WNOHANG)
    except ChildProcessError:
        pass
    else:
        raise AssertionError('actual direct child not reaped')
    assert runner.marker.exists()  # one CLI cannot supply all six helper proofs
    results.append({'name': name, 'receipt': receipt, 'error': error,
                    'capture_truncated': output['capture_truncated'] if output else None,
                    'scope': 'retained marker is intentional missing matrix evidence, not a live test child'})
    print('PASS', name, flush=True)
    return output, error, receipt

out, err, receipt = run('normal', 'print("original normal child")')
assert out['returncode'] == 0 and not err and 'original normal child' in out['log']
out, err, receipt = run('nonzero', 'raise SystemExit(7)')
assert out['returncode'] == 7 and not err
out, err, receipt = run('bounded-output', 'import sys;sys.stdout.write("x"*(5*1024*1024))')
assert out['capture_truncated'] and len(out['log']) == 4 * 1024 * 1024
out, err, receipt = run('term-ignoring-timeout',
    'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)', timeout=True)
assert err and receipt['timed_out'] and receipt['returncode'] == -signal.SIGKILL
out, err, receipt = run('same-group-descendant',
    'import os,time;pid=os.fork();time.sleep(30) if pid==0 else None')
assert out['returncode'] == 0 and not err
out, err, receipt = run('capture-setup-failure', 'import time;time.sleep(30)', capture_fault=True)
assert err == 'original capture-setup fixture' and receipt['fault'] is not None
(work / 'RESULT.json').write_text(json.dumps({'complete': True, 'cases': results,
    'scope': 'six finite original fake-child cases, actual direct reap and own-group absence only; no SDK/Photo, aggregate controller or helper-proof release qualification'}, indent=2) + '\n')
print('PASS six real fake-child lifecycle cases; report', work / 'RESULT.json', flush=True)
