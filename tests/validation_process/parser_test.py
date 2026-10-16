#!/usr/bin/env python3
"""Finite pure parsing controls; launches no process or helper."""
from dataclasses import FrozenInstanceError
from pathlib import Path
import json
import hashlib
import tempfile
import sys

import records

header = ('[validation-process] Helper result v0 pid=42 status=exit:0 outcome=completed '
          'candidate-sha256=' + 'a' * 64 + ' candidate-bytes=123 capture-truncated=false '
          'stdout-truncated=false stderr-truncated=false stdout-hex=414200ff stderr-hex=')
r = records.parse('ordinary log\n' + header + '\n')[0]
assert r.endpoint == 'client' and r.pid == 42 and r.status == ('exit', 0)
assert r.stdout == b'AB\x00\xff' and r.stderr == b'' and r.complete_capture
assert records.parse(header.replace('[validation-process]', '[server: validation-process]'))[0].endpoint == 'server'
try:
    r.pid = 99
except FrozenInstanceError:
    pass
else:
    raise AssertionError('mutable diagnostic')
# Absence is an empty observation set, not a measured zero or validator verdict.
assert records.parse('ordinary Helper result v0 mention') == []
assert len(records.parse(header + '\n' + header)) == 2  # do not invent PID uniqueness/lifetime
nonzero = records.parse(header.replace('exit:0', 'exit:4'))[0]
assert nonzero.complete_capture and nonzero.status == ('exit', 4)
assert not records.parse(header.replace('capture-truncated=false', 'capture-truncated=true'))[0].complete_capture
clipped = records.parse(header.replace('stderr-truncated=false', 'stderr-truncated=true') + 'ff' * 4096)[0]
assert not clipped.complete_capture and clipped.stderr == b'\xff' * 4096
nochild = header.replace('pid=42 status=exit:0 outcome=completed', 'pid=none status=none outcome=failed')
assert records.parse(nochild)[0].pid is None
bad = [header.replace('v0', 'v1'), header.replace('pid=42', 'pid=0'),
       header.replace('pid=42', 'pid=2147483648'), header.replace('exit:0', 'exit:256'),
       header.replace('exit:0', 'exit:-1'), header.replace('exit:0', 'signal:-0'), header.replace('exit:0', 'signal:2147483648'),
       header.replace('pid=42', 'pid=none'), header.replace('status=exit:0', 'status=none'),
       header.replace('candidate-bytes=123', 'candidate-bytes=9223372036854775808'),
       header.replace('candidate-bytes=123', 'candidate-bytes=-1'),
       header.replace('candidate-bytes=123', 'candidate-bytes=0123'),
       header.replace('stdout-hex=414200ff', 'stdout-hex=abc'),
       header.replace('stdout-hex=414200ff', 'stdout-hex=FF'),
       header.replace('stderr-truncated=false', 'stderr-truncated=true'),
       header.replace('stdout-truncated=false', 'stdout-truncated=true'),
       '\n'.join([header] * 4097), header + '00' * 4097, header + ' extra-field',
       '[validation-process] ' + 'x' * 20001,
       'x' * (records.MAX_LOG_BYTES + 1), 'é' * (records.MAX_LOG_BYTES // 2 + 1)]
for malformed in bad:
    try:
        records.parse(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError('malformed record accepted')
# Independently decode retained actual stock/Ox fixture logs, never rerun them.
qualification = json.loads((Path(__file__).parent / 'qualification.json').read_text())
observed = []
for run in qualification['runs']:
    work = Path(run['workspace'])
    reference = run['cli_report']
    report_path = Path(reference['path'])
    assert report_path.stat().st_size == reference['bytes']
    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == reference['sha256']
    original = json.loads(report_path.read_text())
    expected = {item['pid']: item for item in original['observations']}
    parsed = []
    logs = []
    for log in sorted(work.glob('*/*.log')):
        parsed.extend(records.parse(log.read_text()))
        logs.append({'path': str(log), 'bytes': log.stat().st_size,
                     'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
    for item in parsed:
        baseline = expected[item.pid]
        assert item.stdout.decode('ascii') == baseline['stdout']
        assert item.stderr.hex() == baseline['stderr_hex']
        assert item.candidate_sha256 == baseline['candidate_sha256']
        assert item.stderr_truncated == baseline['stderr_truncated']
    assert len(parsed) == 3, (run['compiler_kind'], len(parsed))
    assert all(item.endpoint == 'server' and item.status == ('exit', 0) for item in parsed)
    assert sum(item.stderr_truncated for item in parsed) == 1
    assert sum(b'errors 1\n' in item.stdout for item in parsed) == 1
    assert any(item.stderr == bytes(range(256)) * 16 for item in parsed)
    observed.append({'compiler': run['compiler_kind'], 'actual_records': len(parsed),
                     'pinned_prior_report': reference, 'current_log_pins': logs})
work = Path(tempfile.mkdtemp(prefix='unison-validation-parser-'))
report = {'complete': True, 'python': sys.version, 'malformed_controls': len(bad), 'actual_retained_log_readback': observed,
          'scope': 'pure bounded parser and existing synthetic logs only; no subprocess, native or SDK call'}
(work / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS parser controls,', len(bad), 'malformed cases and six retained actual records; report', work / 'RESULT.json')
