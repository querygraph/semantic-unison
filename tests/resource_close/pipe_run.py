"""Fixed original notification pipe ledger faults using real Lwt close."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[ROOT/'src/notificationPipe.ml',ROOT/'src/notificationPipe.mli',HERE/'pipe_fault.ml',HERE/'pipe_fixed.ml',Path(__file__).resolve()]
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler']
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('borrowedWork.cmx')+1];native=objects('COBJS')
 work=Path(tempfile.mkdtemp(prefix='unison-pipe-ledger-'));calls=[]
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=20);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode:raise RuntimeError(json.dumps(calls))
 shutil.copyfile(HERE/'pipe_fault.ml',work/'pipeFault.ml');call([compiler,*flags,'-c','pipeFault.ml'])
 for path in paths[:2]:shutil.copyfile(path,work/path.name)
 source=(work/'notificationPipe.ml').read_text()
 assert source.count('Lwt_unix.close reader')==1 and source.count('Unix.close t.read.fd')==1 and source.count('Unix.close t.write.fd')==1
 source=source.replace('Lwt_unix.close reader','PipeFault.wrapped_close reader').replace('Unix.close t.read.fd','PipeFault.raw_close t.read.fd').replace('Unix.close t.write.fd','PipeFault.raw_close t.write.fd')
 (work/'notificationPipe.ml').write_text(source)
 for name in ['notificationPipe.mli','notificationPipe.ml']:call([compiler,*flags,'-c',name])
 shutil.copyfile(HERE/'pipe_fixed.ml',work/'pipe_fixed.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules]+['pipeFault.cmx','notificationPipe.cmx','pipe_fixed.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for mode in ['known','known-wrapped','read','write','both','wrapped']:
  call([str(work/'fixed'),mode])
 records.append(dict(compiler=compiler,build=str(build),work=str(work),calls=calls,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='NotificationPipe candidate only, real Unix/Lwt close then injected EIO+number reuse; not integrated worker-pool/domain/Runtime qualification',sources=pins,records=records),f,indent=2)
print('PASS six fixed pipe ledger controls per stock/Ox compiler')
