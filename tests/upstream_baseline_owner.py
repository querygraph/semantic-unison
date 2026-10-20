"""Serial isolated upstream baseline build; standing Unison8, no Photo/SDK IO."""
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
 if work.parent!=Path('/private/tmp') or not work.name.startswith('u-upstream-ox-'):raise ValueError('fresh baseline namespace required')
 patch=ROOT/'doc/upstream-8772-minimal-oxcaml-v2.patch'
 if sha(patch)!='7951aaede099632e392ba950f9381e52a1a46ac07e5dcf222b21996b3f401f3e':raise ValueError('patch changed')
 compiler=Path('/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt').resolve()
 if tool_sha(compiler)!='e02b8590aa2c05948203befbfef22253282b1799d92f9a32c3878681f1b3e166':raise ValueError('compiler changed')
 policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
 if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('standing policy changed')
 work.mkdir(mode=0o700);st=work.stat();store=Store(str(work),dict(device=st.st_dev,inode=st.st_ino));cpu=None;active=attempted=False;calls=[]
 try:
  cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
  if cpu is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
  env=dict(os.environ,PATH='/Users/alexy/.opam/5.2.0+ox/bin:'+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
  for k in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(k,None)
  store.write('START.json',dict(owner_pid=os.getpid(),workspace=str(work),base='8772d26a2eb77cfd0cb6da81807e81f24f51044c',patch_sha256=sha(patch),CPU=list(range(8)),EX_IO=False,SDK=False,compiler_jobs=1))
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
  run(['/usr/bin/git','archive','--format=tar','--output='+str(work/'SOURCE.tar'),'8772d26a2eb77cfd0cb6da81807e81f24f51044c'],ROOT,60)
  tree=work/'source';tree.mkdir();run(['/usr/bin/tar','-xf',str(work/'SOURCE.tar'),'-C',str(tree)],work,60)
  run(['/usr/bin/git','apply','--check',str(patch)],tree,30);run(['/usr/bin/git','apply',str(patch)],tree,30)
  refs=json.loads(read_bytes(str(ROOT/'doc/upstream-baseline-source-preparation-v2-20261019.json'),65536))
  for name,ref in refs['files'].items():
   if sha(tree/name)!=ref['patched_sha256']:raise ValueError('patched source differs '+name)
  for target in ('depend','tui'):run(['/usr/bin/make','-s','-C','src',target,'-j1','NATIVE=true','TOOL_PREFIX=/Users/alexy/.opam/5.2.0+ox/bin/'],tree,900)
  binary=tree/'src/unison';state=work/'selftest-state';state.mkdir();env['UNISON']=str(state)
  run([str(binary),'-ui','text','-selftest'],tree,600)
  store.write('RESULT.json',dict(complete=True,base=refs['base'],patch_sha256=refs['patch_sha256'],binary=str(binary),binary_sha256=sha(binary,64*1048576),compiler=str(compiler),compiler_sha256=tool_sha(compiler),calls=len(calls),patched_sources=refs['files'],parent_tool_terminal_proved=False))
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
