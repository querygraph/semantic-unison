#!/usr/bin/env python3
"""Pure admission boundary controls; no child process or SDK invocation."""
import copy
import json
import pathlib
import tempfile
import time
import plan
from run import admission_check

work = pathlib.Path(tempfile.mkdtemp(prefix='unison-host-admission-', dir='/private/tmp'))
path = work / 'PLAN.json'
path.write_text('original plan binding\n')
command = ['/unused/python', '/unused/executor', '--plan', str(path)]
original = {'state': 'ROOT_ADMITTED_FINITE_UNISON_HOST_MATRIX_V1',
            'plan': {'path': str(path.resolve()), 'sha256': plan.sha(path)},
            'command': command, 'limits': plan.LIMITS, 'startDeadlineUnix': time.time() + 60}
admission_check(original, path, command)
mutations = [('state', 'ROOT_ADMITTED_FINITE_UNISON_RECEIVE_PILOT_V1'),
             ('startDeadlineUnix', 0), ('command', command + ['--retry']),
             ('limits', dict(plan.LIMITS, CPU_credits=36)),
             ('plan', dict(original['plan'], sha256='0' * 64))]
for key, value in mutations:
    changed = copy.deepcopy(original)
    changed[key] = value
    try:
        admission_check(changed, path, command)
    except ValueError:
        continue
    raise RuntimeError('invalid admission accepted: ' + key)
result = {'scope': 'pure admission checks; no native calls or subprocesses',
          'positive': 1, 'denials': len(mutations), 'source_sha256': plan.sha(__file__)}
(work / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
print(work / 'RESULT.json')
