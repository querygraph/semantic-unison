"""Production-linked remote materializer tracked parent faults, no transport/SDK."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for name in ['semanticRemote.ml','semanticRemote.mli','notificationPipe.ml','notificationPipe.mli']:
  assert (ROOT/'src'/name).read_bytes()==(build/name).read_bytes(),name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRemote.cmx')];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-remote-parent-'));calls=[]
 (work/'state').mkdir(mode=0o700)
 environment=dict(os.environ,UNISON=str(work/'state'))
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,env=environment,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 shutil.copyfile(HERE/'remote_parent_fault.ml',work/'remoteParentFault.ml');call([compiler,*flags,'-c','remoteParentFault.ml'])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   for old,new in [('Unix.close t.read.fd','RemoteParentFault.close_read t.read.fd'),('Unix.close t.write.fd','RemoteParentFault.close_write t.write.fd')]:
    assert source.count(old)==1;source=source.replace(old,new)
  (work/(name+'.ml')).write_text(source);shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 source=(build/'semanticRemote.ml').read_text()
 substitutions=[('let supported connection =\n  SemanticFormats.peer_enabled () <> [] && Remote.connectionVersion connection >= 1 &&\n  Features.enabled transport','let supported _ = SemanticFormats.peer_enabled () <> [] && Features.enabled transport'),('~maxArgs:request_limit ~maxResult:response_limit args result make_plan','~maxArgs:request_limit ~maxResult:response_limit args result make_plan\nlet request_plan connection args = make_plan connection args')]
 for old,new in substitutions:assert source.count(old)==1;source=source.replace(old,new)
 old='let adopt ()=StagePublication.adopt_owned_tracked context publication.parent_handoff ~parent ~stage:output_fd in'
 new='let adopt ()= RemoteParentFault.before_native context publication.parent_handoff parent; StagePublication.adopt_owned_tracked context publication.parent_handoff ~parent ~stage:output_fd; RemoteParentFault.after_native () in'
 assert source.count(old)==1;source=source.replace(old,new)
 old='if publication.closing || publication.closed then begin'
 assert source.count(old)==1;source=source.replace(old,'if RemoteParentFault.interrupt () then publication.closing<-true; '+old)
 shutil.copyfile(build/'stagePublication_stubs.c',work/'stagePublication_stubs.c')
 fixture=(ROOT/'tests/stage_publication_owned/fixture.c').read_text()
 fixture=fixture.replace('static int owned_fixture_close(int fd)', 'static int parent_watch=-1,parent_watch_calls;\nCAMLprim value parent_fixture_watch(value fd) { parent_watch=Int_val(fd);parent_watch_calls=0;return Val_unit; }\nCAMLprim value parent_fixture_closes(value unit) { (void)unit;return Val_int(parent_watch_calls); }\nstatic int owned_fixture_close(int fd)')
 fixture=fixture.replace('int ordinal = ++calls;', 'int ordinal = ++calls; if(fd==parent_watch)parent_watch_calls++;')
 (work/'fixture.c').write_text(fixture);call([compiler,*flags,'-c','fixture.c'])
 native_paths=[str(work/'fixture.o') if x=='stagePublication_stubs.o' else str(build/x) for x in native]
 (work/'semanticRemoteForParent.ml').write_text(source);shutil.copyfile(HERE/'remote_parent_test.ml',work/'remote_parent_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['remoteParentFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticRemoteForParent.ml','remote_parent_test.ml']+native_paths+['-o',str(work/'fixed')])
 for mode in ['known','before-call','after-call','preentry','parent-before','parent-after','combined','interrupted']:
  case=work/mode;case.mkdir(mode=0o700);call([str(work/'fixed'),str(case),mode])
 # Deliberately broken consumer: a prepared acknowledgement is not transfer.
 # Recompile the full dependent suffix rather than mixing incompatible cmx CRCs.
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx')
  if name=='notificationPipe':
   bad=(work/'notificationPipe.ml').read_text()
   old='Some handoff -> StagePublication.parent_consumed handoff'
   assert bad.count(old)==1
   (work/'notificationPipe.ml').write_text(bad.replace(old,'Some _ -> true'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['remoteParentFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticRemoteForParent.ml','remote_parent_test.ml']+native_paths+['-o',str(work/'bad')])
 case=work/'bad-preentry';case.mkdir(mode=0o700)
 rejected=call([str(work/'bad'),str(case),'preentry'],expected=2)
 assert 'DESIGNATED unconsumed parent falsely transferred' in rejected.stderr
 records.append(dict(compiler=compiler,work=str(work),calls=calls,controlled_source_sha256=hashlib.sha256(source.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual remote caller/native consumption acknowledgement; in-process planner/no transport, original8192B DNGs; preentry and before/after call, close uncertainty/recycled numbers and interrupted acquisition. Not directory/RSS/aggregate FD qualification',records=records,sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'remote_parent_run.py',HERE/'remote_parent_test.ml',HERE/'remote_parent_fault.ml']}),f,indent=2)
print('PASS actual remote parent controls stock/Ox')
