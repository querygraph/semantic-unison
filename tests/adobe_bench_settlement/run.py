#!/usr/bin/env python3
"""Benchmark helper settlement on owned synthetic receipts, without Adobe."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--target', required=True, type=Path)
p.add_argument('--report', required=True, type=Path)
a = p.parse_args()
work = Path(tempfile.mkdtemp(prefix='unison-bench-settlement-', dir='/private/tmp'))
print('Workspace:', work, flush=True)
candidate = work/'original.bin'
candidate.write_bytes(b'Original non-photographic helper-settlement input\n'*4096)
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
helper = work/'helper.py'
helper.write_text('''#!/usr/bin/python3
import fcntl,json,os,pathlib,signal,sys,time
here=pathlib.Path(__file__)
control=json.loads(here.with_suffix('.control').read_text())
calls=here.with_suffix('.calls')
with calls.open('a+') as out:
 fcntl.flock(out,fcntl.LOCK_EX);out.seek(0);index=len(out.readlines())
 out.write(str(os.getpid())+'\\n');out.flush()
args=sys.argv[1:]
assert args[0]=='--unison-dng-validation-v1'
if control=='hang' or (control=='reject-peer' and index!=0):
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 time.sleep(8) # bounded independent backstop; core should KILL after grace
elif control=='reject-peer':
 deadline=time.monotonic()+2
 while len(calls.read_text().splitlines())<2 and time.monotonic()<deadline:time.sleep(.01)
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+args[2]);print('candidate-size '+args[4])
print('driver-build synthetic-bench-v1');print('structure valid');print('decode success')
bad=control=='reject-peer' and index==0
print('raw-digest '+('mismatch' if bad else 'valid'))
print('errors '+('1' if bad else '0'));print('warnings 0');print('END')
''')
helper.chmod(0o700)
cases = []
for mode, signalled, expected_success in [('pass', False, True), ('reject-peer', False, False),
                                         ('hang', False, False), ('hang', True, False), ('pass', False, True)]:
    name = f'{len(cases)}-{mode}'+('-signal' if signalled else '')
    helper.with_suffix('.control').write_text(json.dumps(mode))
    helper.with_suffix('.calls').unlink(missing_ok=True)
    command = [str(a.target.resolve()), str(candidate), digest(candidate), str(candidate.stat().st_size),
               str(helper), digest(helper), 'synthetic-bench-v1', '2', '2', '0.3' if mode=='hang' and not signalled else '10']
    start = time.monotonic()
    settlement = work/(name+".settled.json")
    environment = dict(os.environ, UNISON_BENCH_SETTLEMENT=str(settlement))
    child = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if signalled:
        deadline = time.monotonic()+5
        while (not helper.with_suffix('.calls').exists() or
               len(helper.with_suffix('.calls').read_text().splitlines())<2):
            if time.monotonic()>deadline:
                raise RuntimeError('synthetic helper entry deadline')
            time.sleep(.01)
        child.send_signal(signal.SIGTERM)
    stdout, stderr = child.communicate(timeout=20)
    (work/(name+'.log')).write_bytes(stdout+b'\n'+stderr)
    assert (child.returncode==0)==expected_success, stderr.decode(errors='replace')
    elapsed = time.monotonic()-start
    assert json.loads(settlement.read_text()) == {"pid": child.pid, "final_children": 0, "final_cpu_permits": 0, "settled": True}
    assert elapsed<6, ('helper backstop used instead of cancellation', elapsed)
    pids = [int(value) for value in helper.with_suffix('.calls').read_text().splitlines()]
    assert len(pids)==2
    for pid in pids:
        try:
            os.kill(pid,0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError('owned synthetic helper survived benchmark return')
    assert digest(candidate)==command[2]
    cases.append({'case':name,'exit':child.returncode,'seconds':elapsed,'helper_pids':pids,
                  'helpers_absent_after_return':True,'input_unchanged':True})
    print('PASS',name,flush=True)
a.report.write_text(json.dumps({'workspace':str(work),'scope':'Actual current core benchmark with synthetic helper processes; no SDK',
    'target_sha256':digest(a.target),'cases':cases,'test_sha256':digest(Path(__file__))},indent=2)+'\n')
