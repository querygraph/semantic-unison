#!/usr/bin/env python3
"""Synthetic receiving diagnostics; original fake validators, no Adobe calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import sys

import records

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt', type=Path, required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
build = json.loads(a.build_receipt.read_text())
assert build['complete'] and build['build_exit'] == build['selftest_exit'] == 0
assert sha(build['binary']) == build['binary_sha256']
for name, digest in build['source_sha256'].items():
    if name.startswith('src/'):
        assert sha(root / name) == digest, name
spec = importlib.util.spec_from_file_location('paths', root / 'tests/validation_paths/run.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
v.ADMISSION_OPTIONS[:] = ['-semanticvolumejobs', '1']
work = Path(tempfile.mkdtemp(prefix='unison-validation-process-')).resolve()
print('Workspace:', work, flush=True)
pattern = re.compile(r'^\[server: validation-process\] Helper result v0 pid=([0-9]+) status=exit:0 outcome=completed candidate-sha256=([0-9a-f]{64}) candidate-bytes=([0-9]+) capture-truncated=false stdout-truncated=false stderr-truncated=(true|false) stdout-hex=([0-9a-f]*) stderr-hex=([0-9a-f]*)$')
def reports(log):
    return [line for line in log.splitlines() if 'Helper result v0 ' in line]
def observed(log, session, expected, truncated=False):
    lines = reports(log)
    assert len(lines) == 1, lines
    match = pattern.fullmatch(lines[0])
    assert match, lines[0]
    pid, digest, size, clipped, stdout, stderr = match.groups()
    assert int(pid) == session.calls('server')[-1]['pid']
    assert digest == hashlib.sha256(expected).hexdigest() and int(size) == len(expected)
    assert clipped == ('true' if truncated else 'false')
    raw = bytes.fromhex(stdout)
    assert len(raw) <= 4096 and len(bytes.fromhex(stderr)) <= 4096
    assert raw.startswith(b'UNISON-DNG-VALIDATION 1\n') and raw.endswith(b'END\n')
    groups = records.parse_groups(log)
    assert len(groups) == 1, groups
    group = groups[0]
    assert group.endpoint == 'server' and group.pid == int(pid)
    assert group.candidate_sha256 == digest
    if sys.platform == 'darwin':
        assert group.observation == 'observed' and group.other_members == 0, group
    else:
        assert group.observation == 'unknown' and group.other_members is None, group
    return {'group_observation': group.observation, 'group_other_members': group.other_members,
            'pid': int(pid), 'candidate_sha256': digest, 'stdout': raw.decode('ascii'),
            'stderr_hex': stderr, 'stderr_truncated': truncated}

original = b'original synthetic filename-claimed DNG bytes'
plain = v.Session(work / 'default', build['binary'])
(plain.left / 'image.dng').write_bytes(original)
plain_log = plain.sync()
assert not reports(plain_log) and not records.parse_groups(plain_log)
assert (plain.right / 'image.dng').read_bytes() == original

s = v.Session(work / 'observed', build['binary'])
(s.left / 'image.dng').write_bytes(original)
options = ('-debug', 'validation-process', '-debug', 'validation-group')
passed = observed(s.sync(options=options), s, original)
assert 'errors 0\n' in passed['stdout']
assert (s.right / 'image.dng').read_bytes() == original
before = len(s.calls('server'))
noop_log = s.sync(options=options)
assert not reports(noop_log) and not records.parse_groups(noop_log)
assert len(s.calls('server')) == before
changed = original + b' rejected change'
(s.left / 'image.dng').write_bytes(changed)
s.control('image.dng', server='error')
rejected = observed(s.sync(options=options, success=False), s, changed)
assert 'errors 1\n' in rejected['stdout']
assert (s.right / 'image.dng').read_bytes() == original

clipped = v.Session(work / 'clipped', build['binary'])
# Exercise arbitrary bytes and diagnostic clipping, independently of the much
# larger supervised stderr allowance. This is an original Python fake helper.
for driver in clipped.drivers.values():
    driver.write_text(v.DRIVER + '\nimport sys\nsys.stderr.buffer.write(bytes(range(256))*20)\n')
# Session freezes server-local endpoint settings at construction. Refresh that
# private profile after editing its fake executable, before starting any peer.
settings = clipped.config('server')
settings['semanticvolumejobs'] = '1'
(clipped.server_state / 'endpoint.prf').write_text(
    ''.join(f'{key} = {value}\n' for key, value in settings.items()))
(clipped.left / 'image.dng').write_bytes(original)
clipped_result = observed(clipped.sync(options=options), clipped, original, True)
assert bytes.fromhex(clipped_result['stderr_hex']) == bytes(range(256)) * 16
assert (clipped.right / 'image.dng').read_bytes() == original
report = {'complete': True, 'workspace': str(work), 'binary_sha256': build['binary_sha256'],
          'build_receipt_sha256': sha(a.build_receipt), 'runner_sha256': sha(__file__), 'parser_sha256': sha(root / 'tests/validation_process/records.py'),
          'cases': ['default-off', 'actual-pid-raw-receipt-and-retained-group', 'noop-no-report',
                    'exit-zero-finding-still-rejects', 'bounded-arbitrary-stderr'],
          'observations': [passed, rejected, clipped_result],
          'scope': 'production CLI with original fake validators; no SDK/Photo; diagnostic status is not validation/publication authority or surviving PID/group ownership'}
a.report.write_text(json.dumps(report, indent=2) + '\n')
print('PASS five receiving diagnostic controls; no Adobe calls', flush=True)
