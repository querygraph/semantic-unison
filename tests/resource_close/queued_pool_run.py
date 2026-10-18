"""Current compiler-matched production worker queued/cancellation regressions."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[HERE/'queued_pool_test.ml',Path(__file__).resolve(),ROOT/'tests/resource_lifetime/census.c'];pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];source_pins={}
 for name,digest in r['source_sha256'].items():
  if name.startswith('src/'):
   assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name;source_pins[name]=digest
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticWorkers.cmx')+1];native=objects('COBJS')
 work=Path(tempfile.mkdtemp(prefix='unison-queued-pool-'));calls=[]
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=20);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode:raise RuntimeError(json.dumps(calls))
 shutil.copyfile(paths[0],work/'queued_pool_test.ml');shutil.copyfile(paths[2],work/'census.c')
 call([compiler,*flags,'-c','census.c'])
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules]+['queued_pool_test.ml']+[str(build/x) for x in native]+['census.o','-o',str(work/'fixed')])
 for mode in ['queued-cpu','queued-io','cancel-active','shutdown-active']:
  case=work/mode;case.mkdir(mode=0o700);call([str(work/'fixed'),mode],cwd=case)
 records.append(dict(compiler=compiler,work=str(work),source_sha256=source_pins,calls=calls,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual current worker with Atomic-barrier recognizer, queue/CPU/IO cancellation and known shutdown; synthetic4096B files and phase census, no peak/global FD/RSS or SDK/Photo claim',sources=pins,records=records),f,indent=2)
print('PASS four actual queued/cancelled pool cases per stock/Ox compiler')
