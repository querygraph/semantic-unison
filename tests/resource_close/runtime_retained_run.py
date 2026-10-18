"""Link real Runtime and admission with private real-reader close faults."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for name in ('semanticRuntime.ml','semanticRuntime.mli','semanticFile.ml','semanticFile.mli','retainedOwnership.ml','retainedOwnership.mli'):
  assert (ROOT/'src'/name).read_bytes()==(build/name).read_bytes(),name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRuntime.cmx')+1];native=objects('COBJS');start=modules.index('semanticFile.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-runtime-retention-'));calls=[]
 flags=[v for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for v in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30)
  calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 shutil.copyfile(HERE/'reader_fault.ml',work/'readerCloseFault.ml');call([compiler,*flags,'-c','readerCloseFault.ml'])
 reader=(build/'semanticFile.ml').read_text()
 for old,new in [('then close_in (Atomic.get issue.channel)','then ReaderCloseFault.close_channel (Atomic.get issue.channel)'),('else Unix.close (Atomic.get issue.descriptor)','else ReaderCloseFault.close_raw (Atomic.get issue.descriptor)'),('let channel = Unix.in_channel_of_descr descriptor in','let channel = ReaderCloseFault.channel_of_fd descriptor in')]:
  assert reader.count(old)==1;reader=reader.replace(old,new)
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  (work/(name+'.ml')).write_text(reader) if name=='semanticFile' else shutil.copyfile(build/(name+'.ml'),work/(name+'.ml'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 shutil.copyfile(HERE/'runtime_retained_test.ml',work/'runtime_retained_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa',str(work/'readerCloseFault.cmx')]+[str(work/x) if x in modules[start:] else str(build/x) for x in modules]+['runtime_retained_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for owner in ['internal','explicit']:
  for mode in ['known','known-error','single','error','install','async']:
   case=work/(owner+'-'+mode);case.mkdir(mode=0o700);call([str(work/'fixed'),mode,owner],cwd=case)
 baseline=work/'baseline';baseline.mkdir()
 old=subprocess.run(['git','show','b19c845a:src/semanticRuntime.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
 # Compatibility observation only; old admission/exception control flow stays intact.
 (baseline/'semanticRuntime.ml').write_text(old+'\nlet retained_ownership_count () = 0\nlet guard_ownership f = f () (* uncalled compatibility binding *)\nlet resource_accounting () = invalid_arg "historical Runtime has no infrastructure snapshot" (* uncalled *)\n')
 for ext in ['.mli','.cmi']:shutil.copyfile(build/('semanticRuntime'+ext),baseline/('semanticRuntime'+ext))
 oldflags=['-I',str(baseline),*flags]
 call([compiler,*oldflags,'-c','semanticRuntime.ml'],cwd=baseline)
 # Compile the participant from its own directory to avoid stale .cmx assumptions.
 shutil.copyfile(HERE/'runtime_retained_test.ml',baseline/'runtime_retained_test.ml')
 call([compiler,*oldflags,'unix.cmxa','str.cmxa',str(work/'readerCloseFault.cmx')]+[str(baseline/x) if x=='semanticRuntime.cmx' else str(work/x) if x in modules[start:] else str(build/x) for x in modules]+['runtime_retained_test.ml']+[str(build/x) for x in native]+['-o',str(baseline/'old')],cwd=baseline)
 for owner in ['internal','explicit']:
  case=baseline/owner;case.mkdir(mode=0o700)
  failure=call([str(baseline/'old'),'single',owner],cwd=case,expected=2)
  assert 'DESIGNATED runtime released uncertain reader reply' in failure.stderr
 records.append(dict(compiler=compiler,build=str(build),work=str(work),calls=calls,old_runtime_sha256=hashlib.sha256(old.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Linked actual Runtime/admission/reader with private close-after-kernel-close+FD reuse, two admission paths; no complete pool/FD/RSS qualification',records=records,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'runtime_retained_run.py',HERE/'runtime_retained_test.ml',HERE/'reader_fault.ml']}),f,indent=2)
print('PASS actual Runtime/admission retention stock/Ox')
