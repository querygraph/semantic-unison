"""Actual pool stop/join and runtime publication faults, no SDK."""
import argparse,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
paths=[ROOT/'src'/x for x in ['notificationPipe.ml','notificationPipe.mli','domainOwner.ml','domainOwner.mli','semanticWorkers.ml','semanticWorkers.mli','semanticRuntime.ml','semanticRuntime.mli']]+[HERE/x for x in ['pipe_fault.ml','pool_lifecycle_fault.ml','pool_lifecycle_test.ml','pool_lifecycle_run.py','domain_slot_test.ml']]
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for path in paths[:8]:assert path.read_bytes()==(build/path.name).read_bytes(),path.name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRuntime.cmx')+1];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-pool-lifecycle-'));calls=[]
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 for original,target in [('pipe_fault.ml','pipeFault.ml'),('pool_lifecycle_fault.ml','poolLifecycleFault.ml')]:
  shutil.copyfile(HERE/original,work/target);call([compiler,*flags,'-c',target])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   for old,new in [('Lwt_unix.close reader','PipeFault.wrapped_close reader'),('Unix.close t.read.fd','PipeFault.raw_close t.read.fd'),('Unix.close t.write.fd','PipeFault.raw_close t.write.fd')]:
    assert source.count(old)==1;source=source.replace(old,new)
  if name=='semanticWorkers':
   old='Unix.set_nonblock read_fd;';assert source.count(old)==1;source=source.replace(old,'PoolLifecycleFault.after_adopt read_fd write_fd; '+old)
   old='let reader = Lwt_unix.of_unix_file_descr read_fd in';assert source.count(old)==1;source=source.replace(old,'PoolLifecycleFault.before_wrapper (); '+old)
   old='DomainOwner.adopt domains.(index) domain';assert source.count(old)==1
   source=source.replace(old,old+'; PoolLifecycleFault.after_publish index')
   old='let stop shared =\n    locked shared';assert source.count(old)==1
   source=source.replace(old,'let stop shared =\n    PoolLifecycleFault.before_stop ();\n    locked shared')
   old='      else begin\n        locked t.shared (fun () -> Atomic.set t.shared.stopping true;';assert source.count(old)==1
   source=source.replace(old,'      else begin\n        PoolLifecycleFault.before_stop ();\n        locked t.shared (fun () -> Atomic.set t.shared.stopping true;')
  if name=='domainOwner':
   old='Domain.join (Obj.obj slot.handle : unit Domain.t)';assert source.count(old)==1
   source=source.replace(old,'PoolLifecycleFault.join (Obj.obj slot.handle : unit Domain.t)')
  if name=='semanticRuntime':
   old='try\n    SemanticWorkers.set_read_observer';assert source.count(old)==1
   source=source.replace(old,'try\n    PoolLifecycleFault.before_publish ();\n    SemanticWorkers.set_read_observer')
  (work/(name+'.ml')).write_text(source);shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 shutil.copyfile(HERE/'pool_lifecycle_test.ml',work/'pool_lifecycle_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['pipeFault.cmx','poolLifecycleFault.cmx']+[str(work/x) for x in modules[start:]]+['pool_lifecycle_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for mode in ['creation-before','creation-after','creation-stop','shutdown-before','shutdown-after','shutdown-stop','handoff','publication-first','publication-second']:call([str(work/'fixed'),mode])
 slot_source=(HERE/'domain_slot_test.ml').read_text()
 marker='Domain.spawn (* ox-safe-worker-spawn *)';assert slot_source.count(marker)==1
 slot_source=slot_source.replace(marker,'Domain.Safe.spawn' if '+ox' in compiler else 'Domain.spawn')
 (work/'domain_slot_test.ml').write_text(slot_source)
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['pipeFault.cmx','poolLifecycleFault.cmx']+[str(work/x) for x in modules[start:]]+['domain_slot_test.ml']+[str(build/x) for x in native]+['-o',str(work/'slots')])
 call([str(work/'slots')])
 for variant in ['old-runtime','no-latch']:
  private=work/variant;private.mkdir()
  if variant=='old-runtime':
   old=subprocess.run(['git','show','501085bd:src/semanticRuntime.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
   marker='    SemanticWorkers.set_read_observer';assert old.count(marker)==1
   altered=old.replace(marker,'    PoolLifecycleFault.before_publish ();\n'+marker)+'\nlet guard_ownership f = f () (* uncalled compatibility binding *)\n'
   designated='DESIGNATED runtime lost unpublished pool owner'
  else:
   altered=(work/'semanticRuntime.ml').read_text()
   marker='  if !runtime_unresolved then raise !runtime_failure;';assert altered.count(marker)==1
   altered=altered.replace(marker,'')
   designated='runtime silently created replacement pool'
  (private/'semanticRuntime.ml').write_text(altered)
  for ext in ['.mli','.cmi']:shutil.copyfile(build/('semanticRuntime'+ext),private/('semanticRuntime'+ext))
  privateflags=['-I',str(private),*flags]
  call([compiler,*privateflags,'-c','semanticRuntime.ml'],cwd=private)
  shutil.copyfile(HERE/'pool_lifecycle_test.ml',private/'pool_lifecycle_test.ml')
  call([compiler,*privateflags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['../pipeFault.cmx','../poolLifecycleFault.cmx']+[str(private/x) if x=='semanticRuntime.cmx' else str(work/x) for x in modules[start:]]+['pool_lifecycle_test.ml']+[str(build/x) for x in native]+['-o',str(private/'regression')],cwd=private)
  failed=call([str(private/'regression'),'handoff'],expected=2)
  assert designated in failed.stderr
 records.append(dict(compiler=compiler,work=str(work),calls=calls,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual pool stop/join errors before and after real join, retained Runtime singleton publication; unknown domain ownership settles at process exit only, no arbitrary allocation failure or aggregate RSS/FD claim',sources=pins,records=records),f,indent=2)
print('PASS seven actual pool lifecycle cases per stock/Ox compiler')
