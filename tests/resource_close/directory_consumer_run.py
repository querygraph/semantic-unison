"""Production-linked Os.childrenOf and Files.ls scoped ownership, no transport/SDK."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--report',required=True);p.add_argument('--participant',choices=['current','old-os','old-files'],default='current');a=p.parse_args()
r=json.loads(Path(a.receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
for name,digest in r['source_sha256'].items():
 if name.startswith('src/'):assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
text=(build/'Makefile.OCaml').read_text()
def objects(name):
 body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
 return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
modules=objects('OCAMLOBJS');modules=modules[:modules.index('files.cmx')+1];native=objects('COBJS');start=modules.index('directoryOwner.cmx')
work=Path(tempfile.mkdtemp(prefix='unison-directory-consumers-'));work.chmod(0o700);calls=[]
(work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
includes=[work/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]+[build/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]
for directory in includes[:6]:directory.mkdir(parents=True,exist_ok=True)
flags=[v for directory in includes for v in ['-I',str(directory)]]+['-I','+unix','-I','+str']
def call(argv,cwd=work,expected=0):
 c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=45)
 calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
 if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
 return c
shutil.copyfile(HERE/'directory_consumer_fault.ml',work/'directoryConsumerFault.ml');call([compiler,*flags,'-c','directoryConsumerFault.ml'])
controlled={};old_sources={}
for obj in modules[start:]:
 name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
 if a.participant=='old-'+name:
  source=subprocess.run(['git','show','4b9e7e67:src/'+name+'.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
  old_sources[name]=hashlib.sha256(source.encode()).hexdigest()
 if name=='directoryOwner':
  for old,new in [('Unix.opendir path','DirectoryConsumerFault.open_directory path'),('Unix.closedir (Obj.obj owner.handle : Unix.dir_handle)','DirectoryConsumerFault.close (Obj.obj owner.handle : Unix.dir_handle)'),('Unix.readdir (Obj.obj owner.handle : Unix.dir_handle)','DirectoryConsumerFault.read (Obj.obj owner.handle : Unix.dir_handle)'),('try publish () with error ->','try DirectoryConsumerFault.before_publish ();publish () with error ->')]:
   assert source.count(old)==1;source=source.replace(old,new)
 if name=='system/system_generic':
  old='let owner=DirectoryOwner.prepare () in';assert source.count(old)==1
  source=source.replace(old,old+'\n  DirectoryConsumerFault.before_wrapper ();')
 controlled[name]=source;(work/(name+'.ml')).write_text(source)
 for ext in ['.mli','.cmi']:
  if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
def compile_from(index):
 for obj in modules[index:]:
  name=obj.removesuffix('.cmx');argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
def link(binary):
 shutil.copyfile(HERE/'directory_consumer_test.ml',work/'directory_consumer_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['directoryConsumerFault.cmx']+[str(work/x) for x in modules[start:]]+['directory_consumer_test.ml']+[str(build/x) for x in native]+['-o',str(work/binary)])
compile_from(start);link('participant')
if a.participant=='current':
 for consumer in ['os','files']:
  for mode in ['known','missing','open-error','read-error','read-enoent','close-before','close-after','read-before','read-after','publish','publish-after','wrapper']:
   case=work/(consumer+'-'+mode);case.mkdir(mode=0o700);call([str(work/'participant'),consumer,mode],cwd=case)
  print(compiler,consumer,'12 current cases PASS',flush=True)
else:
 consumer=a.participant.removeprefix('old-')
 case=work/('historical-'+consumer);case.mkdir(mode=0o700)
 c=call([str(work/'participant'),consumer,'read-before'],cwd=case,expected=2)
 assert 'DESIGNATED directory consumer released uncertain borrower' in c.stderr
result=dict(scope='Actual Os.childrenOf and Files.ls with Runtime admission/I/O borrower: names and missing/read ENOENT distinction, original errors, prepared-publication and close failures, no retry; private tiny synthetic files only/no SDK/transport/Photo. Historical whole Os/Files module source rejects designated retained-borrower assertions.',participant=a.participant,compiler=compiler,work=str(work),calls=calls,controlled_source_sha256={n:hashlib.sha256(s.encode()).hexdigest() for n,s in controlled.items()},historical_source_sha256=old_sources,linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native},sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'directory_consumer_run.py',HERE/'directory_consumer_test.ml',HERE/'directory_consumer_fault.ml']})
with Path(a.report).open('x') as f:json.dump(result,f,indent=2)
print('PASS directory consumer participant',a.participant,compiler)
