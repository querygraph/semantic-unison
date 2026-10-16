#!/usr/bin/env python3
"""Pin installed OxCaml compiler diagnostics for the real worker boundary."""
import argparse,hashlib,json,pathlib,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--worker-build',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-ox-boundary-',dir='/private/tmp'))
# Import only compiler-matched object/interfaces and their matching source.
for s in a.worker_build.iterdir():
 if s.stem!='test' and s.suffix in ('.cmi','.cmx','.o','.ml','.mli'):shutil.copyfile(s,w/s.name)
source_pins={}
for s in w.glob('*.ml'):
 current=next((p for d in ['src','src/lwt','src/lwt/generic'] if (p:=root/d/s.name).exists()),root/'src'/s.name)
 if current.exists(): assert current.read_bytes()==s.read_bytes(),str(current);source_pins[str(current.relative_to(root))]=hashlib.sha256(s.read_bytes()).hexdigest()
for s in w.glob('*.mli'):
 current=next((p for d in ['src','src/lwt','src/lwt/generic'] if (p:=root/d/s.name).exists()),root/'src'/s.name)
 if current.exists(): assert current.read_bytes()==s.read_bytes(),str(current);source_pins[str(current.relative_to(root))]=hashlib.sha256(s.read_bytes()).hexdigest()
compiler=pathlib.Path(a.compiler);version=subprocess.check_output([str(compiler),'-version'],text=True).strip();assert '+ox' in version,version
cases=[]
def compile_case(name,path,expect,needle=None,run=False):
 command=[str(compiler),'-I','+unix']+(['unix.cmxa',path.name,'-o',name] if run else ['-c',path.name])
 r=subprocess.run(command,cwd=w,capture_output=True,text=True,timeout=60);log=r.stdout+r.stderr;(w/(name+'.log')).write_text(log)
 assert (r.returncode==0)==expect,(name,log)
 if needle:assert needle in log,(name,log)
 runtime=None
 if run:
  rr=subprocess.run([str(w/name)],capture_output=True,text=True,timeout=10);assert rr.returncode==0,rr.stdout+rr.stderr;runtime=dict(exit=rr.returncode,output=rr.stdout+rr.stderr)
 cases.append(dict(name=name,command=command,exit=r.returncode,log=str(w/(name+'.log')),logSha256=hashlib.sha256(log.encode()).hexdigest(),sourceSha256=hashlib.sha256(path.read_bytes()).hexdigest(),runtime=runtime))
worker=w/'semanticWorkers.ml';original=worker.read_text();compile_case('production-original',worker,True)
assert original.count('Domain.spawn (worker shared)')==1
worker.write_text(original.replace('Domain.spawn (worker shared)','Domain.Safe.spawn (worker shared)'))
compile_case('production-safe-substitution',worker,False,'portable')
worker.write_text(original)
positive=w/'portable.ml';positive.write_text('let () = let cell = Atomic.make 0 in\n let d = Domain.Safe.spawn (fun () -> Atomic.set cell 42) in\n Domain.join d; if Atomic.get cell <> 42 then failwith "bad result";\n print_endline "PASS compiler-checked portable atomic capture"\n')
compile_case('portable',positive,True,run=True)
negative=w/'unsafe_ref.ml';negative.write_text('let cell = ref 0\nlet _ = Domain.Safe.spawn (fun () -> cell := 42)\n')
compile_case('unsafe-ref-capture',negative,False,'portable')
negative=w/'mutex_ref.ml';negative.write_text('let cell = ref 0\nlet lock = Mutex.create ()\nlet _ = Domain.Safe.spawn (fun () -> Mutex.lock lock; cell := 42; Mutex.unlock lock)\n')
compile_case('plain-mutex-ref-capture',negative,False,'portable')
r=dict(schema='unison-oxcaml-boundary-probe/1',state='PRODUCTION_NOT_COMPILER_PROVED_SAFE_SUBSTITUTION_REJECTED',workspace=str(w),compiler=dict(path=str(compiler),version=version,sha256=hashlib.sha256(compiler.read_bytes()).hexdigest()),installedInterfacePins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [compiler.parent.parent/'lib/ocaml/domain.mli',compiler.parent.parent/'lib/ocaml/mutex.mli']},sourcePins=source_pins,cases=cases,objectPins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in w.iterdir() if p.suffix in ('.cmi','.cmx','.o')},probeSourcePin=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),productionChanges=0,qualifiedProductionSafeBoundary=False)
a.receipt.write_text(json.dumps(r,indent=2)+'\n');print('PASS five compiler boundary probes; retained',w)
