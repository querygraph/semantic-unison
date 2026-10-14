#!/usr/bin/env python3
"""Opt-in receiving manifest limits on private synthetic directories."""
import argparse,pathlib,subprocess,tempfile,importlib.util,hashlib,json,os,re
p=argparse.ArgumentParser();p.add_argument('--build',type=pathlib.Path,required=True);p.add_argument('--compiler',required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];src=a.build.resolve()/'src';w=pathlib.Path(tempfile.mkdtemp(prefix='unison-validation-tree-')).resolve();cases=[];commands=[]
spec=importlib.util.spec_from_file_location('paths',r/'tests/validation_paths/run.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
j=dict(schema='unison-validation-tree-structure/1',work=str(w),cases=cases,commands=commands,limits=['Entry/path accounting is not heap/RSS or full directory resource admission. Properties, symlink target bytes and SDK heaps are outside these structural limits.'],PhotoOrAdobeAccess=False)
try:
 (w/'test.ml').write_bytes((r/'tests/validation_tree_limits/test.ml').read_bytes())
 x=subprocess.run([a.compiler,'-I',str(src),str(src/'validationTreeBudget.cmx'),str(w/'test.ml'),'-o',str(w/'test')],capture_output=True,text=True);assert x.returncode==0,x.stdout+x.stderr
 x=subprocess.run([w/'test'],capture_output=True,text=True);assert x.returncode==0;xlog=w/'kernel.log';xlog.write_text(x.stdout+x.stderr);commands.append(dict(name='actual-object-kernel',exit=x.returncode,log=str(xlog),sha256=H(xlog)));print(x.stdout.strip(),flush=True)
 def objects(name):
  m=re.search(r'^'+name+r' = (.*?)(?=\n\n)',(src/'Makefile.OCaml').read_text(),re.M|re.S);assert m
  return m.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 def command(args,cwd,label,expected=0):
  x=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=60);log=cwd/(label+'.log');log.write_text(x.stdout+x.stderr);commands.append(dict(name=label,exit=x.returncode,log=str(log),sha256=H(log)));assert x.returncode==expected,log.read_text();return log.read_text()
 enum=w/'enumeration';enum.mkdir()
 for n in range(100):(enum/f'private-{n:03}').touch()
 original=(src/'candidateValidation.ml').read_text();anchor='  let directory = Fs.opendir path in\n';assert original.count(anchor)==1
 observed=original.replace(anchor,anchor+'''  let raw_read = directory.Fs.readdir and raw_close = directory.Fs.closedir in
  let directory = { Fs.readdir=(fun () -> let name = raw_read () in
      incr probe_reads; if !probe_reads = 3 then Abort.all (); name);
    closedir=(fun () -> incr probe_closes; raw_close ()) } in
''')
 observed='let probe_reads = ref 0\nlet probe_closes = ref 0\n'+observed+'''
let () =
  Abort.reset ();
  (try ignore (all_children (ValidationTreeBudget.create ~max_entries:0 ~max_path_bytes:0)
     ~prefix_bytes:0 (Fspath.canonize (Some Sys.argv.(1))));
     failwith "DESIGNATED directory enumeration ignored cancellation"
   with Util.Transient "Aborted by user request" ->
     assert (!probe_reads=3 && !probe_closes=1));
  Abort.reset (); print_endline "PASS enumeration cancellation: three reads, one native close"
'''
 mods=objects('OCAMLOBJS');before=mods[:mods.index('candidateValidation.cmx')]
 for mode in ['positive','removed-check']:
  d=w/mode;d.mkdir();data=observed
  if mode=='removed-check':
   marker='let rec read acc =\n    Abort.checkAll ();\n';assert data.count(marker)==1;data=data.replace(marker,'let rec read acc =\n')
  (d/'candidateValidation.ml').write_text(data);(d/'candidateValidation.mli').write_bytes((src/'candidateValidation.mli').read_bytes())
  inc=[d,src,src/'ubase',src/'system',src/'system/generic',src/'lwt',src/'lwt/generic'];flags=[str(v) for p in inc for v in ['-I',p]]+['-I','+unix','-I','+str']
  for suffix in ['mli','ml']:command([a.compiler,*flags,'-c',d/('candidateValidation.'+suffix)],d,'compile-'+suffix)
  binary=d/'enumerate';command([a.compiler,*flags,'unix.cmxa','str.cmxa',*[src/m for m in before],d/'candidateValidation.cmx',*[src/n for n in objects('COBJS')],'-o',binary],d,'link')
  output=command([binary,enum],d,'enumeration',0 if mode=='positive' else 2)
  assert ('PASS enumeration cancellation' if mode=='positive' else 'DESIGNATED directory enumeration ignored cancellation') in output
  j.setdefault('enumeration',{})[mode]=dict(binarySha256=H(binary),privateParticipantSha256=H(d/'candidateValidation.ml'),expectedExit=0 if mode=='positive' else 2)
  print('PASS enumeration',mode,flush=True)
 for name,entries,byte_limit,policy,success,hidden in [('exact-entries',7,0,'require',True,False),('entries-require',6,0,'require',False,False),('entries-warn',6,0,'warn',False,False),('path-require',0,1,'require',False,False),('path-warn',0,1,'warn',False,False),('negative-config',-1,0,'require',False,False),('post-helper-hidden-entry',7,0,'require',False,True)]:
  s=v.Session(w/name,str(src/'unison'));album=s.left/'album';album.mkdir();expected={}
  for n in range(6):
   data=b'private synthetic directory DNG gate '+bytes([n]);filename=f'item-{n}.dng';(album/filename).write_bytes(data);expected[filename]=data
  driver=s.drivers['server']
  if hidden:
   text=driver.read_text();anchor="if control['mode']=='mutate':";assert text.count(anchor)==1
   driver.write_text(text.replace(anchor,"(candidate.parent / '.helper-hidden').write_bytes(b'private helper-added sentinel')\n"+anchor))
  cfg=s.config('server');cfg.update(validationtreeentries=str(entries),validationtreepathbytes=str(byte_limit));(s.server_state/'endpoint.prf').write_text(''.join(f'{k} = {value}\n' for k,value in cfg.items()))
  driver.with_suffix('.control.json').write_text(json.dumps(dict(endpoint='server',build=cfg['adobevalidatorbuild'],mode='pass',destination=str(s.right/'album'),directory=True)))
  # This lower client limit must not override the receiving endpoint.
  log=s.sync(policy=policy,options=('-validationtreeentries','1'),success=success)
  assert {p.name:p.read_bytes() for p in album.iterdir()}==expected
  calls=s.calls()
  if success:
   assert len(calls)==6 and {p.name:p.read_bytes() for p in (s.right/'album').iterdir()}==expected
  else:
   assert not (s.right/'album').exists()
   assert not list(s.right.glob('.unison*')),'rejected staging remained resumable'
   assert len(calls)==(6 if hidden else 0),calls
   assert ('Validation tree limits must be nonnegative' if entries<0 else 'Validation tree exceeds validationtree') in log,log
  cases.append(dict(name=name,status='passed',helperCalls=len(calls),sourceUnchanged=True,destinationPublished=success,endpointLocal=True));print('PASS',name,flush=True)
 for f in ['validationTreeBudget.ml','validationTreeBudget.mli','candidateValidation.ml','Makefile.OCaml']:
  assert H(src/f)==H(r/'src'/f),('source drift',f)
 j.update(status='passed',binarySha256=H(src/'unison'),sources={f:H(r/f) for f in ['src/validationTreeBudget.ml','src/validationTreeBudget.mli','src/candidateValidation.ml','src/Makefile.OCaml','tests/validation_tree_limits/test.ml','tests/validation_tree_limits/run.py','tests/validation_paths/run.py']},compiledObjectPins={f:H(src/f) for f in ['validationTreeBudget.cmx','validationTreeBudget.cmi','candidateValidation.cmx']},scope='Actual loopback CLI receiving tree entry/path caps and helper-mutation failure on private synthetic inputs. No native Adobe/Lightroom operation.')
finally:
 j.setdefault('status','failed');a.receipt.write_text(json.dumps(j,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(j,indent=2)+'\n')
