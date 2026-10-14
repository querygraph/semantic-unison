#!/usr/bin/env python3
"""Original finite containment controls; no SDK initialization or Photo access."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'bench/adobe'))
from phase import supervise, invoke_contained
p = argparse.ArgumentParser()
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
work = Path(tempfile.mkdtemp(prefix='unison-phase-controls-',dir='/private/tmp'))
print('Workspace:',work,flush=True)
helper = work/'original.py'
helper.write_text('''import os,pathlib,signal,sys,time
pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))
if sys.argv[2]=='hang':
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 time.sleep(30)
else:print('original')
''')
cases=[]
for mode in ['pass','python-hang','native-hang','abrupt-worker','worker-error']:
    owned=work/mode;owned.mkdir()
    record=owned/'pid'
    def run():
        if mode=='python-hang':
            while True: pass
        if mode=='worker-error':
            raise ValueError('original worker failure')
        if mode=='abrupt-worker':
            subprocess.Popen([sys.executable,str(helper),str(record),'hang'])
            limit=time.monotonic()+1
            while not record.exists():
                if time.monotonic()>limit:raise RuntimeError('helper did not start')
                time.sleep(.005)
            os._exit(17)
        result=invoke_contained([sys.executable,str(helper),str(record),
                                 'hang' if mode=='native-hang' else 'pass'],os.environ.copy(),30)
        assert result['returncode']==0
    start=time.monotonic()
    try:
        closure=supervise(run,owned,seconds=6)
        assert mode=='pass'
    except RuntimeError:
        assert mode!='pass'
        closure=json.loads((owned/'AGGREGATE-CLOSED.json').read_text())
    assert closure['closed'] and closure['reaped'] and closure['other_members_absent']
    assert time.monotonic()-start<6
    assert not (owned/'AGGREGATE-OWNERSHIP-UNRESOLVED.json').exists()
    if record.exists():
        try:os.kill(int(record.read_text()),0)
        except ProcessLookupError:pass
        else:raise AssertionError('original helper survived group closure')
    cases.append(dict(case=mode,closure=closure))
    print('PASS',mode,flush=True)
# Parent cancellation is a separately owned subprocess, not a signal to the
# test driver/session. Its child and native helper still use the same protocol.
parent_work=work/'parent-cancel';parent_work.mkdir()
program=parent_work/'driver.py'
program.write_text('''import os,sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nfrom phase import supervise,invoke_contained\ntry:supervise(lambda:invoke_contained([sys.executable,sys.argv[3],sys.argv[4],'hang'],os.environ.copy(),30),Path(sys.argv[2]),seconds=6)\nexcept RuntimeError:sys.exit(1)\n''')
record=parent_work/'pid'
with (parent_work/'log').open('w') as log:
    child=subprocess.Popen([sys.executable,str(program),str(ROOT/'bench/adobe'),str(parent_work),str(helper),str(record)],stdout=log,stderr=log)
    limit=time.monotonic()+2
    while not record.exists():
        if time.monotonic()>limit:raise RuntimeError('parent cancellation readiness')
        time.sleep(.005)
    child.send_signal(signal.SIGTERM)
    assert child.wait(timeout=6)==1
closure=json.loads((parent_work/'AGGREGATE-CLOSED.json').read_text())
assert closure['closed'] and closure['other_members_absent']
cases.append(dict(case='parent-sigterm',closure=closure))
print('PASS parent-sigterm',flush=True)
a.report.write_text(json.dumps({'workspace':str(work),'cases':cases,'scope':'original synthetic process containment only; no SDK'},indent=2)+'\n')
