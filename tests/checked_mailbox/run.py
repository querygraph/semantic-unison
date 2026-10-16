#!/usr/bin/env python3
"""Same mailbox implementation under stock and OxCaml mode-checked exports."""
import argparse,pathlib,subprocess,tempfile,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-mailbox-',dir='/private/tmp'));version=subprocess.check_output([a.compiler,'-version'],text=True).strip();ox='+ox' in version
sources=['src/semanticMailbox.ml','src/semanticMailbox.mli','src/semanticMailbox.ox.mli.in','tests/checked_mailbox/test.ml']
for s in sources:shutil.copyfile(r/s,w/pathlib.Path(s).name)
if ox:
 p=w/'semanticMailbox.mli';expected='@@ portable\n'+p.read_text().replace("type 'a t", "type 'a t : value mod portable contended with 'a");checked=(r/'src/semanticMailbox.ox.mli.in').read_text();assert checked==expected; p.write_text(checked)
else:
 p=w/'test.ml';p.write_text(p.read_text().replace('Domain.Safe.spawn','Domain.spawn'))
commands=[]
def run(name,cmd,expected=0):
 x=subprocess.run(cmd,cwd=w,capture_output=True,text=True,timeout=60);log=x.stdout+x.stderr;(w/(name+'.log')).write_text(log);print(log,end='');assert x.returncode==expected,(name,x.returncode)
 commands.append(dict(name=name,argv=cmd,exit=x.returncode,logSha256=hashlib.sha256(log.encode()).hexdigest()));return x
run('compile',[a.compiler,'-I','+unix','unix.cmxa','semanticMailbox.mli','semanticMailbox.ml','test.ml','-o','test'])
run('runtime',[str(w/'test')])
if ox:
 for name,expr in [('reference','ref 7'),('bytes','Bytes.of_string "packet"')]:
  p=w/(name+'.ml');p.write_text('let q = SemanticMailbox.create ~capacity:2\nlet _ = SemanticMailbox.push q ('+expr+')\nlet _ = Domain.Safe.spawn (fun () -> match SemanticMailbox.pop q with Item payload -> '+('ignore (!payload)' if name=='reference' else 'ignore (Bytes.get payload 0)')+' | _ -> ())\n')
  x=run(name,[a.compiler,'-I','+unix','-c',p.name],expected=2);assert 'contended' in x.stderr or 'nonportable' in x.stderr
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-checked-mailbox/1',status='passed',workspace=str(w),compiler=dict(path=a.compiler,version=version,sha256=H(pathlib.Path(a.compiler))),modeChecked=ox,sourcePins={s:H(r/s) for s in sources+['tests/checked_mailbox/run.py']},actualCompiledSources={p.name:H(p) for p in w.iterdir() if p.suffix in ['.ml','.mli']},binarySha256=H(w/'test'),commands=commands,productionWorkerIntegrated=False)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS mailbox',version,'12000 jobs retained',w)
