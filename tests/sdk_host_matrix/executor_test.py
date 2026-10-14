#!/usr/bin/env python3
"""Original deterministic fake validators only; no SDK or Photo work."""
import json
import pathlib
import subprocess
import sys
import tempfile

import plan

work = pathlib.Path(tempfile.mkdtemp(prefix='unison-host-matrix-mock-', dir='/private/tmp'))
records = []
for scenario in ('pass', 'different-warning', 'bad-digest', 'noncanonical-command'):
    case = work / scenario
    case.mkdir()
    tools = []
    for kind in ('reference', 'experimental'):
        tool = case / (kind + '.py')
        build = 'MOCK-' + kind
        tool.write_text('''#!/usr/bin/python3
import sys
a=sys.argv[1:]
warning='4'
raw='valid'
if SCENARIO == 'different-warning' and '--host-memory-bytes' in a: warning='5'
if SCENARIO == 'bad-digest' and '--host-memory-bytes' in a: raw='mismatch'
print('UNISON-DNG-VALIDATION 1\\ncandidate-sha256 '+a[2]+'\\ncandidate-size '+a[4]+'\\ndriver-build '+BUILD+'\\nstructure valid\\ndecode success\\nraw-digest '+raw+'\\nerrors 0\\nwarnings '+warning+'\\nEND')
'''.replace('SCENARIO', repr(scenario)).replace('BUILD', repr(build)))
        tool.chmod(0o700)
        tools.append({'executable': str(tool), 'sha256': plan.sha(tool), 'build_id': build})
    fixtures = []
    for codec in plan.CODECS:
        path = case / (codec + '.original-synthetic')
        path.write_bytes(('original test data ' + codec).encode())
        fixtures.append({'codec': codec, 'path': str(path), 'size': path.stat().st_size,
                         'sha256': plan.sha(path)})
    packet = {'schema': 'unison-sdk-host-matrix-plan/1', 'limits': plan.LIMITS,
              'source_pins': {name: plan.sha(plan.ROOT / name) for name in plan.SOURCES},
              'tools': tools, 'host_memory_bytes': 1048576,
              'cases': plan.matrix(*tools, fixtures, 1048576)}
    if scenario == 'noncanonical-command':
        packet['cases'][1]['command'][7] = '128'
    input_path = case / 'PLAN.json'
    input_path.write_text(json.dumps(packet))
    run = case / 'run'
    command = [sys.executable, str(plan.ROOT / 'tests/sdk_host_matrix/run.py'),
               '--plan', str(input_path), '--workspace', str(run), '--mode', 'mock']
    result = subprocess.run(command, capture_output=True, text=True)
    (case / 'stdout.txt').write_text(result.stdout)
    (case / 'stderr.txt').write_text(result.stderr)
    plan.require((result.returncode == 0) == (scenario == 'pass'), 'unexpected wrapper exit')
    if scenario == 'noncanonical-command':
        plan.require(not run.exists(), 'invalid commands acquired workspace')
    else:
        closure = json.loads((run / 'AGGREGATE-CLOSED.json').read_text())
        plan.require(closure['closed'] and closure['reaped'] and closure['other_members_absent']
                     and not (run / 'AGGREGATE-OWNERSHIP-UNRESOLVED.json').exists(), 'not closed')
        count = len(list(run.glob('CALL-*.json')))
        plan.require(count == (12 if scenario == 'pass' else 2), 'wrong actual calls')
        plan.require((run / 'RESULT.json').exists() == (scenario == 'pass'), 'false success receipt')
    if scenario == 'pass':
        # The exact workspace is consumed even after a genuine successful close.
        replay = subprocess.run(command, capture_output=True, text=True)
        plan.require(replay.returncode != 0 and len(list(run.glob('CALL-*.json'))) == 12,
                     'workspace replay accepted')
    records.append({'scenario': scenario, 'exit': result.returncode, 'passed': True})
    print(scenario + ' passed', flush=True)
output = {'scope': 'original fake Python tools; no SDK/native backend invoked',
          'cases': records, 'source_sha256': plan.sha(__file__),
          'executor_sha256': plan.sha(plan.ROOT / 'tests/sdk_host_matrix/run.py'),
          'workspace': str(work)}
(work / 'RESULT.json').write_text(json.dumps(output, indent=2) + '\n')
print(work / 'RESULT.json')
