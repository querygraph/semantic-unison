"""Link fixed private close-fault participants into actual worker objects."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for path in a.receipt:
 receipt=json.loads(Path(path).read_text());build=Path(receipt['workspace'])/'src';compiler=receipt['compiler'];version=receipt['compiler_version']
 for name in ('semanticWorkers.ml','semanticWorkers.mli','ownedClose.ml','ownedClose.mli','ownedClose.ox.mli.in','semantic_mode_filter.ml'):
  if (ROOT/'src'/name).read_bytes()!=(build/name).read_bytes():raise ValueError('build source differs: '+name)
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticWorkers.cmx')+1];native=objects('COBJS')
 work=Path(tempfile.mkdtemp(prefix='unison-real-worker-close-'))
 flags=[]
 for directory in (work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'):flags+=['-I',str(directory)]
 flags+=['-I','+unix','-I','+str']
 env=os.environ.copy()
 for key in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(key,None)
 calls=[]
 def call(argv,*,cwd=work,expected=0):
  result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=20)
  calls.append(dict(argv=argv,cwd=str(cwd),returncode=result.returncode,expected=expected,stdout=result.stdout,stderr=result.stderr))
  if result.returncode!=expected:
   with Path(a.report).open('x') as failed:json.dump(dict(state='FAILED_CONTROL_ATTEMPT_PRESERVED',records=records,active_compiler=compiler,active_work=str(work),active_calls=calls),failed,indent=2);failed.write('\n')
   raise RuntimeError(json.dumps(calls[-1]))
  return result
 (work/'workerCloseFault.ml').write_bytes((HERE/'worker_fault.ml').read_bytes())
 (work/'workerCloseFault.mli').write_text(('@@ portable\n' if '+ox' in version else '')+'val arm : unit -> unit\nval close : Unix.file_descr -> unit\nval attempts : unit -> int\nval replacements : unit -> Unix.file_descr list\n')
 (work/'participant.ml').write_bytes((HERE/'worker_fault_test.ml').read_bytes())
 current=(build/'semanticWorkers.ml').read_text();assert current.count('let close = Unix.close')==1
 (work/'semanticWorkers.ml').write_text(current.replace('let close = Unix.close','let close = WorkerCloseFault.close'))
 shutil.copyfile(build/'semanticWorkers.cmi',work/'semanticWorkers.cmi')
 shutil.copyfile(build/'semanticWorkers.mli',work/'semanticWorkers.mli')
 for unit in ('workerCloseFault.mli','workerCloseFault.ml'):
  call([compiler,*flags,'-c',unit])
 call([compiler,*flags,'-pp',str(build/'semantic_mode_filter')+' '+version,'-c','semanticWorkers.ml'])
 argv=[compiler,*flags,'unix.cmxa','str.cmxa',str(work/'workerCloseFault.cmx')]+[str(work/'semanticWorkers.cmx') if name=='semanticWorkers.cmx' else str(build/name) for name in modules]+[str(work/'participant.ml')]+[str(build/name) for name in native]+['-o',str(work/'participant')]
 call(argv)
 for mode in ('known','uncertain','dual','error'):
  case=work/mode;case.mkdir(mode=0o700)
  call([str(work/'participant'),mode],cwd=case)
 # Reproduce the old close-swallowing behavior without changing its runtime
 # logic. Added compatibility bindings are not called by these participants.
 old_call=call(['git','show','674bfc57:src/semanticWorkers.ml'],cwd=ROOT)
 old=old_call.stdout
 expected=json.loads((ROOT/'doc/sync-timed-request-v1.json').read_text())['production_source_sha256']['src/semanticWorkers.ml']
 assert hashlib.sha256(old.encode()).hexdigest()==expected
 old=old.replace('type usage = { workers : int; pending : int; running : int; peak_running : int }',
                 'type usage = { workers : int; pending : int; running : int; peak_running : int; retained : int }')
 old=old.replace('{workers = List.length t.domains; pending = t.pending; running; peak_running}',
                 '{workers = List.length t.domains; pending = t.pending; running; peak_running; retained = 0}')
 hook='let close_noerr fd = try Unix.close fd with Unix.Unix_error _ -> ()'
 assert old.count(hook)==1
 old=old.replace(hook,'let close_noerr fd = try WorkerCloseFault.close fd with Unix.Unix_error _ -> ()')
 # Current interface compatibility only; participant never invokes this API.
 old += '\nlet retain_unsettled _ error = raise error\n'
 baseline=work/'baseline';baseline.mkdir(mode=0o700)
 (baseline/'semanticWorkers.ml').write_text(old)
 shutil.copyfile(build/'semanticWorkers.cmi',baseline/'semanticWorkers.cmi')
 shutil.copyfile(build/'semanticWorkers.mli',baseline/'semanticWorkers.mli')
 shutil.copyfile(work/'participant.ml',baseline/'participant.ml')
 call([compiler,'-I',str(baseline),*flags,'-pp',str(build/'semantic_mode_filter')+' '+version,'-c','semanticWorkers.ml'],cwd=baseline)
 baseline_argv=[str(baseline/'semanticWorkers.cmx') if arg==str(work/'semanticWorkers.cmx') else str(baseline/'participant.ml') if arg==str(work/'participant.ml') else arg for arg in argv]
 baseline_argv[1:1]=['-I',str(baseline)]
 baseline_argv[-1]=str(baseline/'participant')
 call(baseline_argv,cwd=baseline)
 case=baseline/'uncertain';case.mkdir(mode=0o700)
 rejected=call([str(baseline/'participant'),'uncertain'],cwd=case,expected=2)
 assert 'expected-retained-reply' in rejected.stderr
 records.append(dict(compiler=compiler,build=str(build),work=str(work),calls=calls,
                     original_worker_sha256=expected,old_behavior_rejected=True,
                     baseline_compatibility='Zero-valued retained usage field and uncalled retain_unsettled binding only; close swallowing control flow unchanged'))
value=dict(state='ORIGINAL_PRIVATE_WORKER_FAULT_CONTROLS_PASS',scope='Actual worker/close owner objects with ONE private close callback substitution; tiny generated64B inputs; fault pools intentionally retain until controlled process exit, not successful pool shutdown; no SDK/Photo/payload/wholeFD/RSS claim',records=records,sources={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('worker_fault.ml','worker_fault_test.ml','worker_fault_run.py')})
with Path(a.report).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print('PASS actual worker close faults both compilers')
