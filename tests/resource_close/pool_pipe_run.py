"""Private close and construction faults through actual worker-pool paths."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[ROOT/'src'/x for x in ['notificationPipe.ml','notificationPipe.mli','semanticWorkers.ml','semanticWorkers.mli']]+[HERE/x for x in ['pipe_fault.ml','pool_pipe_fault.ml','pool_pipe_test.ml','pool_pipe_run.py']]
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for path in paths[:4]:assert path.read_bytes()==(build/path.name).read_bytes(),path.name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticWorkers.cmx')+1];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-pool-pipe-'));calls=[]
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode:raise RuntimeError(json.dumps(calls))
 for original,target in [('pipe_fault.ml','pipeFault.ml'),('pool_pipe_fault.ml','poolPipeFault.ml')]:
  shutil.copyfile(HERE/original,work/target);call([compiler,*flags,'-c',target])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   for old,new in [('Lwt_unix.close reader','PipeFault.wrapped_close reader'),('Unix.close t.read.fd','PipeFault.raw_close t.read.fd'),('Unix.close t.write.fd','PipeFault.raw_close t.write.fd')]:
    assert source.count(old)==1;source=source.replace(old,new)
  if name=='semanticWorkers':
   old='Unix.set_nonblock read_fd;';assert source.count(old)==1;source=source.replace(old,'PoolPipeFault.after_adopt read_fd write_fd; '+old)
   old='let reader = Lwt_unix.of_unix_file_descr read_fd in';assert source.count(old)==1;source=source.replace(old,'PoolPipeFault.before_wrapper (); '+old)
  (work/(name+'.ml')).write_text(source);shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 shutil.copyfile(HERE/'pool_pipe_test.ml',work/'pool_pipe_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['pipeFault.cmx','poolPipeFault.cmx']+[str(work/x) for x in modules[start:]]+['pool_pipe_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for mode in ['known','read','write','both','creation-raw','creation-wrapped']:call([str(work/'fixed'),mode])
 records.append(dict(compiler=compiler,work=str(work),calls=calls,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual pool creation/pump/shutdown, private pipe close after kernel close+reuse and original construction faults; no arbitrary allocation failure/domain-join/RSS/global-FD claim',sources=pins,records=records),f,indent=2)
print('PASS six actual pool pipe cases per stock/Ox compiler')
