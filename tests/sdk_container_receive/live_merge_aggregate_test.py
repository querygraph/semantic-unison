#!/usr/bin/env python3
"""Finite fake workers, no native validator/Photo/CLI or compiler."""
import json
from pathlib import Path
import signal
import tempfile
import time
import os
import live_merge_aggregate as aggregate

work = Path(tempfile.mkdtemp(prefix='unison-live-aggregate-fixtures-'))
print('Workspace:', work, flush=True)
results = []

def normal(_deadline):
    return

def failure(_deadline):
    raise ValueError('original aggregate worker failure fixture')

def stuck(_deadline):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(30)

for name, function, expect_helpers, success in (
        ('normal', normal, 0, True), ('worker-failure', failure, 0, False),
        ('missing-helper-proof', normal, 6, False), ('term-ignoring-timeout', stuck, 0, False)):
    path = work / name
    path.mkdir()
    error = None
    try:
        aggregate.supervise(function, path, seconds=12, expected_helper_calls=expect_helpers)
    except (RuntimeError, FileNotFoundError) as exception:
        error = str(exception)
    assert (error is None) == success, (name, error)
    receipt = json.loads((path / 'AGGREGATE-CLOSED.json').read_text())
    assert receipt['reaped'] and receipt['other_cli_group_members_absent_before_reap']
    assert receipt['within_wall_limit'] and not (path / 'AGGREGATE-OWNERSHIP-UNRESOLVED.json').exists()
    assert (path / 'EXTERNAL-HELPERS-UNRESOLVED.json').exists() != success
    assert (path / 'SUPERVISOR-CLOSED.json').exists() == success
    try:
        os.waitpid(receipt['pid'], os.WNOHANG)
    except ChildProcessError:
        pass
    else:
        raise AssertionError('aggregate worker not reaped')
    results.append({'case': name, 'error': error, 'receipt': receipt,
                    'external_marker_retained': not success})
    print('PASS', name, flush=True)
(work / 'RESULT.json').write_text(json.dumps({'complete': True, 'cases': results,
    'scope': 'four original fake-worker aggregate lifecycle cases only; no SDK/Photo/CLI. Intentional external markers represent missing proof, not live children.'},indent=2)+'\n')
print('PASS four aggregate fixtures; report', work / 'RESULT.json', flush=True)
