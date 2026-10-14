#!/usr/bin/env python3
"""Build the optional native launcher independently of Adobe or OCaml."""
import argparse,pathlib,subprocess,hashlib,json,platform,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--compiler',default='clang');p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
s=pathlib.Path(__file__).with_name('launcher.c').resolve();out=a.output.resolve();out.parent.mkdir(parents=True,exist_ok=True)
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-helper-limits-build-')).resolve();snapshot=w/'launcher.c';snapshot.write_bytes(s.read_bytes());binary=w/'launcher'
command=[a.compiler,'-std=c11','-D_DEFAULT_SOURCE','-D_DARWIN_C_SOURCE','-Wall','-Wextra','-Werror','-O2',str(snapshot),'-o',str(binary)]
x=subprocess.run(command,capture_output=True,text=True)
j=dict(schema='unison-helper-limits-build/1',platform=platform.platform(),source=str(snapshot),sourceSha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),command=command,exit=x.returncode,stdout=x.stdout,stderr=x.stderr)
if x.returncode==0:
 assert s.read_bytes()==snapshot.read_bytes(),'source changed during launcher compilation'
 os.replace(binary,out);j['binary']=str(out);j['binarySha256']=hashlib.sha256(out.read_bytes()).hexdigest()
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print(x.stdout+x.stderr,end='');raise SystemExit(x.returncode)
