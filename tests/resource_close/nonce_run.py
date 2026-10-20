"""Extract exact production nonce body and link actual owner admission objects."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
def extract(text):return text[text.index('let nonce () ='):text.index('let try_transfer_internal')]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for name in ['semanticRemote.ml','notificationPipe.ml','semanticRuntime.ml']:assert (ROOT/'src'/name).read_bytes()==(build/name).read_bytes(),name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('semanticRuntime.cmx')+1];native=objects('COBJS');start=modules.index('notificationPipe.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-nonce-owner-'));calls=[];(work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 shutil.copyfile(HERE/'nonce_fault.ml',work/'nonceFault.ml');call([compiler,*flags,'-c','nonceFault.ml'])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   old='Unix.close t.read.fd';assert source.count(old)==1;source=source.replace(old,'NonceFault.close t.read.fd')
  (work/(name+'.ml')).write_text(source);shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 current=extract((build/'semanticRemote.ml').read_text());assert current.count('Unix.read fd b off (32-off)')==1
 (work/'nonceFixture.ml').write_text(current.replace('Unix.read fd b off (32-off)','NonceFault.read fd b off (32-off)'))
 shutil.copyfile(HERE/'nonce_test.ml',work/'nonce_test.ml')
 link=[compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['nonceFault.cmx']+[str(work/x) for x in modules[start:]]+['nonceFixture.ml','nonce_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')]
 call(link)
 for mode in ['known','interrupt','empty','read-error','before','after','read-close']:call([str(work/'fixed'),mode])
 baseline=work/'baseline';baseline.mkdir()
 original=extract(subprocess.run(['git','show','1663ec98:src/semanticRemote.ml'],cwd=ROOT,capture_output=True,text=True,check=True).stdout)
 old=original.replace('Unix.read fd b off (32-off)','NonceFault.read fd b off (32-off)');assert old.count('Unix.close fd')==1
 (baseline/'nonceFixture.ml').write_text(old.replace('Unix.close fd','NonceFault.close fd'));shutil.copyfile(HERE/'nonce_test.ml',baseline/'nonce_test.ml')
 oldlink=[str(work/x) if x=='nonceFault.cmx' else x for x in link];oldlink[1:1]=['-I',str(baseline)];oldlink[-1]=str(baseline/'old')
 call(oldlink,cwd=baseline)
 for mode in ['before','after','read-close']:
  c=call([str(baseline/'old'),mode],expected=2);assert 'DESIGNATED uncertain nonce released caller' in c.stderr
 records.append(dict(compiler=compiler,work=str(work),calls=calls,nonce_sha256=hashlib.sha256(current.encode()).hexdigest(),old_nonce_sha256=hashlib.sha256(original.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Exact extracted production nonce with read/close substitutions, actual Runtime/admission/ledger; not complete remote/parent/directory/RSS qualification',records=records,sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'nonce_run.py',HERE/'nonce_test.ml',HERE/'nonce_fault.ml']}),f,indent=2)
print('PASS nonce owner fixed controls and old behavior rejections stock/Ox')
