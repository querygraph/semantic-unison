"""Actual validation-tree opaque directory ownership; no transport or SDK."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',action='append',required=True);p.add_argument('--report',required=True);a=p.parse_args()
records=[]
for receipt in a.receipt:
 r=json.loads(Path(receipt).read_text());build=Path(r['workspace'])/'src';compiler=r['compiler'];version=r['compiler_version']
 for name,digest in r['source_sha256'].items():
  if name.startswith('src/'):assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
 text=(build/'Makefile.OCaml').read_text()
 def objects(name):
  body=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S).group(1)
  return body.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 modules=objects('OCAMLOBJS');modules=modules[:modules.index('candidateValidation.cmx')+1];native=objects('COBJS');start=modules.index('directoryOwner.cmx')
 work=Path(tempfile.mkdtemp(prefix='unison-directory-owner-'));work.chmod(0o700);calls=[]
 (work/'state').mkdir(mode=0o700);env=dict(os.environ,UNISON=str(work/'state'))
 includes=[work/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]+[build/d for d in ['', 'ubase','system','system/generic','lwt','lwt/generic']]
 for directory in includes[:6]:directory.mkdir(parents=True,exist_ok=True)
 flags=[v for directory in includes for v in ['-I',str(directory)]]+['-I','+unix','-I','+str']
 def call(argv,cwd=work,expected=0):
  c=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=60)
  calls.append(dict(argv=argv,returncode=c.returncode,stdout=c.stdout,stderr=c.stderr))
  if c.returncode!=expected:raise RuntimeError(json.dumps(calls))
  return c
 shutil.copyfile(HERE/'directory_fault.ml',work/'directoryFault.ml');call([compiler,*flags,'-c','directoryFault.ml'])
 sources={}
 for obj in modules[start:]:
  name=obj.removesuffix('.cmx');source=(build/(name+'.ml')).read_text()
  if name=='directoryOwner':
   for old,new in [('Unix.opendir path','DirectoryFault.open_directory path'),('Unix.closedir (Obj.obj owner.handle : Unix.dir_handle)','DirectoryFault.close (Obj.obj owner.handle : Unix.dir_handle)'),('Unix.readdir (Obj.obj owner.handle : Unix.dir_handle)','DirectoryFault.read (Obj.obj owner.handle : Unix.dir_handle)'),('try publish () with error ->','try DirectoryFault.before_publish ();publish () with error ->')]:
    assert source.count(old)==1;source=source.replace(old,new)
  if name=='system/system_generic':
   old='let owner=DirectoryOwner.prepare () in';assert source.count(old)==1
   source=source.replace(old,old+'\n  DirectoryFault.before_wrapper ();')
  sources[name]=source
  for ext in ['.mli','.cmi']:
   if (build/(name+ext)).exists():shutil.copyfile(build/(name+ext),work/(name+ext))
 def compile_module(name):
  argv=[compiler,*flags]
  if name+'.cmx: '+name+'.ml '+name+'.cmi semantic_mode_filter' in text:argv+=['-pp',str(build/'semantic_mode_filter')+' '+version]
  call(argv+['-c',name+'.ml'])
 def compile_suffix():
  for obj in modules[start:]:
   name=obj.removesuffix('.cmx');(work/(name+'.ml')).write_text(sources[name]);compile_module(name)
 def link(binary):
  shutil.copyfile(HERE/'directory_test.ml',work/'directory_test.ml')
  call([compiler,*flags,'unix.cmxa','str.cmxa']+[str(build/x) for x in modules[:start]]+['directoryFault.cmx']+[str(work/x) for x in modules[start:]]+['directory_test.ml']+[str(build/x) for x in native]+['-o',str(work/binary)])
 current_source_hashes={n:hashlib.sha256(s.encode()).hexdigest() for n,s in sources.items()}
 compile_suffix();link('fixed')
 # Compile the Windows wrapper/signature on this host; do not link/run Win32.
 shutil.copyfile(build/'system/system_win.ml',work/'system/system_win.ml')
 call([compiler,*flags,'-c','system/system_win.ml'])
 (work/'win_signature.ml').write_text('module Checked : System_intf.Core with type fspath = string = System_win\n')
 call([compiler,*flags,'-c','win_signature.ml'])
 monitor=(ROOT/'src/fsmonitor/windows/Makefile').read_text()
 assert monitor.index('directoryOwner.cmo')<monitor.index('system/system_generic.cmo')
 for mode in ['known','read-error','cancel','wrapper','open-error','publish','close-before','close-after','read-before','read-after','cancel-before','publish-after','legacy-close']:
  case=work/mode;case.mkdir(mode=0o700);call([str(work/'fixed'),mode],cwd=case)
  print(compiler,mode,'PASS',flush=True)
 # Removing the whole-tree guard must fail legacy (unadmitted manifest) borrowing.
 original=sources['candidateValidation'];old='SemanticRuntime.guard_ownership (fun () ->'
 assert original.count(old)==1
 (work/'candidateValidation.ml').write_text(original.replace(old,'(fun f -> f ()) (fun () ->'));compile_module('candidateValidation');link('bad-tree')
 case=work/'bad-tree-case';case.mkdir(mode=0o700);c=call([str(work/'bad-tree'),'legacy-close'],cwd=case,expected=2)
 assert 'DESIGNATED directory uncertainty escaped borrowed tree' in c.stderr
 # An ordinary close error is not a qualified ownership carrier.
 old='if owner.phase=Close_uncertain then raise owner.carrier';assert sources['directoryOwner'].count(old)==1
 sources['directoryOwner']=sources['directoryOwner'].replace(old,'if owner.phase=Close_uncertain then raise owner.close_error')
 compile_suffix();link('bad-close')
 case=work/'bad-close-case';case.mkdir(mode=0o700);c=call([str(work/'bad-close'),'read-after'],cwd=case,expected=2)
 assert 'DESIGNATED directory uncertainty escaped borrowed tree' in c.stderr
 records.append(dict(compiler=compiler,work=str(work),calls=calls,current_controlled_source_sha256=current_source_hashes,bad_close_source_sha256=hashlib.sha256(sources['directoryOwner'].encode()).hexdigest(),linked_object_sha256={x:hashlib.sha256((build/x).read_bytes()).hexdigest() for x in modules+native}))
with Path(a.report).open('x') as f:json.dump(dict(scope='Actual CandidateValidation tree lifetime and prepared System directory wrappers; private synthetic TOY0 files, original errors/cancellation, before/after native closedir failures, repeated opaque close and independent replacement handles; no numeric directory FD assumptions, SDK/transport/Photo or aggregate FD/RSS claim.',records=records,sources={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE/'directory_run.py',HERE/'directory_test.ml',HERE/'directory_fault.ml']}),f,indent=2)
print('PASS actual directory ownership stock/Ox')
