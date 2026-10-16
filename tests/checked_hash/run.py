#!/usr/bin/env python3
"""Compile portable hash contract, execute real stubs and forced reference."""
import argparse,pathlib,hashlib,json,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-checked-hash-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
sources=['src/semanticHash.ml','src/semanticHash.mli','src/semanticHash.ox.mli.in','src/semanticHash_stubs.c','tests/checked_hash/test.ml','tests/checked_hash/run.py']
results=[]
for mode in ['native','forced-reference']:
 d=w/mode;d.mkdir()
 for name in ['semanticHash.ml','semanticHash.mli','semanticHash_stubs.c']:shutil.copyfile(r/'src'/name,d/name)
 shutil.copyfile(r/'tests/checked_hash/test.ml',d/'test.ml')
 if ox:
  interface=(r/'src/semanticHash.ox.mli.in').read_text();assert interface=='@@ portable\n'+(r/'src/semanticHash.mli').read_text();(d/'semanticHash.mli').write_text(interface)
  x=(d/'semanticHash.ml').read_text();assert x.count('(* ox-portable-ffi *)')==3;(d/'semanticHash.ml').write_text(x.replace('(* ox-portable-ffi *)','@@ portable'))
 else:
  p=d/'test.ml';p.write_text(p.read_text().replace('Domain.Safe.spawn','Domain.spawn'))
 if mode=='forced-reference':
  p=d/'semanticHash_stubs.c';p.write_text(p.read_text().replace('#ifdef __APPLE__','#if 0 /* qualification only: force reference backend */'))
 for length in [0,1,55,56,63,64,65,119,120,127,128,65535,65536,65537,1048576]:
  data=bytes((i*113+29)%256 for i in range(length));(d/(str(length)+'.bin')).write_bytes(data);(d/(str(length)+'.sha256')).write_text(hashlib.sha256(data).hexdigest())
 commands=[]
 def run(name,argv,expected=0):
  x=subprocess.run(argv,cwd=d,capture_output=True,text=True,timeout=60);log=x.stdout+x.stderr;(d/(name+'.log')).write_text(log);print(log,end='');assert x.returncode==expected,(name,x.returncode);commands.append(dict(name=name,argv=argv,exit=x.returncode,logSha256=hashlib.sha256(log.encode()).hexdigest()));return x
 run('compile',[a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticHash.mli','semanticHash.ml','test.ml','-o','test'])
 run('runtime',[str(d/'test')])
 if ox:
  for name,decl,body in [('context','SemanticHash.create ()','ignore(SemanticHash.finish shared)'),('input','Bytes.of_string "xmp"','SemanticHash.feed (SemanticHash.create ()) shared 0 3')]:
   p=d/(name+'.ml');p.write_text('let shared = '+decl+'\nlet _ = Domain.Safe.spawn (fun () -> '+body+')\n')
   x=run(name,[a.compiler,'-c',p.name],2);assert 'nonportable' in x.stderr or 'contended' in x.stderr
 H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 results.append(dict(mode=mode,root=str(d),commands=commands,compiledInputs={p.name:H(p) for p in d.iterdir() if p.suffix in ['.ml','.mli','.c']},binarySha256=H(d/'test')))
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-checked-hash/1',status='passed',compiler=dict(path=a.compiler,version=version,sha256=H(pathlib.Path(a.compiler))),modeChecked=ox,workspace=str(w),sourcePins={s:H(r/s) for s in sources},results=results,productionModeInterfaceSelected=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS checked hash',version,'retained',w)
