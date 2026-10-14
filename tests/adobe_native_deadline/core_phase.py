#!/usr/bin/env python3
"""Actual contained validation core inside the aggregate owner; fake helpers only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'bench/adobe'))
from phase import supervise,invoke_contained
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--target',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
work=Path(tempfile.mkdtemp(prefix='unison-core-phase-',dir='/private/tmp'))
print('Workspace:',work,flush=True)
candidate=work/'original.bin';candidate.write_bytes(b'original synthetic core lifetime input\n'*4096)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
helper=work/'helper.py'
helper.write_text('''#!/usr/bin/python3
import json,os,pathlib,signal,sys,time
here=pathlib.Path(__file__);mode=here.with_suffix('.mode').read_text()
with here.with_suffix('.calls').open('a') as log:log.write(json.dumps({'pid':os.getpid(),'group':os.getpgrp()})+'\\n')
if mode!='pass':
 signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)
a=sys.argv[1:]
print('UNISON-DNG-VALIDATION 1');print('candidate-sha256 '+a[2]);print('candidate-size '+a[4]);print('driver-build original-core-phase')
print('structure valid');print('decode success');print('raw-digest valid');print('errors 0');print('warnings 0');print('END')
''')
helper.chmod(0o700)
cases=[]
for mode in ['pass','aggregate-expiry','abrupt-python']:
    owned=work/mode;owned.mkdir()
    helper.with_suffix('.mode').write_text(mode)
    helper.with_suffix('.calls').unlink(missing_ok=True)
    command=[str(a.target.resolve()),str(candidate),sha(candidate),str(candidate.stat().st_size),str(helper),sha(helper),'original-core-phase','2','2','30']
    proof=owned/'core-settled.json'
    def run():
        environment=dict(os.environ,UNISON_BENCH_SETTLEMENT=str(proof))
        if mode=='abrupt-python':
            subprocess.Popen(command,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            limit=time.monotonic()+2
            while not helper.with_suffix('.calls').exists() or len(helper.with_suffix('.calls').read_text().splitlines())<2:
                if time.monotonic()>limit:raise RuntimeError('core helper entry failed')
                time.sleep(.005)
            os._exit(19)
        receipt=invoke_contained(command,environment,30)
        (owned/'core-log').write_text(receipt['stdout']+'\n'+receipt['stderr'])
        assert receipt['returncode']==0
    try:
        closure=supervise(run,owned,seconds=8)
        assert mode=='pass'
    except RuntimeError:
        assert mode!='pass'
        closure=json.loads((owned/'AGGREGATE-CLOSED.json').read_text())
    assert closure['closed'] and closure['reaped'] and closure['within_wall_limit'] and closure['other_members_absent']
    calls=[json.loads(row) for row in helper.with_suffix('.calls').read_text().splitlines()]
    assert len(calls)==2 and all(row['group']==closure['pid'] for row in calls)
    for call in calls:
        try:os.kill(call['pid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError('helper survived aggregate closure')
    cases.append({'mode':mode,'closure':closure,'helpers':calls,'core_settlement_present':proof.exists()})
    print('PASS',mode,flush=True)
a.report.write_text(json.dumps({'scope':'actual checked core with original fake helpers only; no SDK','workspace':str(work),'target_sha256':sha(a.target),'cases':cases},indent=2)+'\n')
