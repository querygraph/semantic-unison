#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile,shutil,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--filter',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-mode-filter-controls-',dir='/private/tmp'));cases=[]
for n in ['semanticHash','semanticFile','semanticMailbox']:
 for suffix in ['.ml','.mli','.ox.mli.in']:shutil.copyfile(r/'src'/(n+suffix),w/(n+suffix))
def run(name,version,path,expected=None,reject=False):
 x=subprocess.run([str(a.filter),version,str(path)],capture_output=True,timeout=10)
 if reject:assert x.returncode!=0 and not x.stdout,(name,x.stdout)
 else:assert x.returncode==0 and x.stdout==expected,(name,x.stderr)
 cases.append(dict(name=name,exit=x.returncode,stdoutSha256=hashlib.sha256(x.stdout).hexdigest(),stderr=x.stderr.decode()))
for n in ['semanticHash','semanticFile','semanticMailbox']:
 for suffix in ['.ml','.mli']:
  path=w/(n+suffix);source=path.read_bytes();run(n+suffix+'-stock','5.5.1',path,source)
  expected=(w/(n+'.ox.mli.in')).read_bytes() if suffix=='.mli' else source.replace(b'(* ox-portable-ffi *)',b'@@ portable')
  run(n+suffix+'-ox','5.2.0+ox',path,expected)
path=w/'unknown.ml';path.write_text('let secret=0\n');run('unknown-module','5.2.0+ox',path,reject=True)
p=w/'semanticHash.ox.mli.in';p.write_bytes(p.read_bytes()+b'\n');run('tampered-template','5.2.0+ox',w/'semanticHash.mli',reject=True)
p=w/'semanticHash.ml';original=p.read_bytes();p.write_bytes(original.replace(b'(* ox-portable-ffi *)',b'',1));run('missing-ffi-marker','5.2.0+ox',p,reject=True)
p.write_bytes(original+b'\n(* ox-portable-ffi *)');run('extra-ffi-marker','5.2.0+ox',p,reject=True)
p.write_bytes(b'x'*1048577);run('oversized-source','5.5.1',p,reject=True)
p=w/'semanticMailbox.mli';p.write_text(p.read_text().replace("type 'a t","type 'a changed"));run('changed-mailbox-declaration','5.2.0+ox',p,reject=True)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=dict(schema='unison-semantic-mode-filter-controls/1',status='passed',workspace=str(w),filter=dict(path=str(a.filter),sha256=H(a.filter)),sourcePins={s:H(r/s) for s in ['src/semantic_mode_filter.ml','tests/mode_build/filter.py']},cases=cases)
a.receipt.write_text(json.dumps(j,indent=2)+'\n');print('PASS mode filter',len(cases),'controls',w)
