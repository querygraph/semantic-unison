#!/usr/bin/env python3
import argparse,pathlib,tempfile,subprocess,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--dune',action='store_true');p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-production-modes-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
if a.dune:
 base=a.build/'_build/default/src';cmx=base/'.unison_lib.objs/native';cmi=base/'.unison_lib.objs/byte'
else:base=a.build/'src';cmx=cmi=base
source=(r/'tests/mode_build/positive.ml').read_text();(w/'positive.ml').write_text(source if ox else source.replace('Domain.Safe.spawn','Domain.spawn'))
data=bytes((i*113+29)%256 for i in range(131099));(w/'input.bin').write_bytes(data);(w/'expected.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n')
flags=['-I','+unix','-I',str(cmi),'-I',str(cmx)];modules=[cmx/(n+'.cmx') for n in ['semanticHash','semanticFile','semanticMailbox']];native=[base/(n+'_stubs.o') for n in ['semanticHash','semanticFile']]
commands=[]
def run(name,argv,expected=0):
 x=subprocess.run(argv,cwd=w,capture_output=True,text=True,timeout=30);log=x.stdout+x.stderr;(w/(name+'.log')).write_text(log);print(log,end='');assert x.returncode==expected,(name,x.returncode);commands.append(dict(name=name,argv=argv,exit=x.returncode,logSha256=hashlib.sha256(log.encode()).hexdigest()));return x
run('link',[a.compiler,*flags,'unix.cmxa',*map(str,modules),*map(str,native),'positive.ml','-o','positive'])
run('runtime',[str(w/'positive')])
if ox:
 (w/'negative.ml').write_text('let q = SemanticMailbox.create ~capacity:2\nlet _ = SemanticMailbox.push q (ref 0)\nlet _ = Domain.Safe.spawn(fun () -> match SemanticMailbox.pop q with Item x -> ignore(!x) | _ -> ())\n')
 x=run('negative',[a.compiler,*flags,'-c','negative.ml'],2);assert 'contended' in x.stderr or 'nonportable' in x.stderr
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-actual-production-mode-exports/1',status='passed',build=str(a.build),dune=a.dune,workspace=str(w),compiler=dict(path=a.compiler,version=version),modeChecked=ox,commands=commands,linkedObjects={str(p):H(p) for p in modules+native+[cmi/(n+'.cmi') for n in ['semanticHash','semanticFile','semanticMailbox']]},sourcePins={p:H(r/p) for p in ['tests/mode_build/positive.ml','tests/mode_build/probe.py']},binarySha256=H(w/'positive'),fullWorkerPortable=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS actual production mode exports',version,'dune',a.dune,w)
