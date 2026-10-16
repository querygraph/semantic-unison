#!/usr/bin/env python3
"""Pure receiving proof checks; no CLI/helper/native invocation."""
import live_merge_cases as live

digest = 'a' * 64
target = {'sha256': digest, 'bytes': 123}
protocol = ('UNISON-DNG-VALIDATION 1\ncandidate-sha256 ' + digest + '\ncandidate-size 123\n'
            'driver-build fixture\nstructure valid\ndecode success\nraw-digest valid\nerrors 0\nwarnings 4\nEND\n')

def trace(endpoint, pid):
    prefix = '' if endpoint == 'client' else 'server: '
    return (f'[{prefix}validation-process] Helper result v0 pid={pid} status=exit:0 outcome=completed '
            f'candidate-sha256={digest} candidate-bytes=123 capture-truncated=false '
            f'stdout-truncated=false stderr-truncated=false stdout-hex={protocol.encode().hex()} stderr-hex=\n'
            f'[{prefix}validation-group] Retained group v0 pid={pid} candidate-sha256={digest} other-members=0\n')

log = trace('client', 42) + trace('server', 43)
proof = live.audit_merge(log, target, 'fixture')
assert [x['endpoint'] for x in proof] == ['client', 'server']
assert all(x['receipt']['errors'] == '0' and x['retained_group_other_members'] == 0 for x in proof)
live.no_helpers('ordinary output')
bad = [log.replace('other-members=0', 'other-members=unknown', 1),
       log.replace('other-members=0', 'other-members=unobserved', 1),
       log.replace('other-members=0', 'other-members=1', 1),
       log.replace('Retained group v0 pid=42', 'Retained group v0 pid=44'),
       log.replace('candidate-bytes=123', 'candidate-bytes=124', 1),
       log.replace('capture-truncated=false', 'capture-truncated=true', 1),
       log.replace('status=exit:0', 'status=exit:1', 1),
       trace('client', 42), log + trace('client', 42),
       log.replace(protocol.encode().hex(), protocol.replace('errors 0', 'errors 1').encode().hex(), 1),
       log.replace(protocol.encode().hex(), protocol.replace('raw-digest valid', 'raw-digest missing').encode().hex(), 1)]
for item in bad:
    try:
        live.audit_merge(item, target, 'fixture')
    except ValueError:
        pass
    else:
        raise AssertionError('accepted unqualified receiving evidence')
try:
    live.no_helpers(log)
except ValueError:
    pass
else:
    raise AssertionError('noop allowed helper calls')
print('PASS two-endpoint receiving proof,', len(bad), 'negative traces and unexpected-noop rejection; no native calls')
