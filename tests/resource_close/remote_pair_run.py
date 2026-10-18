"""Production-linked remote materializer pair close faults, no transport/SDK."""
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
 work=Path(tempfile.mkdtemp(prefix='unison-remote-pair-'));calls=[]
 (work/'state').mkdir(mode=0o700)
 environment=dict(os.environ,UNISON=str(work/'state'))
 flags=[x for d in [work,build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic'] for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work):
  c=subprocess.run(argv,cwd=cwd,env=environment,capture_output=True,text=True,timeout=30);calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode:raise RuntimeError(json.dumps(calls))
 shutil.copyfile(HERE/'remote_pair_fault.ml',work/'remotePairFault.ml');call([compiler,*flags,'-c','remotePairFault.ml'])
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='notificationPipe':
   for old,new in [('Unix.close t.read.fd','RemotePairFault.close_read t.read.fd'),('Unix.close t.write.fd','RemotePairFault.close_write t.write.fd')]:
    assert source.count(old)==1;source=source.replace(old,new)
  (work/(name+'.ml')).write_text(source);shutil.copyfile(build/(name+'.cmi'),work/(name+'.cmi'))
  if (build/(name+'.mli')).exists():shutil.copyfile(build/(name+'.mli'),work/(name+'.mli'))
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 source=(build/'semanticRemote.ml').read_text()
 substitutions=[('let supported connection =\n  SemanticFormats.peer_enabled () <> [] && Remote.connectionVersion connection >= 1 &&\n  Features.enabled transport','let supported _ = SemanticFormats.peer_enabled () <> [] && Features.enabled transport'),('~maxArgs:request_limit ~maxResult:response_limit args result make_plan','~maxArgs:request_limit ~maxResult:response_limit args result make_plan\nlet request_plan connection args = make_plan connection args')]
 for old,new in substitutions:assert source.count(old)==1;source=source.replace(old,new)
 assert source.count('try candidates.register candidate with error ->')==2
 source=source.replace('try candidates.register candidate with error ->','try RemotePairFault.before_register ();candidates.register candidate with error ->')
 for value in ['true','false']:
  old='try {basis;output;files;path;owned='+value+'}';assert source.count(old)==1
  source=source.replace(old,'try RemotePairFault.before_record ();{basis;output;files;path;owned='+value+'}')
 (work/'semanticRemoteForPair.ml').write_text(source);shutil.copyfile(HERE/'remote_pair_test.ml',work/'remote_pair_test.ml')
 call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['remotePairFault.cmx']+[str(work/x) for x in modules[start:]]+['semanticRemoteForPair.ml','remote_pair_test.ml']+[str(build/x) for x in native]+['-o',str(work/'fixed')])
 for kind,modes in [('bound',['known','read','write','both','before','callback','register','record']),('legacy',['known','both','register','record'])]:
  for mode in modes:
   case=work/(kind+'-'+mode);case.mkdir(mode=0o700);call([str(work/'fixed'),str(case),kind,mode])
 records.append(dict(compiler=compiler,work=str(work),calls=calls,controlled_source_sha256=hashlib.sha256(source.encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual remote materializer, in-process source planner/no transport, original8192B DNGs; pair error-before/after close+reuse, registry/record/callback failures; not full native parent/nonce/directory/RSS/FD qualification',records=records,sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'remote_pair_run.py',HERE/'remote_pair_test.ml',HERE/'remote_pair_fault.ml']}),f,indent=2)
print('PASS actual remote pair controls stock/Ox')
