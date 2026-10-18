"""Actual local async semantic owners: raw pair/source, native parent and producer."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--report',required=True);a=p.parse_args()
r=json.loads(Path(a.receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
for name,digest in r['source_sha256'].items():
 if name.startswith('src/'):assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
text=(build/'Makefile.OCaml').read_text()
def objects(name):
 body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
 return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticSync.cmx')];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
work=Path(tempfile.mkdtemp(prefix='unison-local-owner-'));work.chmod(0o700);calls=[]
(work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
flags=[v for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for v in ['-I',str(d)]]+['-I','+unix','-I','+str']
def call(argv,cwd=work,expected=0):
 c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
 if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
 return c
shutil.copyfile(HERE/'local_owner_fault.ml',work/'localOwnerFault.ml');call([compiler,*flags,'-c','localOwnerFault.ml'])
for obj in modules[start:]:
 name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
 if name=='notificationPipe':
  for old,new in [('Unix.close t.read.fd','LocalOwnerFault.close_read t.read.fd'),('Unix.close t.write.fd','LocalOwnerFault.close_write t.write.fd')]:
   assert source.count(old)==1;source=source.replace(old,new)
 (work/(name+'.ml')).write_text(source)
 for ext in ['.mli','.cmi']:
  if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
 argv=[compiler,*flags]
 if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
 call(argv+['-c',name+'.ml'])
source=(build/'semanticSync.ml').read_text()
replacements=[('let prepare_transaction path on_uncertain =','let prepare_transaction path on_uncertain =\n  LocalOwnerFault.prepare ();'),('transaction.owned<-name_owned','transaction.owned<-name_owned;LocalOwnerFault.pair basis output;\n  if LocalOwnerFault.interrupt_pair () then transaction.abandoned<-true'),('try transaction_resources.register transaction with error ->','try LocalOwnerFault.before_register ();transaction_resources.register transaction with error ->'),('let fd=Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in','LocalOwnerFault.before_source ();\n  let fd=Fs.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in'),('NotificationPipe.adopt_read transaction.source_owner fd;','NotificationPipe.adopt_read transaction.source_owner fd;LocalOwnerFault.source_open fd;\n  if LocalOwnerFault.interrupt_source () then transaction.abandoned<-true;'),('let adopt ()=StagePublication.adopt_owned_tracked context publication.parent_handoff ~parent ~stage:output_fd in','let adopt ()=LocalOwnerFault.before_native context publication.parent_handoff parent;\n            StagePublication.adopt_owned_tracked context publication.parent_handoff ~parent ~stage:output_fd;LocalOwnerFault.after_native () in')]
for old,new in replacements:assert source.count(old)==1;source=source.replace(old,new)
(work/'semanticSyncForOwner.ml').write_text(source);shutil.copyfile(HERE/'local_owner_test.ml',work/'local_owner_test.ml')
shutil.copyfile(build/'stagePublication_stubs.c',work/'stagePublication_stubs.c')
fixture=(ROOT/'tests/stage_publication_owned/fixture.c').read_text()
fixture=fixture.replace('static int owned_fixture_close(int fd)','static int parent_watch=-1,parent_watch_calls;\nCAMLprim value parent_fixture_watch(value fd) { parent_watch=Int_val(fd);parent_watch_calls=0;return Val_unit; }\nCAMLprim value parent_fixture_closes(value unit) { (void)unit;return Val_int(parent_watch_calls); }\nstatic int owned_fixture_close(int fd)').replace('int ordinal = ++calls;','int ordinal = ++calls; if(fd==parent_watch)parent_watch_calls++;')
(work/'fixture.c').write_text(fixture);call([compiler,*flags,'-c','fixture.c'])
native_paths=[str(work/'fixture.o') if x=='stagePublication_stubs.o' else str(build/x) for x in native]
def link(binary):
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['localOwnerFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticSyncForOwner.ml','local_owner_test.ml']+native_paths+['-o',str(work/binary)])
link('fixed')
common=['known','prepare','register','open-source','read','write','source','all','before-read','before-source','register-close','open-source-close','interrupt-pair','interrupt-source']
for kind,modes in [('legacy',common),('bound',common+['callback','callback-close','callback-cancel','before-native','after-native','parent-before','parent-after','preentry','borrowed-unknown'])]:
 for mode in modes:
  case=work/(kind+'-'+mode);case.mkdir(mode=0o700);call([str(work/'fixed'),str(case),kind,mode])
 print(compiler,kind,len(modes),'cases PASS',flush=True)
# A close-swallowing participant must not pass through as a normal completed transfer.
old='with NotificationPipe.Uncertain _ as error -> retain_transaction transaction error'
assert source.count(old)==2
bad=source.replace(old,'with NotificationPipe.Uncertain _ -> ()')
(work/'semanticSyncForOwner.ml').write_text(bad);link('bad')
case=work/'bad-close-swallow';case.mkdir(mode=0o700)
c=call([str(work/'bad'),str(case),'legacy','all'],expected=2)
assert 'DESIGNATED local descriptor uncertainty escaped' in c.stderr
result=dict(scope='Actual SemanticSync async workers/APFS/SDE and producer, generated8192B DNGs. Prepared pair/source/parent, known/errors/registration/interruption/no retries and callback connection cleanup. No transport/SDK/Photo or aggregate RSS/FD proof; synchronous reference/capture/scalar merge remain separate.',compiler=compiler,work=str(work),calls=calls,current_controlled_source_sha256=hashlib.sha256(source.encode()).hexdigest(),bad_controlled_source_sha256=hashlib.sha256(bad.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native},sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'local_owner_run.py',HERE/'local_owner_fault.ml',HERE/'local_owner_test.ml']})
with Path(a.report).open('x') as f:json.dump(result,f,indent=2)
print('PASS local async owned close and designated swallowing rejection',compiler)
