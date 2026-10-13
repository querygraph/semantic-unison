#!/usr/bin/env python3
"""Private candidate pre-inspection EIO through actual warn-mode receive gates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_positional_sync import run_owned
from dng_profile_v1_remote import fixture,objects

DRIVER='''#!/usr/bin/python3
import hashlib,json,pathlib,sys
here=pathlib.Path(__file__)
data=pathlib.Path(sys.argv[-1]).read_bytes()
with here.with_suffix('.calls').open('a') as output:
 output.write(json.dumps({'candidate':sys.argv[-1],'sha256':hashlib.sha256(data).hexdigest()})+'\\n')
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+hashlib.sha256(data).hexdigest())
print('candidate-size '+str(len(data)))
print('driver-build synthetic-inspection-fault-1')
print('structure valid')
print('decode success')
print('raw-digest missing')
print('errors 0')
print('warnings 0')
print('END')
'''

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def patch(source,trace):
 anchor='let snapshot pool cancellation path =\n'
 assert source.count(anchor)==1
 injection='''  (* Private test only: initial Identify is complete before this callback. *)
  if Filename.basename path <> "synthetic-driver.py" then begin
    let text = path ^ "\\n" in
    let channel = open_out_gen [Open_wronly;Open_creat;Open_append;Open_binary] 0o600 TRACE in
    (try output_string channel text; close_out channel
     with error -> close_out_noerr channel; raise error);
    fail (Unix.Unix_error (Unix.EIO,"private candidate pre-inspection",path))
  end else
'''.replace('TRACE',json.dumps(str(trace)))
 return source.replace(anchor,anchor+injection)

class Run:
 def __init__(self,work): self.work=work;self.commands=[]
 def command(self,name,command,environment,cwd=None,success=True):
  result=run_owned(command,environment,120)
  log=self.work/(name+'.log')
  text=result['capture']['stdout']['text']+result['capture']['stderr']['text']
  log.write_text(text)
  self.commands.append({'name':name,'result':result,'log':str(log),'log_sha256':sha(log)})
  assert not result['timed_out'] and all(not c['truncated'] for c in result['capture'].values()),log
  assert result['client_cleanup']['reaped'] and result['client_cleanup']['group_cleanup_before_leader_reap'],log
  assert (result['exit']==0)==success,(name,text)
  return text

def exercise(run,normal,faulty,trace,remote,decoder):
 case=run.work/('remote' if remote else 'local');case.mkdir()
 left,right,state,receiver=(case/n for n in ('left','right','state','receiver'))
 for path in (left,right,state,receiver):path.mkdir()
 driver=case/'synthetic-driver.py';driver.write_text(DRIVER);driver.chmod(0o700)
 config={'adobevalidator':str(driver),'adobevalidatorhash':sha(driver),
         'adobevalidatorbuild':'synthetic-inspection-fault-1','adobevalidatorthreads':'1','adobevalidatetimeout':'30',
         'semanticvolumejobs':'1'}
 (receiver/'endpoint.prf').write_text(''.join(key+' = '+value+'\n' for key,value in config.items()))
 launcher=case/'loopback.py'
 launcher.write_text('#!/usr/bin/env python3\nimport os,sys\na=sys.argv[1:]\ni=next(i for i,s in enumerate(a) if os.path.basename(s)=="unison")\n'
                     'os.environ["UNISON"]='+repr(str(receiver))+'\nos.execv(a[i],a[i:])\n')
 launcher.chmod(0o700)
 source,target=left/'renamed.bin',right/'renamed.bin'
 old,new=fixture(),fixture(b'two')
 source.write_bytes(old)
 options=[str(left),'ssh://localhost/'+str(right) if remote else str(right),
          '-batch','-auto','-fastcheck','false','-times','-clone','off','-maxthreads','1',
          '-semanticworkers','2','-semanticmaxinflight','2','-adobevalidate','warn']
 if not remote:options += [word for key,value in config.items() for word in ('-'+key,value)]
 environment=dict(os.environ,UNISON=str(state))
 def sync(binary,phase,success=True):
  command=[str(binary)]+options
  if remote:command += ['-sshcmd',str(launcher),'-servercmd',str(binary)]
  return run.command(('remote' if remote else 'local')+'-'+phase,command,environment,success=success)
 def count():
  calls=driver.with_suffix('.calls')
  return len(calls.read_text().splitlines()) if calls.exists() else 0
 def inventory():
  assert {p.name for p in left.iterdir()}=={'renamed.bin'}
  assert {p.name for p in right.iterdir()}=={'renamed.bin'}
 def archives(phase):
  saved=case/('archives-'+phase);saved.mkdir()
  result={}
  for config_root in (state,receiver):
   for path in config_root.glob('ar*'):
    if len(path.name)==34 and all(c in '0123456789abcdef' for c in path.name[2:]):
     retained=saved/(config_root.name+'-'+path.name);retained.write_bytes(path.read_bytes())
     text=run.command(('remote' if remote else 'local')+'-'+phase+'-'+path.name,
                      [str(decoder),str(retained)],environment)
     node=json.loads(text)
     assert node['filename']=='renamed.bin' and hashlib.md5(old).hexdigest() in node['fullfingerprint'],node
     assert node['archive_root'].endswith(str(left)) or node['archive_root'].endswith(str(right)),node
     assert path.name=='ar'+hashlib.md5((node['archive_root']+';'+node['peer_roots']+';23').encode()).hexdigest(),node
     node['role']='receiver' if node['archive_root'].endswith(str(right)) else 'source'
     result[str(path)]={'raw_sha256':sha(path),'retained':str(retained),'node':node}
  assert len(result)>=2,result
  assert {'source','receiver'}=={entry['node']['role'] for entry in result.values()}
  return result
 sync(normal,'baseline');assert target.read_bytes()==old and count()==1;inventory()
 inode=target.stat().st_ino
 before=archives('before')
 source.write_bytes(new);source_identity=(source.stat().st_dev,source.stat().st_ino)
 previous=trace.read_text().splitlines() if trace.exists() else []
 output=sync(faulty,'warn-failure',False)
 assert 'Adobe DNG validation rejected' in output and 'private candidate pre-inspection' in output,output
 assert count()==1,'inspection failure invoked helper'
 assert target.read_bytes()==old and target.stat().st_ino==inode
 assert source.read_bytes()==new and (source.stat().st_dev,source.stat().st_ino)==source_identity
 inventory();after=archives('after-failure')
 assert set(after)==set(before)
 assert all(after[path]['node']['fullfingerprint']==before[path]['node']['fullfingerprint'] for path in before), 'typed file fingerprint advanced after rejection'
 calls=trace.read_text().splitlines()[len(previous):]
 assert len(calls)==1 and Path(calls[0]).parent==right and not Path(calls[0]).exists(),calls
 sync(normal,'retry');assert target.read_bytes()==new and count()==2;inventory()
 inodes=(source.stat().st_ino,target.stat().st_ino)
 sync(normal,'noop');assert inodes==(source.stat().st_ino,target.stat().st_ino) and count()==2;inventory()
 return {'remote':remote,'initial_identify_completed_before_injected_inspect':True,
         'warn_rejected_before_helper':True,'failed_live_bytes_and_inode_preserved':True,
         'typed_archive_file_fingerprints_preserved':True,'archives_before':before,'archives_after_failure':after,
         'discarded_candidate':calls[0],
         'exact_retry':True,'noop_inodes_stable':True,'driver_sha256':sha(driver)}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--build',type=Path,required=True);parser.add_argument('--ocamlopt',required=True)
 parser.add_argument('--report',type=Path)
 args=parser.parse_args();snapshot=args.build.resolve();compiler=Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
 sources=[os.fsdecode(raw) for raw in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0')
          if raw and os.fsdecode(raw).startswith('src/') and os.fsdecode(raw)!='src/.depend']
 manifest={name:sha(ROOT/name) for name in sources if (ROOT/name).is_file()}
 assert all(sha(snapshot/name)==digest for name,digest in manifest.items()),'refresh frozen snapshot'
 work=Path(tempfile.mkdtemp(prefix='unison-validation-inspection-fault-',dir='/private/tmp'));print('work',work,flush=True)
 run=Run(work);private=work/'build';shutil.copytree(snapshot,private)
 shutil.copy2(__file__,work/'runner.py');trace=work/'inspection-trace.txt'
 original=(private/'src/candidateValidation.ml').read_text();mutated=patch(original,trace)
 (work/'candidateValidation.original.ml').write_text(original)
 (private/'src/candidateValidation.ml').write_text(mutated)
 environment=dict(os.environ,PATH=str(compiler.parent)+os.pathsep+os.environ.get('PATH',''))
 for name in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):environment.pop(name,None)
 command=['make','-C',str(private/'src'),'tui','-j2','NATIVE=true','TOOL_PREFIX='+str(compiler.parent)+'/']
 status='failed';cases=[];decoder_inputs=[]
 try:
  run.command('private-relink',command,environment)
  build=snapshot/'src';makefile=(build/'Makefile.OCaml').read_text()
  modules=objects(makefile,'OCAMLOBJS');modules=modules[:modules.index('update.cmx')+1]
  decoder_inputs=[build/obj for obj in modules+objects(makefile,'COBJS')]
  decoder_inputs += [path.with_suffix('.o') for path in decoder_inputs if path.suffix=='.cmx']
  includes=[build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic']
  flags=[value for path in includes for value in ('-I',str(path))]+['-I','+unix','-I','+str']
  decoder_source=work/'archive_node.ml';decoder_source.write_bytes((Path(__file__).parent/'archive_node.ml').read_bytes())
  decoder=work/'archive-node'
  decode_command=[str(compiler)]+flags+['unix.cmxa','str.cmxa']+[str(build/obj) for obj in modules]
  decode_command += [str(decoder_source)]+[str(build/obj) for obj in objects(makefile,'COBJS')]+['-o',str(decoder)]
  run.command('archive-decoder-link',decode_command,environment)
  cases=[exercise(run,snapshot/'src/unison',private/'src/unison',trace,remote,decoder) for remote in (False,True)]
  status='passed'
 finally:
  inputs=[ROOT/'tests/test_positional_sync.py',ROOT/'tests/dng_profile_v1_remote.py',ROOT/'bench/sync/ownership.py',ROOT/'bench/sync/measure.py']
  pins={str(path):sha(path) for path in inputs}
  pins.update({str(path):sha(path) for path in decoder_inputs})
  for path in (work/'runner.py',work/'candidateValidation.original.ml',private/'src/candidateValidation.ml',
               private/'src/candidateValidation.cmx',private/'src/candidateValidation.o',private/'src/unison',snapshot/'src/unison',compiler,
               work/'archive_node.ml',work/'archive-node'):
   if path.is_file():pins[str(path)]=sha(path)
  result={'status':status,'work':str(work),'production_manifest':manifest,'snapshot':str(snapshot),
          'compiler':str(compiler),'one_file_private_patch':'candidateValidation.snapshot candidate-EIO before SDK invocation',
          'pins':pins,'trace':None if not trace.exists() else {'path':str(trace),'sha256':sha(trace)},
          'cases':cases,'commands':run.commands,'limits':['synthetic driver and DNG bytes only; no Adobe/Photo',
          'production format23 codec binds renamed.bin full fingerprint; raw archive container metadata may change',
          'worker/process/borrower counters are not inferred from client exit; owned group cleanup and leader wait4 only']}
  target=args.report.resolve() if args.report else work/'qualification.json';target.write_text(json.dumps(result,indent=2)+'\n')
  print('receipt',target,'status',status,flush=True)

if __name__=='__main__':main()
