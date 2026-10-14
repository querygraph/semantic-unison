#!/usr/bin/env python3
import argparse,pathlib,tempfile,subprocess,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-xmp-merge-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
sources=['src/'+n+e for n in ['semanticHash','xmpObservation','xmpMerge'] for e in ['.ml','.mli','.ox.mli.in']]+['src/semanticHash_stubs.c','src/semantic_mode_filter.ml','tests/xmp_merge/test.ml','tests/xmp_merge/run.py']
for s in sources:shutil.copyfile(r/s,w/pathlib.Path(s).name)
if ox:
 t=w/'test.ml';s=t.read_text();assert s.count('let () =')==1;t.write_text(s.replace('let () =','let controls () =')+'\nlet () = let ds=List.init 4(fun _ -> Domain.Safe.spawn(fun () -> controls())) in List.iter Domain.join ds\n')
subprocess.run([a.compiler,'-o','filter','semantic_mode_filter.ml'],cwd=w,check=True)
for n in ['semanticHash','xmpObservation','xmpMerge']:
 for e in ['mli','ml']:
  output=subprocess.check_output([str(w/'filter'),version,str(w/(n+'.'+e))]);(w/(n+'.'+e)).write_bytes(output)
cmd=[a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticHash.mli','semanticHash.ml','xmpObservation.mli','xmpObservation.ml','xmpMerge.mli','xmpMerge.ml','test.ml','-o','test'];x=subprocess.run(cmd,cwd=w,capture_output=True,text=True);(w/'compile.log').write_text(x.stdout+x.stderr);assert x.returncode==0,x.stderr
x=subprocess.run([str(w/'test')],cwd=w,capture_output=True,text=True);(w/'test.log').write_text(x.stdout+x.stderr);print(x.stdout+x.stderr,end='');assert x.returncode==0
if ox:
 (w/'portable.ml').write_text('let () = let d=Domain.Safe.spawn(fun () -> ignore(XmpMerge.merge ~base:"bad" ~left:"bad" ~right:"bad")) in Domain.join d\n')
 x=subprocess.run([a.compiler,'-I','+unix','unix.cmxa','semanticHash.cmx','xmpObservation.cmx','xmpMerge.cmx','semanticHash_stubs.o','portable.ml','-o','portable'],cwd=w,capture_output=True,text=True);(w/'portable.log').write_text(x.stdout+x.stderr);assert x.returncode==0,x.stderr;subprocess.run([str(w/'portable')],cwd=w,check=True)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=dict(schema='unison-xmp-scalar-merge-kernel/1',status='passed',workspace=str(w),compiler=dict(path=a.compiler,version=version),sourcePins={s:H(r/s) for s in sources},binarySha256=H(w/'test'),testLogSha256=H(w/'test.log'),compileLogSha256=H(w/'compile.log'),modeChecked=ox,actualCompiledTestSha256=H(w/'test.ml'),concurrentControlDomains=4 if ox else 1,fileMergeEnabled=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n')
