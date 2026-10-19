"""Original finite validation-policy controls, stock/Ox; standing Unison8, no Photo/SDK IO."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import close_unstarted
from shared_process_owner import retain_after_record
from shared_child import start
from final_profile_owner import closed,sha
from final_clone_interruption_owner import can_close_failed_prefix
from sdk_merge_receiving.store import Store
from cached_benchmark.contract import read_bytes
from sdk_fixture_build_owner import tool_sha


def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);a=p.parse_args()
 work=Path(a.workspace)
 if work.parent!=Path('/private/tmp') or not work.name.startswith('u-validation-policy-'):raise ValueError('fresh baseline namespace required')
 compilers=[('stock','/Users/alexy/.opam/default/bin/ocamlopt','f183dd4bd5c655b56fb87da2d39e01b843a730b6252e8b92fc6989e6f07cfacf'),('ox','/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt','e02b8590aa2c05948203befbfef22253282b1799d92f9a32c3878681f1b3e166')]
 sources=['src/lwt/lwt.mli','src/lwt/lwt.ml','src/lwt/pqueue.mli','src/lwt/pqueue.ml','src/lwt/generic/lwt_unix_impl.ml','src/lwt/lwt_unix.mli','src/lwt/lwt_unix.ml','src/borrowedWork.mli','src/borrowedWork.ml','src/helperSupervisor.mli','src/helperSupervisor.ml','src/dngValidation.mli','src/dngValidation.ml','src/helperSupervisor_stubs.c','tests/final_validation_policy/finding_helper.ml','tests/final_validation_policy/findings.ml']
 source_pins={name:sha(ROOT/name) for name in sources}
 for _,invocation,digest in compilers:
  if tool_sha(Path(invocation).resolve())!=digest:raise ValueError('compiler changed')
 policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
 if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('standing policy changed')
 work.mkdir(mode=0o700);st=work.stat();store=Store(str(work),dict(device=st.st_dev,inode=st.st_ino));cpu=None;active=attempted=False;calls=[]
 try:
  cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
  if cpu is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
  env=dict(os.environ,PATH='/Users/alexy/.opam/default/bin:'+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
  for k in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(k,None)
  store.write('START.json',dict(owner_pid=os.getpid(),workspace=str(work),source_pins=source_pins,CPU=list(range(8)),EX_IO=False,SDK=False,compiler_jobs=1))
  print('BASELINE_START',os.getpid(),str(work),flush=True)
  def run(argv,cwd,seconds):
   nonlocal active,attempted
   active=attempted=True;old=os.getcwd()
   try:
    os.chdir(cwd);child=start(argv,env,pass_fds=cpu.fds,capture_limit=262144)
   finally:os.chdir(old)
   out=child.finish(time.monotonic()+seconds);store.write('call-%02d.json'%len(calls),out);calls.append(out);closed(out,out['returncode']);active=False
   print('BASELINE_CHILD',len(calls),out['returncode'],flush=True)
   if out['returncode']:raise ValueError('baseline child failed: '+repr(argv)+'\n'+out['stdout'][-3000:]+out['stderr'][-3000:])
   return out
  from final_clone_stage_owner import write_bytes
  programs=[]
  for label,invocation,digest in compilers:
   tree=work/label;tree.mkdir();env['PATH']=str(Path(invocation).parent)+':'+os.environ['PATH']
   for name in sources:write_bytes(tree/Path(name).name,read_bytes(str(ROOT/name),1048576))
   for name in sources[:-2]:run([invocation,'-I','+unix','-c',Path(name).name],tree,60)
   run([invocation,'-I','+unix','unix.cmxa','finding_helper.ml','-o','finding_helper'],tree,60)
   run([invocation,'-I','+unix','unix.cmxa','lwt.cmx','pqueue.cmx','lwt_unix_impl.cmx','lwt_unix.cmx','helperSupervisor_stubs.o','borrowedWork.cmx','helperSupervisor.cmx','dngValidation.cmx','findings.ml','-o','findings'],tree,60)
   out=run([str(tree/'findings'),str(tree/'finding_helper')],tree,120)
   lines=out['stdout'].splitlines()
   if len(lines)!=39 or len(set(lines))!=39 or lines[-1]!='PASS off no-inspection no-execution; 38 finding/policy cases':raise ValueError('finding matrix incomplete')
   for name in sources:
    if sha(tree/Path(name).name)!=source_pins[name]:raise ValueError('compiled source differs')
   programs.append(dict(compiler=label,compiler_sha256=digest,program=str(tree/'findings'),program_sha256=sha(tree/'findings',64*1048576),helper=str(tree/'finding_helper'),helper_sha256=sha(tree/'finding_helper',64*1048576),stdout=out['stdout']))
  for name,digest in source_pins.items():
   if sha(ROOT/name)!=digest:raise ValueError('source changed '+name)
  store.write('RESULT.json',dict(complete=True,calls=len(calls),source_pins=source_pins,programs=programs,SDK_calls=0,Photo_calls=0,scope='fixed synthetic receipt-policy/core only; not receiving publication or SDK qualification',parent_tool_terminal_proved=False))
  store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);print('BASELINE_CLOSED',str(work),flush=True);return 0
 except BaseException as error:
  if can_close_failed_prefix(active=active,error=error):
   try:
    store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),settled_calls=len(calls)));store.close()
    if cpu is not None and not cpu.closed:
     if attempted:cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
     else:close_unstarted(cpu)
   except BaseException as failure:retain_after_record(lambda:print('BASELINE_CLOSE_RETAIN',repr(failure),flush=True))
   raise
  retain_after_record(lambda:print('BASELINE_RETAIN',repr(error),flush=True))
if __name__=='__main__':raise SystemExit(main())
