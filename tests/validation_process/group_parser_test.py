#!/usr/bin/env python3
"""Finite pure fixtures, not a native process-group qualification."""
from dataclasses import FrozenInstanceError
import records

line = ('[validation-group] Retained group v0 pid=42 candidate-sha256='
        + 'a' * 64 + ' other-members=0')
r = records.parse_groups(line)[0]
assert (r.endpoint, r.pid, r.observation, r.other_members) == ('client', 42, 'observed', 0)
assert records.parse_groups(line.replace('validation-group', 'server: validation-group'))[0].endpoint == 'server'
assert records.parse_groups(line.replace('members=0', 'members=64'))[0].other_members == 64
for state in ('unknown', 'unobserved'):
    r = records.parse_groups(line.replace('members=0', 'members=' + state))[0]
    assert r.observation == state and r.other_members is None
assert records.parse_groups(line.replace('pid=42', 'pid=none').replace('members=0', 'members=unobserved'))[0].pid is None
assert records.parse_groups('ordinary log') == []
assert len(records.parse_groups(line + '\n' + line)) == 2
try:
    r.other_members = 0
except FrozenInstanceError:
    pass
else:
    raise AssertionError('mutable group record')
bad = [line.replace('v0', 'v1'), line.replace('pid=42', 'pid=0'),
       line.replace('pid=42', 'pid=2147483648'), line.replace('pid=42', 'pid=none'),
       line.replace('members=0', 'members=65'), line.replace('members=0', 'members=-1'),
       line.replace('members=0', 'members=00'), line.replace('members=0', 'members=absent'),
       line.replace('a' * 64, 'A' * 64), line + ' extra',
       '\n'.join([line] * 4097), 'x' * (records.MAX_LOG_BYTES + 1),
       'é' * (records.MAX_LOG_BYTES // 2 + 1),
       '[validation-group] ' + 'x' * (records.MAX_LINE + 1)]
for value in bad:
    try:
        records.parse_groups(value)
    except ValueError:
        pass
    else:
        raise AssertionError('accepted malformed group fixture')
print('PASS immutable group parser, state distinction, duplicates and', len(bad), 'malformed fixtures; no native calls')
