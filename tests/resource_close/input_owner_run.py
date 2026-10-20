"""Prepared capture/scalar-merge input owners; private close fault injection."""
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
shutil.copyfile(HERE/'input_owner_fault.ml',work/'inputOwnerFault.ml');call([compiler,*flags,'-c','inputOwnerFault.ml'])
for obj in modules[start:]:
 name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
 if name=='notificationPipe':
  old='Unix.close t.read.fd';assert source.count(old)==1
  source=source.replace(old,'InputOwnerFault.close t.read.fd')
 (work/(name+'.ml')).write_text(source)
 for ext in ['.mli','.cmi']:
  if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
 argv=[compiler,*flags]
 if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
 call(argv+['-c',name+'.ml'])
source=(build/'semanticSync.ml').read_text()
old='NotificationPipe.adopt_read slot fd;';assert source.count(old)==1
source=source.replace(old,old+'InputOwnerFault.acquired index fd;')
(work/'semanticSyncForInputs.ml').write_text(source)
shutil.copyfile(HERE/'input_owner_test.ml',work/'input_owner_test.ml')
native_paths=[str(build/x) for x in native]
def link(binary):
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['inputOwnerFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticSyncForInputs.ml','input_owner_test.ml']+native_paths+['-o',str(work/binary)])
link('fixed')
for count in [1,4]:
 for mode in ['known','error','all','before-all','error-all']+['slot'+str(i) for i in range(count)]+['open'+str(i) for i in range(count)]:
  case=work/(str(count)+'-'+mode);case.mkdir(mode=0o700);(case/'input').write_bytes(b'private input sentinel')
  call([str(work/'fixed'),str(count),mode,str(case)])
  assert (case/'input').read_bytes()==b'private input sentinel'
 print(compiler,'inputs',count,'PASS',flush=True)
old='with NotificationPipe.Uncertain _ as error->retain_inputs owner error'
assert source.count(old)==1
(work/'semanticSyncForInputs.ml').write_text(source.replace(old,'with NotificationPipe.Uncertain _ -> ()'))
link('bad')
case=work/'bad-case';case.mkdir(mode=0o700);(case/'input').write_bytes(b'private input sentinel')
c=call([str(work/'bad'),'4','all',str(case)],expected=2)
assert 'DESIGNATED input uncertainty escaped' in c.stderr
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual prepared input owner inside production Runtime admission. 1/4 slots; open/error/individual/combined before-kernel and after-kernel recycled closes; no retries; independent closes; preserved original. Private helper participant, not full capture/cache/merge pipeline qualification.',compiler=compiler,work=str(work),calls=calls,source_sha256=hashlib.sha256(source.encode()).hexdigest()),f,indent=2)
print('PASS input owners and designated swallowing rejection',compiler)
