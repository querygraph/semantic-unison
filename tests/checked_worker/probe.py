#!/usr/bin/env python3
"""Compiler negatives against actual production OxCaml interfaces."""
import argparse,pathlib,tempfile,subprocess,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-checked-worker-negative-',dir='/private/tmp'));c=a.compiler;version=subprocess.check_output([c,'-version'],text=True).strip();assert '+ox' in version
flags=['-I','+unix','-I',str(a.build/'lwt'),'-I',str(a.build/'lwt/generic'),'-I',str(a.build)];cases=[]
sources={
 'recognizer-state':'let state=ref 0\nmodule R=struct let format="bad-recognizer" let identify _ = incr state;FormatRecognition.Not_matched end\nlet _=FormatRecognition.trusted(module R)\n',
 'inspector-state':'let state=ref 0\nmodule E=struct let profile="bad-inspector" let inspect _ = incr state;Error "bad" end\nlet _=FormatExtension.trusted(module E)\n',
 'observer-state':'let state=ref 0\nlet _ : FormatExtension.observer = {schema="bad";observe=(fun _ -> incr state;Ok [])}\n',
 'owner-registry':'let _=Domain.Safe.spawn(fun () -> ignore(FormatExtension.profiles()))\n',
 'owner-pool':'let budget=HelperSupervisor.create ~cpu_permits:1 ~max_children:1 ~max_pending:2\nlet pool=SemanticWorkers.create ~workers:1 ~max_pending:2 ~budget\nlet _=Domain.Safe.spawn(fun () -> ignore(SemanticWorkers.usage pool))\n',
}
def reject(name,source):
 (w/(name+'.ml')).write_text(source);x=subprocess.run([c,*flags,'-c',name+'.ml'],cwd=w,capture_output=True,text=True,timeout=30);log=x.stdout+x.stderr;(w/(name+'.log')).write_text(log);assert x.returncode==2,(name,log);assert 'portable' in log or 'contended' in log,(name,log);cases.append(dict(name=name,exit=x.returncode,sourceSha256=hashlib.sha256(source.encode()).hexdigest(),logSha256=hashlib.sha256(log.encode()).hexdigest()));print('PASS rejected',name)
for n,s in sources.items():reject(n,s)
# Genuine former shared-counter implementation against current portable
# extension interfaces: isolate the cause without replaying old runtime work.
old=subprocess.check_output(['git','show','49dc756:src/semanticWorkers.ml'],cwd=r).decode();assert old.count('Domain.spawn (worker shared)')==1
old=old.replace('Domain.spawn (worker shared)','Domain.Safe.spawn (fun () -> worker shared ())');shutil.copyfile(a.build/'semanticWorkers.cmi',w/'semanticWorkers.cmi');reject('semanticWorkers',old)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-checked-production-worker-negative/1',status='passed',workspace=str(w),build=str(a.build),compiler=dict(path=c,version=version,sha256=H(pathlib.Path(c))),cases=cases,previousWorkerCommit='49dc756',previousWorkerSha256=hashlib.sha256(subprocess.check_output(['git','show','49dc756:src/semanticWorkers.ml'],cwd=r)).hexdigest(),actualInterfacePins={str(p):H(p) for p in a.build.rglob('*.cmi')},probeSha256=H(pathlib.Path(__file__)),runtimeInvocation=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS six actual-interface negative controls',w)
