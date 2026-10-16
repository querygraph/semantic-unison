#!/usr/bin/env python3
"""Full production CLI receiving with original fake validator; never Adobe."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import run_live_merge as runner

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
a = p.parse_args()
work = Path(tempfile.mkdtemp(prefix='unison-live-merge-mock-'))
print('Workspace:', work, flush=True)
tool = work / 'original-fake-validator.py'
tool.write_text('#!' + sys.executable + '\n' + '''import hashlib,pathlib,sys
args=sys.argv[1:]
assert len(args)==9 and args[0]=='--unison-dng-validation-v1'
assert args[1]=='--expected-sha256' and args[3]=='--expected-size'
assert args[5:8]==['--threads','1','--']
data=pathlib.Path(args[8]).read_bytes()
assert hashlib.sha256(data).hexdigest()==args[2] and len(data)==int(args[4])
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+args[2]);print('candidate-size '+args[4])
print('driver-build MOCK-live-merge-v1')
print('structure valid\\ndecode success\\nraw-digest valid\\nerrors 0\\nwarnings 0\\nEND')
''')
tool.chmod(0o700)
packet = json.loads(a.prepared.read_text())
packet['tool'] = {'executable':str(tool),'sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),
                  'build_id':'MOCK-live-merge-v1'}
prepared = work / 'MOCK-PREPARED.json'
prepared.write_text(json.dumps(packet,indent=2)+'\n')
runner.validate(packet, 'mock')
try:
    runner.validate(packet, 'native')
except (KeyError, ValueError):
    pass
else:
    raise AssertionError('mock tool eligible for native mode')
command = [sys.executable, str(Path(runner.__file__).resolve()), '--prepared', str(prepared),
           '--workspace', str(work / 'runtime'), '--mode', 'mock']
# The wrapper owns its aggregate and all nested process closure. This harness
# deliberately adds no timeout-kill that could abandon an owned helper group.
completed = subprocess.run(command, capture_output=True, text=True)
(work/'stdout.log').write_text(completed.stdout)
(work/'stderr.log').write_text(completed.stderr)
assert completed.returncode == 0, completed.stdout + completed.stderr
runtime = work / 'runtime'
result = json.loads((runtime/'RESULT.json').read_text())
closure = json.loads((runtime/'SUPERVISOR-CLOSED.json').read_text())
assert result['complete'] and result['mode']=='mock' and result['cli_runs']==9 and result['validation_calls']==6
assert closure['external_proofs_accepted'] and closure['aggregate']['reaped']
assert not list(runtime.glob('*UNRESOLVED*'))
(work/'RESULT.json').write_text(json.dumps({'complete':True,'wrapper_returncode':completed.returncode,
    'runtime':str(runtime),'result':result,'supervisor':closure,
    'scope':'production stock/Ox receiving with original fake SDK protocol, no Adobe/Photo'},indent=2)+'\n')
print('PASS nine CLI runs, six fake validations and independent aggregate/helper closure; report', work/'RESULT.json')
