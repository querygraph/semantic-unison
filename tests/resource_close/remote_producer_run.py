"""Actual remote producer borrowing, with real nested file/directory carriers."""
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
modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRemote.cmx')];native=objects('COBJS');start=modules.index('directoryOwner.cmx')
work=Path(tempfile.mkdtemp(prefix='unison-remote-producer-'));work.chmod(0o700);calls=[]
(work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
includes=[work/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]+[build/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]
for directory in includes[:6]:directory.mkdir(parents=True,exist_ok=True)
flags=[v for directory in includes for v in ['-I',str(directory)]]+['-I','+unix','-I','+str']
def call(argv,cwd=work,expected=0):
 c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
 if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
 return c
shutil.copyfile(HERE/'remote_producer_fault.ml',work/'remoteProducerFault.ml');call([compiler,*flags,'-c','remoteProducerFault.ml'])
for obj in modules[start:]:
 name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
 if name=='directoryOwner':
  old='Unix.closedir (Obj.obj owner.handle : Unix.dir_handle)';assert source.count(old)==1
  source=source.replace(old,'RemoteProducerFault.close (Obj.obj owner.handle : Unix.dir_handle)')
 (work/(name+'.ml')).write_text(source)
 for ext in ['.mli','.cmi']:
  if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
 argv=[compiler,*flags]
 if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
 call(argv+['-c',name+'.ml'])
def controlled(source):
 changes=[('let supported connection =\n  SemanticFormats.peer_enabled () <> [] && Remote.connectionVersion connection >= 1 &&\n  Features.enabled transport','let supported _ = SemanticFormats.peer_enabled () <> [] && Features.enabled transport'),('~maxArgs:request_limit ~maxResult:response_limit args result make_plan','~maxArgs:request_limit ~maxResult:response_limit args result make_plan\nlet request_plan connection args = make_plan connection args')]
 for old,new in changes:assert source.count(old)==1;source=source.replace(old,new)
 return source
shutil.copyfile(HERE/'remote_producer_test.ml',work/'remote_producer_test.ml')
def link(source,binary):
 (work/'semanticRemoteForProducer.ml').write_text(source)
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['remoteProducerFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticRemoteForProducer.ml','remote_producer_test.ml']+[str(build/x) for x in native]+['-o',str(work/binary)])
current=controlled((build/'semanticRemote.ml').read_text());(work/'current_remote.ml').write_text(current);link(current,'fixed')
for phase in ['normal','cancel','nested-file','nested-dir']:
 case=work/phase;case.mkdir(mode=0o700);call([str(work/'fixed'),str(case),phase])
old=subprocess.run(['git','show','65de6192:src/semanticRemote.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
(work/'historical_remote.ml').write_text(old);link(controlled(old),'old')
case=work/'old-cancel';case.mkdir(mode=0o700);c=call([str(work/'old'),str(case),'cancel'],expected=2)
assert 'DESIGNATED remote active producer closed' in c.stderr
marker=' | DirectoryOwner.Uncertain _';assert current.count(marker)==1
bad=current.replace(marker,'');(work/'missing-directory-classifier.ml').write_text(bad);link(bad,'bad-classifier')
case=work/'bad-directory';case.mkdir(mode=0o700);c=call([str(work/'bad-classifier'),str(case),'nested-dir'],expected=2)
assert 'DESIGNATED remote producer lost its stage borrower' in c.stderr
result=dict(scope='Actual remote receiver/materializer with in-process source planner: active callback cleanup, actual EBADF file carrier, after-kernel/EIO directory carrier, raw pair/native name and transaction retention. Four current+two designated old/missing-classifier rejections. Generated8192B DNGs only/no actual transport/SDK/Photo or aggregate resource qualification.',compiler=compiler,work=str(work),calls=calls,current_controlled_sha256=hashlib.sha256(current.encode()).hexdigest(),historical_source_sha256=hashlib.sha256(old.encode()).hexdigest(),missing_classifier_sha256=hashlib.sha256(bad.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native},sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'remote_producer_run.py',HERE/'remote_producer_test.ml',HERE/'remote_producer_fault.ml']})
with Path(a.report).open('x') as f:json.dump(result,f,indent=2)
print('PASS remote producer current and designated regressions',compiler)
