#!/usr/bin/env python3
import argparse,pathlib,hashlib,json,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-checked-file-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
sources=['src/'+n+s for n in ['semanticHash','semanticFile'] for s in ['.ml','.mli','.ox.mli.in','_stubs.c']]+['tests/checked_file/test.ml','tests/checked_file/run.py']
for s in sources:shutil.copyfile(r/s,w/pathlib.Path(s).name)
for name,count in [('semanticHash',3),('semanticFile',2)]:
 if ox:
  expected='@@ portable\n'+(r/'src'/ (name+'.mli')).read_text();checked=(w/(name+'.ox.mli.in')).read_text();assert checked==expected;(w/(name+'.mli')).write_text(checked)
  p=w/(name+'.ml');s=p.read_text();assert s.count('(* ox-portable-ffi *)')==count;p.write_text(s.replace('(* ox-portable-ffi *)','@@ portable'))
if not ox:
 p=w/'test.ml';p.write_text(p.read_text().replace('Domain.Safe.spawn','Domain.spawn'))
data=bytes((i*113+29)%256 for i in range(131099))
for i in range(4):
 (w/f'input-{i}.bin').write_bytes(data);(w/f'input-{i}.bin.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n');(w/f'output-{i}.bin').write_bytes(data)
commands=[]
def run(name,argv,expected=0):
 x=subprocess.run(argv,cwd=w,capture_output=True,text=True,timeout=60);log=x.stdout+x.stderr;(w/(name+'.log')).write_text(log);print(log,end='');assert x.returncode==expected,(name,x.returncode);commands.append(dict(name=name,argv=argv,exit=x.returncode,logSha256=hashlib.sha256(log.encode()).hexdigest()));return x
run('compile',[a.compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c','semanticHash.mli','semanticHash.ml','semanticFile.mli','semanticFile.ml','test.ml','-o','test'])
run('runtime',[str(w/'test')])
for i in range(4):
 assert (w/f'input-{i}.bin').read_bytes()==data
 assert (w/f'output-{i}.bin').read_bytes()==data[:17]+b'q'*60006+data[60023:]
if ox:
 negatives={
 'reader':'let _ = SemanticFile.with_fd Unix.stdin (fun shared -> Domain.Safe.spawn (fun () -> ignore(SemanticFile.size shared)))\n',
 'writer':'let shared = SemanticFile.prepare_writer Unix.stdout\nlet _ = Domain.Safe.spawn(fun () -> ignore(SemanticFile.write_at shared "x" 0 1 0L))\n',
 'chunk':'let _ = SemanticFile.with_fd Unix.stdin(fun file -> SemanticFile.iter file 0L 1L(fun chunk _ -> ignore(Domain.Safe.spawn(fun () -> ignore(Bytes.get chunk 0)))))\n'}
 for name,source in negatives.items():
  p=w/(name+'.ml');p.write_text(source);x=run(name,[a.compiler,'-I','+unix','-c',p.name],2);assert 'nonportable' in x.stderr or 'contended' in x.stderr
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-checked-file/1',status='passed',workspace=str(w),compiler=dict(path=a.compiler,version=version,sha256=H(pathlib.Path(a.compiler))),modeChecked=ox,sourcePins={s:H(r/s) for s in sources},actualCompiledInputs={p.name:H(p) for p in w.iterdir() if p.suffix in ['.ml','.mli','.c']},commands=commands,binarySha256=H(w/'test'),outputHashes={str(i):H(w/f'output-{i}.bin') for i in range(4)},sourcePhotosAccessed=False,productionModeInterfaceSelected=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS checked file',version,'retained',w)
