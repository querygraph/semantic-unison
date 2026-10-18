"""Actual Runtime I/O-scope closure and nested-carrier retention."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for name in ('semanticRuntime.ml','semanticRuntime.mli','notificationPipe.ml','notificationPipe.mli'):
  assert (ROOT/'src'/name).read_bytes()==(build/name).read_bytes(),name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRuntime.cmx')+1];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-io-scope-'));calls=[]
 flags=[v for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for v in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30)
  calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 shutil.copyfile(HERE/'io_scope_fault.ml',work/'ioScopeFault.ml');call([compiler,*flags,'-c','ioScopeFault.ml'])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   old='Unix.close t.read.fd';assert source.count(old)==1;source=source.replace(old,'IoScopeFault.close t.read.fd')
  if name=='semanticRuntime':
   old='Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0';assert source.count(old)==1;source=source.replace(old,'IoScopeFault.open_candidate path')
  (work/(name+'.ml')).write_text(source)
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 shutil.copyfile(HERE/'io_scope_test.ml',work/'io_scope_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['ioScopeFault.cmx']+[str(work/x) for x in modules[start:]]+['io_scope_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for mode in ['known','error','cancel','close','error-close','nested']:
  case=work/mode;case.mkdir(mode=0o700);call([str(work/'fixed'),mode],cwd=case)
 baseline=work/'baseline';baseline.mkdir()
 old=subprocess.run(['git','show','006ab439:src/semanticRuntime.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
 marker='Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0';assert old.count(marker)==1
 old=old.replace(marker,'IoScopeFault.open_candidate path')
 marker='try Unix.close fd with Unix.Unix_error _ -> ()';assert old.count(marker)==2
 old=old.replace(marker,'try IoScopeFault.close fd with Unix.Unix_error _ -> ()')
 (baseline/'semanticRuntime.ml').write_text(old)
 for ext in ['.mli','.cmi']:shutil.copyfile(build/('semanticRuntime'+ext),baseline/('semanticRuntime'+ext))
 privateflags=['-I',str(baseline),*flags]
 call([compiler,*privateflags,'-c','semanticRuntime.ml'],cwd=baseline)
 shutil.copyfile(HERE/'io_scope_test.ml',baseline/'io_scope_test.ml')
 call([compiler,*privateflags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+[str(work/'ioScopeFault.cmx')]+[str(baseline/x) if x=='semanticRuntime.cmx' else str(work/x) for x in modules[start:]]+['io_scope_test.ml']+[str(build/x) for x in native]+['-o',str(baseline/'old')],cwd=baseline)
 for mode in ['close','nested']:
  case=baseline/mode;case.mkdir(mode=0o700)
  c=call([str(baseline/'old'),mode],cwd=case,expected=2)
  assert 'DESIGNATED uncertain I/O scope' in c.stderr
 records.append(dict(compiler=compiler,build=str(build),work=str(work),calls=calls,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual Runtime I/O scheduling FD and I/O/admission lease closure; private real close/EIO/reuse, nested uncertain callback, no global FD/RSS claim',records=records,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'io_scope_run.py',HERE/'io_scope_test.ml',HERE/'io_scope_fault.ml']}),f,indent=2)
print('PASS actual Runtime I/O-scope retention stock/Ox')
