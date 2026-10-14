#!/usr/bin/env python3
"""Actual DNG companion admission with synthetic protocol helpers; no Adobe."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', required=True, type=Path)
p.add_argument('--report', required=True, type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('paths', root/'tests/validation_paths/run.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
work = Path(tempfile.mkdtemp(prefix='unison-dng-resources-', dir='/private/tmp'))
print('Workspace:', work, flush=True)
cases = []
for name, memory, lanes, success, policy in [
    ('fits', 4, 1, True, 'require'),
    ('memory-too-large', 64, 1, False, 'require'),
    ('memory-too-large-warn', 64, 1, False, 'warn'),
    ('cpu-too-large', 4, 3, False, 'require'),
    ('negative-workspace', -1, 1, False, 'require'),
    ('zero-cpu', 4, 0, False, 'require'),
    ('off-ignores-inactive-estimate', 64, 3, True, 'off'),
    ('nested-directory', 4, 2, True, 'require')]:
    s = v.Session(work/name, str(a.binary.resolve()))
    directory = name == 'nested-directory'
    driver = s.drivers['server']
    if directory:
        driver.write_text(driver.read_text().replace("assert args[5:8]==['--threads','1','--'],args",
                                                    "assert args[5:8]==['--threads','2','--'],args"))
    cfg = dict(s.config('server'), adobevalidatorworkspace=str(memory), adobevalidatorthreads=str(lanes),
               validationtreememory='1' if directory else '0')
    (s.server_state/'endpoint.prf').write_text(''.join(f'{key} = {value}\n' for key, value in cfg.items()))
    parent = s.left/'album' if directory else s.left
    if directory:
        parent.mkdir()
    expected = {}
    for index in range(6 if directory else 1):
        name_at = f'item-{index}.dng' if directory else 'image.dng'
        data = b'Original synthetic claimed-DNG resource fixture ' + bytes([index])
        (parent/name_at).write_bytes(data)
        expected[name_at] = data
    if directory:
        driver.with_suffix('.control.json').write_text(json.dumps(dict(endpoint='server', build=cfg['adobevalidatorbuild'],
            mode='delay', destination=str(s.right/'album'), directory=True)))
    log = s.sync(policy=policy, options=('-semanticdng=false', '-semanticpayloadbudget', '8',
        '-semanticdescriptorbudget', '64', '-semanticmaxinflight', '1', '-adobevalidatorworkspace', '0'), success=success)
    assert {path.name: path.read_bytes() for path in parent.iterdir()} == expected
    calls = s.calls()
    destination = s.right/'album' if directory else s.right
    if success:
        assert {path.name: path.read_bytes() for path in destination.iterdir()} == expected
        assert len(calls) == (0 if policy == 'off' else len(expected))
    else:
        assert not calls and not list(s.right.iterdir()), 'rejected plan created/published staging or invoked helper'
        diagnostic = {'memory-too-large': 'resource budget', 'memory-too-large-warn': 'resource budget', 'cpu-too-large': 'CPU declaration',
                      'negative-workspace': 'adobevalidatorworkspace', 'zero-cpu': 'adobevalidatorthreads'}[name]
        assert diagnostic in log, log
    peak = None
    if directory:
        active = set()
        peak = 0
        for line in driver.with_suffix('.events').read_text().splitlines():
            kind, pid = line.split()
            if kind == 'start':
                active.add(pid)
                peak = max(peak, len(active))
            else:
                active.remove(pid)
        assert not active and peak == 1
    cases.append({'name': name, 'passed': True, 'helper_calls': len(calls), 'peak_helpers': peak,
                  'source_unchanged': True, 'destination_published': success})
    print('PASS', name, flush=True)
receipt = {'scope': 'Actual loopback DNG companion CPU/workspace admission; synthetic Python receipts, no SDK execution or threading proof',
           'workspace': str(work), 'binary_sha256': hashlib.sha256(a.binary.read_bytes()).hexdigest(),
           'cases': cases, 'sources': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [root/'src/dngCandidateValidation.ml', root/'src/dngCandidateValidation.mli',
                           root/'src/candidateValidators.ml', Path(__file__)]}}
a.report.write_text(json.dumps(receipt, indent=2)+'\n')
