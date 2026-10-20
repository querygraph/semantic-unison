"""Fixed real-reader/worker tests with private close substitutions, no SDK."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[];calls=[]
for receipt_path in a.receipt:
 receipt=json.loads(Path(receipt_path).read_text());build=Path(receipt['workspace'])/'src';compiler=receipt['compiler'];version=receipt['compiler_version']
 for name in ('semanticFile.ml','semanticFile.mli','semanticFile.ox.mli.in','semanticWorkers.ml','semanticWorkers.mli','semantic_mode_filter.ml'):
  if (ROOT/'src'/name).read_bytes()!=(build/name).read_bytes():raise ValueError('source differs: '+name)
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticWorkers.cmx')+1];native=objects('COBJS');reader_end=modules.index('semanticFile.cmx')
 baseline=subprocess.run(['git','show','ef74f3f5:src/semanticFile.ml'],cwd=ROOT,capture_output=True,text=True,check=True,timeout=3).stdout
 expected=json.loads((ROOT/'doc/sync-timed-request-v1.json').read_text())['production_source_sha256']['src/semanticFile.ml']
 assert hashlib.sha256(baseline.encode()).hexdigest()==expected
 for variant in ('current','baseline'):
  work=Path(tempfile.mkdtemp(prefix='unison-reader-'+variant+'-'));calls=[]
  env=os.environ.copy()
  for key in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(key,None)
  flags=[]
  for directory in (work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'):flags+=['-I',str(directory)]
  flags+=['-I','+unix','-I','+str']
  def call(argv,*,cwd=work,expected=0):
   completed=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=20)
   calls.append(dict(argv=argv,cwd=str(cwd),returncode=completed.returncode,expected=expected,stdout=completed.stdout,stderr=completed.stderr))
   if completed.returncode!=expected:
    with Path(a.report).open('x') as f:json.dump(dict(state='FAILED_CONTROL_PRESERVED',records=records,active_compiler=compiler,variant=variant,work=str(work),calls=calls),f,indent=2);f.write('\n')
    raise RuntimeError(json.dumps(calls[-1]))
   return completed
  (work/'readerCloseFault.ml').write_bytes((HERE/'reader_fault.ml').read_bytes())
  (work/'readerCloseFault.mli').write_text(('@@ portable\n' if '+ox' in version else '')+'exception Install_failed\nval arm : install:bool -> unit\nval close_channel : in_channel -> unit\nval close_raw : Unix.file_descr -> unit\nval channel_of_fd : Unix.file_descr -> in_channel\nval attempts : unit -> int\nval replacements : unit -> Unix.file_descr list\n')
  for unit in ('readerCloseFault.mli','readerCloseFault.ml'):call([compiler,*flags,'-c',unit])
  source=(build/'semanticFile.ml').read_text() if variant=='current' else baseline
  if variant=='current':
   substitutions=[('then close_in (Atomic.get issue.channel)','then ReaderCloseFault.close_channel (Atomic.get issue.channel)'),('else Unix.close (Atomic.get issue.descriptor)','else ReaderCloseFault.close_raw (Atomic.get issue.descriptor)'),('let channel = Unix.in_channel_of_descr descriptor in','let channel = ReaderCloseFault.channel_of_fd descriptor in')]
  else:
   # API compatibility only. The old close/exception control flow is unchanged.
   source='type close_issue=unit\nexception Close_uncertain of close_issue\nlet close_issue_descriptor (_:close_issue)=assert false\nlet close_issue_identity (_:close_issue)=assert false\nlet close_issue_cause (_:close_issue)=assert false\nlet close_issue_operation_error (_:close_issue)=assert false\n'+source
   substitutions=[('close_in channel','ReaderCloseFault.close_channel channel'),('Unix.close !descriptor','ReaderCloseFault.close_raw !descriptor'),('Unix.in_channel_of_descr !descriptor','ReaderCloseFault.channel_of_fd !descriptor')]
  for old,new in substitutions:
   assert source.count(old)==1,(variant,old);source=source.replace(old,new)
  # Recompile the suffix: other .cmx objects must not retain implementation
  # assumptions over the unmodified SemanticFile object.
  for module in modules[reader_end:]:
   name=module.removesuffix('.cmx')
   ml=build/(name+'.ml');mli=build/(name+'.mli')
   (work/(name+'.ml')).write_text(source) if name=='semanticFile' else shutil.copyfile(ml,work/ml.name)
   if mli.exists():shutil.copyfile(mli,work/mli.name)
   shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
   argv=[compiler,*flags]
   if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:
    argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
   call(argv+['-c',name+'.ml'])
  def link(participant,limit,binary):
   shutil.copyfile(HERE/participant,work/participant)
   selected=modules[:limit]
   argv=[compiler,*flags,'unix.cmxa','str.cmxa',str(work/'readerCloseFault.cmx')]
   argv += [str(work/name) if name in modules[reader_end:] else str(build/name) for name in selected]
   argv += [str(work/participant)]+[str(build/name) for name in native]+['-o',str(work/binary)]
   call(argv)
  link('reader_fault_test.ml',reader_end+1,'reader')
  link('reader_worker_test.ml',len(modules),'worker')
  if variant=='current':
   for mode in ('known','known-error','single','error','nested','install'):
    case=work/('reader-'+mode);case.mkdir(mode=0o700);call([str(work/'reader'),mode],cwd=case)
   for mode in ('single','install'):
    case=work/('worker-'+mode);case.mkdir(mode=0o700);call([str(work/'worker'),mode],cwd=case)
  else:
   for binary,mode,needle in (('reader','single','reader close after kernel close'),('worker','single','expected-reader-retained-reply')):
    case=work/(binary+'-'+mode);case.mkdir(mode=0o700)
    failed=call([str(work/binary),mode],cwd=case,expected=2)
    assert needle in failed.stderr
  records.append(dict(compiler=compiler,variant=variant,work=str(work),calls=calls,baseline_source_sha256=expected))
value=dict(state='READER_AND_WORKER_FIXED_CONTROLS_PASS',records=records,scope='Private real close-after-kernel-close plus fd-number reuse; current direct error chains and worker retention; old reader behavior rejected; fault processes settle at actual exit, not successful pool shutdown; no RSS/wholeFD/nativecontext qualification',sources={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('reader_fault.ml','reader_fault_test.ml','reader_worker_test.ml','reader_fault_run.py')})
with Path(a.report).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print('PASS real reader+worker retention, current and old behavior, stock/Ox')
