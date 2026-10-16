#!/usr/bin/env python3
"""Link compiler-matched production merge objects; deterministic filesystem errors."""
import argparse,json,hashlib,os,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-receipt',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
p.add_argument('--expected-exit',type=int,default=0,choices=(0,2))
p.add_argument('--expected-fault-exit',type=int,default=0,choices=(0,2))
a=p.parse_args();root=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads(a.build_receipt.read_text());build=Path(b['workspace'])
assert b['complete'] and b['build_exit']==b['selftest_exit']==0
assert sha(b['compiler'])==b['compiler_sha256'] and sha(b['binary'])==b['binary_sha256']
# Negative controls deliberately use an older pinned snapshot; do not label it
# current. Positive tests require all production sources to match the checkout.
if a.expected_exit==a.expected_fault_exit==0:
 for name,digest in b['source_sha256'].items():
  if name.startswith('src/'):assert sha(root/name)==digest,name
work=Path(tempfile.mkdtemp(prefix='unison-merge-io-errors-')).resolve()
shutil.copyfile(root/'tests/merge_io_errors/probe.ml',work/'probe.ml')
objects=(build/'src/Makefile.OCaml').read_text().split('OCAMLOBJS =',1)[1].split('\n\n',1)[0].replace('\\','').split()
objects=[name.replace('$(SYSTEM)','generic') for name in objects if name!='$(WINOBJS)']
objects=objects[:objects.index('semanticSync.cmo')+1]
paths=[str(build/'src'/name.replace('.cmo','.cmx')) for name in objects]
flags=[v for name in ['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic'] for v in ['-I',str(build/name)]]
stubs=['pty.o','bytearray_stubs.o','hash_compat.o','props_xattr.o','props_acl.o','osxsupport.o','copy_stubs.o','nativeCopyRange_stubs.o','wholeFileClone_stubs.o','fileObservation_stubs.o','stagePublication_stubs.o','finalPublication_stubs.o','semanticHash_stubs.o','semanticFile_stubs.o','helperSupervisor_stubs.o']
command=[b['compiler'],*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa',*[str(build/'src'/s) for s in stubs],*paths,'probe.ml','-o','probe']
c=subprocess.run(command,cwd=work,capture_output=True,text=True,timeout=60)
(work/'compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stderr
for name in ('base','left','right','output'):(work/name).write_bytes(b'original private synthetic data')
(work/'directory').mkdir();(work/'state').mkdir(mode=0o700)
before={name:sha(work/name) for name in ('base','left','right','output')}
x=subprocess.run([str(work/'probe')],cwd=work,env=dict(os.environ,UNISON=str(work/'state'),UNISON_PRIVATE_MERGE_EXCEPTION='',UNISON_PRIVATE_MERGE_FAULT_PROBE=''),capture_output=True,text=True,timeout=30)
(work/'test.log').write_text(x.stdout+x.stderr)
assert before=={name:sha(work/name) for name in before}
assert x.returncode==a.expected_exit,(x.returncode,x.stdout,x.stderr)
# Keep production objects and source unchanged. A private replacement injects
# explicit exceptions only after all four merge descriptors have been acquired.
private=work/'private';private.mkdir()
source=(build/'src/semanticSync.ml').read_text()
anchor='      let before = Option.map Unix.LargeFile.fstat base_fd in'
assert source.count(anchor)==1
injection='''      (match Sys.getenv_opt "UNISON_PRIVATE_MERGE_EXCEPTION" with
       | Some "not-found" -> raise Not_found
       | Some "end-of-file" -> raise End_of_file
       | Some "out-of-memory" -> raise Out_of_memory
       | Some "break" -> raise Sys.Break
       | Some "failure" -> failwith "private merge failure"
       | Some "invalid-argument" -> invalid_arg "private merge argument"
       | Some "fatal" -> raise (Util.Fatal "private merge fatal")
       | Some "transient" -> raise (Util.Transient "private existing transient")
       | Some "unix" -> raise (Unix.Unix_error (Unix.EIO,"private","private"))
       | Some "sys-error" -> raise (Sys_error "private sys error")
       | Some "blocked-io" -> raise Sys_blocked_io
       | _ -> ());
'''
(private/'semanticSync.ml').write_text(source.replace(anchor,injection+anchor))
shutil.copyfile(build/'src/semanticSync.cmi',private/'semanticSync.cmi')
shutil.copyfile(work/'probe.ml',private/'probe.ml')
cc=subprocess.run([b['compiler'],*flags,'-c','semanticSync.ml'],cwd=private,capture_output=True,text=True,timeout=60)
(private/'module-compile.log').write_text(cc.stdout+cc.stderr);assert cc.returncode==0,cc.stderr
private_command=[str(private/'semanticSync.cmx') if value==paths[-1] else value for value in command]
cc=subprocess.run(private_command,cwd=private,capture_output=True,text=True,timeout=60)
(private/'compile.log').write_text(cc.stdout+cc.stderr);assert cc.returncode==0,cc.stderr
# Same original sentinels; independent runtime state. No actual OOM or disk fault.
for name in before:shutil.copyfile(work/name,private/name)
(private/'directory').mkdir();(private/'state').mkdir(mode=0o700)
fault=subprocess.run([str(private/'probe')],cwd=private,
 env=dict(os.environ,UNISON=str(private/'state'),UNISON_PRIVATE_MERGE_EXCEPTION='',UNISON_PRIVATE_MERGE_FAULT_PROBE='1'),capture_output=True,text=True,timeout=30)
(private/'test.log').write_text(fault.stdout+fault.stderr)
assert fault.returncode==a.expected_fault_exit,(fault.returncode,fault.stdout,fault.stderr)
assert before=={name:sha(private/name) for name in before}
fault_record={'probe_exit':fault.returncode,'expected_exit':a.expected_fault_exit,
 'stdout':fault.stdout,'stderr':fault.stderr,'source_sha256':sha(private/'semanticSync.ml'),
 'probe_sha256':sha(private/'probe'),'log_sha256':sha(private/'test.log'),
 'scope':'Private replacement of actual merge module injects11explicit exceptions after four acquired descriptors; no production hooks/physical OOM/EIO.'}
result={'schema':'unison-merge-io-errors/1','workspace':str(work),'source_pins':{name:sha(root/name) for name in ['tests/merge_io_errors/probe.ml','tests/merge_io_errors/run.py']},'production_merge_sha256':sha(build/'src/semanticSync.ml'),'build_receipt_sha256':sha(a.build_receipt),'build_receipt':str(a.build_receipt),'compiler':b['compiler'],'compile_command':command,'compile_exit':c.returncode,'probe_exit':x.returncode,'expected_exit':a.expected_exit,'stdout':x.stdout,'stderr':x.stderr,'probe_sha256':sha(work/'probe'),'probe_log_sha256':sha(work/'test.log'),'private_exception_probe':fault_record,'scope':'Actual compiler-matched production merge objects plus explicitly private exception injection; settled FD/transaction/CPU/I/O/worker ledgers; no SDK or photos.'}
a.report.write_text(json.dumps(result,indent=2)+'\n');print(x.stdout,end='');print(fault.stdout,end='');print('Report:',a.report)
