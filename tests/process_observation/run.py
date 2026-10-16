"""Compile an OS metadata probe and observe one original threaded Python child."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'bench/sync'))
from ownership import OwnedGroup
SOURCE=ROOT/'tools/process-observation/task_info.c'
p=argparse.ArgumentParser();p.add_argument('--work',required=True,type=Path);a=p.parse_args();w=a.work;w.mkdir(mode=0o700)
exe=w/'probe';compiled=subprocess.run(['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',str(SOURCE),'-lproc','-o',str(exe)],capture_output=True,text=True)
(w/'build.log').write_text(compiled.stdout+compiled.stderr);assert compiled.returncode==0,compiled.stderr
for value in ['0','-1','+1','01','1x','2147483648']:
 r=subprocess.run([str(exe),value],capture_output=True,text=True);assert r.returncode==64
helper=w/'original.py';helper.write_text('''import pathlib,sys,threading,time
root=pathlib.Path(sys.argv[1]);done=threading.Event()
threads=[threading.Thread(target=lambda:done.wait()) for _ in range(6)]
for t in threads:t.start()
(root/'ready').write_text('six threads started')
while not (root/'release').exists():time.sleep(.005)
done.set()
for t in threads:t.join()
''')
child=OwnedGroup([sys.executable,str(helper),str(w)],strict_group_settlement=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
samples=[];closure=None
try:
 deadline=time.monotonic()+5
 while not (w/'ready').exists():
  assert not child.terminal() and time.monotonic()<deadline,'original helper did not become ready';time.sleep(.005)
 for _ in range(3):
  assert not child.reaped and not child.terminal()
  before=time.monotonic_ns();r=subprocess.run([str(exe),str(child.pid)],capture_output=True,text=True,timeout=2);after=time.monotonic_ns()
  assert r.returncode==0;sample=json.loads(r.stdout)
  assert sample['available'] is True and sample['pid']==child.pid and sample['threads']>=7
  assert sample['resident_bytes']>0 and sample['virtual_bytes']>=sample['resident_bytes']
  samples.append(dict(before_monotonic_ns=before,after_monotonic_ns=after,observation=sample))
finally:
 (w/'release').touch();assert child.await_terminal(5)
 closure,_=child.finish(grace=1)
assert closure['returncode']==0 and closure['reaped'] and closure['other_group_members_absent_before_reap']
try:os.waitpid(child.pid,os.WNOHANG)
except ChildProcessError:pass
else:raise AssertionError('original child was not reaped')
unknown=subprocess.run([str(exe),'2147483647'],capture_output=True,text=True);assert unknown.returncode==0 and json.loads(unknown.stdout)['available'] is False
(w/'RESULT.json').write_text(json.dumps(dict(samples=samples,actual_child_closure=closure,probe_source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),probe_binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),invalid_pid_controls=6,unknown_not_zero=True,sdk_calls=0,
 scope='OS kernel per-process snapshot on1originalPythonchild with6waiting threads;3samples/6invalidPID/unknownPID controls. Not aggregate-tree RSS, peak memory, CPU unit calibration, SDK/OSthread cap or performance.',pending_sdk_request_unchanged=True),indent=2)+'\n')
print(json.dumps(dict(workspace=str(w),samples=3,minimum_observed_threads=min(s['observation']['threads'] for s in samples),child_reaped=True,sdk_calls=0)))
