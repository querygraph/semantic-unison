"""Retain original whole-clone current Copy/native controls under Unison8."""
import argparse,contextlib,hashlib,io,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed,log_sha
from final_clone_interruption_owner import can_close_failed_prefix,generated_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from shared_child import start
from native_publication_driver_bridge import Temporary,driver_source


def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--compiler',choices=('stock','ox'),required=True);a=p.parse_args();root=Path(a.workspace)
 if root.parent!=Path('/private/tmp') or not root.name.startswith('u-whole-current-'):raise ValueError('fresh private namespace required')
 label=a.compiler;receipt=Path('/private/tmp/unison-endpoint-cpu-budget-'+label+'-check-20261018-001/RESULT.json');expected={'stock':'71e12a87fded7739949df93aceb3f006d115514742f751ac189e388cdd9a53e8','ox':'4b00fc9ad5da85d94c545c3d6b59f9ff1d3fe35e31994d255d95bc264a21fd64'}[label]
 if sha(receipt,2*1048576)!=expected:raise ValueError('current Make build receipt changed')
 build=json.loads(read_bytes(str(receipt),2*1048576));compiler=str(Path(build['compiler']).resolve());snapshot=Path(build['workspace']);pins={n:h for n,h in build['source_sha256'].items() if n.startswith('src/')}
 if len(pins)!=329 or not build['complete'] or build['build_exit']!=0 or build['selftest_exit']!=0:raise ValueError('qualified current full build required')
 for n,h in pins.items():
  if sha(ROOT/n)!=h or sha(snapshot/n)!=h:raise ValueError('production source changed '+n)
 script=ROOT/'tests/whole_file_clone/run.py';raw=read_bytes(str(script),65536).decode();filtered=driver_source(raw);fixtures={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'tests/whole_file_clone').iterdir() if p.is_file()};fixtures['tests/resource_lifetime/census.c']=sha(ROOT/'tests/resource_lifetime/census.c')
 root.mkdir(mode=0o700);v=root.stat();store=Store(str(root),dict(device=v.st_dev,inode=v.st_ino));cpu=None;active=attempted=False;calls=[]
 try:
  policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
  if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('standing8 changed')
  cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
  if cpu is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
  work=root/'original';freeze=root/'SOURCE-FREEZE.json';store.write(freeze.name,dict(sources=pins));output=root/'original-RESULT.json'
  if sha(compiler,64*1048576)!=build['compiler_sha256']:raise ValueError('compiler changed')
  store.write('START.json',dict(owner_pid=os.getpid(),compiler=label,source_pins=pins,fixture_pins=fixtures,build_receipt_sha256=expected,CPU=list(range(8)),EX_IO=False,SDK=False,compiler_jobs=1));print('WHOLE_START',os.getpid(),str(root),flush=True)
  class Commands:
   @staticmethod
   def run(argv,*,cwd,env,capture_output,text,timeout):
    nonlocal active,attempted
    argv=[os.fspath(x) for x in argv]
    if cwd!=work or capture_output is not True or text is not True or not 0<timeout<=120:raise ValueError('original invocation context changed')
    if argv[0] not in (compiler,'git') and not (Path(argv[0]).parent==work and Path(argv[0]).name.endswith('-test')):raise ValueError('unexpected program')
    if argv[0]=='git' and argv!=['git','-C',str(ROOT),'show','330d04829c43f6a19f6d5af1a95cf3ea24d24635:src/copy.ml']:raise ValueError('exact historical source read required')
    old=Path.cwd();active=attempted=True
    try:os.chdir(cwd);child=start(argv,env,pass_fds=cpu.fds)
    finally:os.chdir(old)
    out=child.finish(time.monotonic()+timeout);pin=store.write('call-%03d.json'%len(calls),out);calls.append(pin);closed(out,out['returncode']);active=False
    return subprocess.CompletedProcess(argv,out['returncode'],out['stdout'],out['stderr'])
  def owned_sha(path):
   path=Path(path);s=path.lstat()
   if not s.st_size:return log_sha(path)
   if path.is_relative_to(work) and s.st_nlink==2:return hashlib.sha256(generated_bytes(path,links=2,maximum=64*1048576)).hexdigest()
   return sha(path,64*1048576)
  namespace=dict(__name__='owned_original_driver',__file__=str(script),subprocess=Commands,tempfile=Temporary(work,'unison-whole-clone-'))
  exec(compile(filtered,str(script),'exec'),namespace);namespace['sha']=owned_sha
  old=sys.argv;log=io.StringIO()
  try:
   sys.argv=[str(script),str(snapshot),'--ocamlopt',compiler,'--freeze',str(freeze),'--keep-work','--receipt',str(output)]
   with contextlib.redirect_stdout(log):namespace['main']()
  finally:sys.argv=old
  result=json.loads(read_bytes(str(output),16*1048576))
  if result['success'] is not True or len(result['cases'])!=10:raise ValueError('original whole clone suite incomplete')
  for n,h in {**pins,**fixtures}.items():
   if sha(ROOT/n)!=h:raise ValueError('source changed '+n)
  store.write('RESULT.json',dict(complete=True,compiler=label,calls=calls,original_result=dict(path=str(output),sha256=sha(output,16*1048576)),cases=result['cases'],source_pins=pins,fixture_pins=fixtures,driver_stdout=log.getvalue(),SDK_or_Photo_calls=0,parent_tool_terminal_proved=False))
  store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);print('WHOLE_CLOSED',label,len(calls),str(root),flush=True);return 0
 except BaseException as error:
  if can_close_failed_prefix(active=active,error=error):
   try:
    store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),settled_calls=calls));store.close()
    if cpu is not None and not cpu.closed:
     if attempted:cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
     else:close_unstarted(cpu)
   except BaseException as failure:retain_after_record(lambda:print('WHOLE_CLOSE_RETAIN',repr(failure),flush=True))
   raise
  retain_after_record(lambda:print('WHOLE_RETAIN',repr(error),flush=True))
if __name__=='__main__':raise SystemExit(main())
