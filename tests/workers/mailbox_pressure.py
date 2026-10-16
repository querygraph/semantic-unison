#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile,shutil,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--worker-build',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-worker-mailbox-pressure-',dir='/private/tmp'))
for p in a.worker_build.iterdir():
 if p.suffix in ('.ml','.mli','.o','.cmi','.cmx') and p.stem!='test':shutil.copyfile(p,w/p.name)
for n in ['semanticWorkers.ml','semanticWorkers.mli','semanticMailbox.ml','semanticMailbox.mli']:assert (w/n).read_bytes()==(r/'src'/n).read_bytes()
p=w/'semanticWorkers.ml';p.write_text(p.read_text()+'\nlet test_mailboxes t = SemanticMailbox.usage t.shared.jobs, SemanticMailbox.usage t.shared.completions\n')
p=w/'semanticWorkers.mli';p.write_text(p.read_text()+'\nval test_mailboxes : t -> SemanticMailbox.usage * SemanticMailbox.usage\n')
logs=[]
def checked(x):
 if x.returncode:
  (w/"test.log").write_text("".join(logs));print(x.stdout+x.stderr,end="")
 x.check_returncode()
for n in ['semanticWorkers.mli','semanticWorkers.ml']:
 x=subprocess.run([a.compiler,'-I','+unix','-c',n],cwd=w,capture_output=True,text=True);logs.append(x.stdout+x.stderr);checked(x)
# Dependency order from the production-shaped standalone worker runner.
mods=['lwt','pqueue','lwt_unix_impl','lwt_unix','borrowedWork','helperSupervisor','semanticAdmission','ioAdmission','semanticHash','semanticFile','formatRecognition','dngRecognition','formatExtension','xmpObservation','xmpMerge','dngSemantic','dngExtended','semanticDelta','semanticMailbox','semanticWorkers']
shutil.copyfile(r/'tests/workers/mailbox_pressure.ml',w/'mailbox_pressure.ml')
cmd=[a.compiler,'-I','+unix','unix.cmxa',*[m+'.cmx' for m in mods],'helperSupervisor_stubs.o','semanticHash_stubs.o','semanticFile_stubs.o','mailbox_pressure.ml','-o','pressure']
x=subprocess.run(cmd,cwd=w,capture_output=True,text=True);logs.append(x.stdout+x.stderr);checked(x);(w/'input.bin').write_bytes(b'p'*4194304)
x=subprocess.run([str(w/'pressure')],cwd=w,capture_output=True,text=True,timeout=15);logs.append(x.stdout+x.stderr);(w/'test.log').write_text(''.join(logs));print(x.stdout+x.stderr,end='');checked(x)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-worker-mailbox-pressure/1',status='passed',workspace=str(w),compiler=a.compiler,sourcePins={str(p.relative_to(r)):H(p) for p in [r/'src/semanticWorkers.ml',r/'src/semanticWorkers.mli',r/'src/semanticMailbox.ml',r/'src/semanticMailbox.mli',r/'tests/workers/mailbox_pressure.ml',pathlib.Path(__file__)]},privateInstrumentedSources={n:H(w/n) for n in ['semanticWorkers.ml','semanticWorkers.mli']},binarySha256=H(w/'pressure'),logSha256=H(w/'test.log'),output=x.stdout+x.stderr)
a.receipt.write_text(json.dumps(j,indent=2)+'\n')
