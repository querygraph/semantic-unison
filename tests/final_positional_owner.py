"""Owned original native positional controls, serial stock/Ox on Unison8.

No EXglobal, SDK or photographic input. Original ML/C bodies and private guard
ablations remain driver-selected. Imports/commands/inventory get trusted owners.
"""
import argparse,contextlib,hashlib,io,json,os,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed,log_sha
from final_clone_interruption_owner import can_close_failed_prefix,generated_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from shared_child import start
from sdk_fixture_build_owner import tool_sha
from native_publication_driver_bridge import Temporary,driver_source


def inventory(directory):
 entries={}
 for p in sorted(directory.rglob('*')):
  v=p.lstat();row=dict(device=v.st_dev,inode=v.st_ino,mode=v.st_mode,links=v.st_nlink,size=v.st_size,mtime_ns=v.st_mtime_ns,ctime_ns=v.st_ctime_ns)
  if stat.S_ISREG(v.st_mode):
   row['kind']='regular'
   if v.st_size<=1048576:row['sha256']=hashlib.sha256(generated_bytes(p,links=v.st_nlink,maximum=1048576)).hexdigest() if v.st_size else log_sha(p)
   else:
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
     before=os.fstat(fd)
     if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns):raise ValueError('sparse fixture rebound')
     row['bounded_samples']={str(at):os.pread(fd,64,at).hex() for at in (0,max(0,v.st_size-64))}
     after=os.fstat(fd)
     if (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)!=(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns):raise ValueError('sparse fixture changed')
    finally:close_descriptors([fd])
    row['scope']='large generated sparse size/epoch and two64B samples, not full hole read/hash'
  elif stat.S_ISLNK(v.st_mode):row.update(kind='symlink',target=os.readlink(p))
  elif stat.S_ISDIR(v.st_mode):row['kind']='directory'
  entries[str(p.relative_to(directory))]=row
 return entries


def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);a=p.parse_args();root=Path(a.workspace)
 if root.parent!=Path('/private/tmp') or not root.name.startswith('u-positional-current-'):raise ValueError('fresh owned namespace required')
 script=ROOT/'tests/positional_write/run.py';raw=read_bytes(str(script),65536).decode();filtered=driver_source(raw)
 compilers=[('stock','/Users/alexy/.opam/default/bin/ocamlopt.opt','f183dd4bd5c655b56fb87da2d39e01b843a730b6252e8b92fc6989e6f07cfacf'),('ox','/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt','e02b8590aa2c05948203befbfef22253282b1799d92f9a32c3878681f1b3e166')]
 # Evaluate definitions only; never execute the original subprocess driver.
 namespace=dict(__name__='owned_original_driver',__file__=str(script));exec(compile(filtered,str(script),'exec'),namespace)
 original_mutate=namespace['mutate']
 def current_mutate(source,mode):
  if mode!='forced-ml-backend':return original_mutate(source,mode)
  start=source.index('CAMLprim value unison_semantic_prepare_writer(')
  end=source.index('CAMLprim value unison_semantic_pwrite(',start)
  body=source[start:end]
  if body.count('CAMLreturn(Val_true);')!=1:raise ValueError('exact writer-only preparation anchor required')
  return source[:start]+body.replace('CAMLreturn(Val_true);','CAMLreturn(Val_false);',1)+source[end:]
 namespace['mutate']=current_mutate
 pins={n:sha(ROOT/n) for n in namespace['INPUTS']}
 root.mkdir(mode=0o700);v=root.stat();store=Store(str(root),dict(device=v.st_dev,inode=v.st_ino));cpu=None;active=attempted=False;calls=[]
 try:
  policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
  if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('standing policy changed')
  cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
  if cpu is None:store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
  for _,compiler,digest in compilers:
   if tool_sha(compiler)!=digest:raise ValueError('compiler changed')
  store.write('START.json',dict(owner_pid=os.getpid(),source_pins=pins,cpu_indexes=list(range(8)),EX_IO=False,SDK=False,compiler_jobs=1));print('POSITIONAL_START',os.getpid(),str(root),flush=True)
  deadline=time.monotonic()+900;runs=[]
  for label,compiler,digest in compilers:
   work=root/label;report=root/(label+'-RESULT.json');original_argv=sys.argv;start_index=len(calls)
   def invoke(argv,environment,cwd,seconds):
    nonlocal active,attempted
    if time.monotonic()+125>=deadline:raise TimeoutError('no new child near observation end')
    argv=[os.fspath(x) for x in argv]
    if argv[0] not in (compiler,'/usr/bin/xcrun','/Library/Developer/CommandLineTools/usr/bin/clang') and not (Path(argv[0]).name=='positional-test' and Path(argv[0]).is_relative_to(work)):raise ValueError('non-original command refused')
    if cwd is not None and not Path(cwd).is_relative_to(work):raise ValueError('working directory escaped')
    old=Path.cwd();attempted=active=True
    try:
     if cwd is not None:os.chdir(cwd)
     child=start(argv,dict(os.environ) if environment is None else environment,pass_fds=cpu.fds)
    finally:os.chdir(old)
    out=child.finish(min(deadline,time.monotonic()+seconds));pin=store.write('call-%03d.json'%len(calls),out);calls.append(pin);closed(out,out['returncode']);active=False
    if len(calls)%20==0:print('POSITIONAL_CHILDREN',len(calls),flush=True)
    return out
   class Probes:
    @staticmethod
    def check_output(argv,*,env=None,text=False):
     allowed=[[compiler,flag] for flag in ('-version','-config','-where')]+[['/usr/bin/xcrun','--find','clang'],['/Library/Developer/CommandLineTools/usr/bin/clang','--version']]
     if argv not in allowed:raise ValueError('unreviewed probe')
     out=invoke(argv,env,None,30)
     if out['returncode']:raise ValueError('probe failed')
     return out['stdout'] if text else out['stdout'].encode()
   def execute(argv,*,work,env,log,timeout=90):
    begin=time.monotonic();out=invoke(argv,env,work,timeout)
    from final_clone_stage_owner import write_bytes
    write_bytes(log,(out['stdout']+out['stderr']).encode())
    return dict(argv=argv,cwd=str(work),exit_code=out['returncode'],elapsed_seconds=time.monotonic()-begin,log=str(log),log_sha256=log_sha(log))
   def bound_sha(path):
    path=Path(path)
    if path==Path('/Library/Developer/CommandLineTools/usr/bin/clang'):return tool_sha(path)
    return sha(path,64*1048576) if path.stat().st_size else log_sha(path)
   namespace.update(subprocess=Probes,tempfile=Temporary(work,'unison-positional-write-'),execute=execute,inventory=inventory,sha=bound_sha)
   output=io.StringIO()
   try:
    sys.argv=[str(script),'--ocamlopt',compiler,'--receipt',str(report)]
    with contextlib.redirect_stdout(output):namespace['main']()
   finally:sys.argv=original_argv
   result=json.loads(read_bytes(str(report),4*1048576))
   if result['terminal']!='passed' or result['sources']!=pins or [r['mode'] for r in result['runs']]!=['fixed','forward-bad-progress','forced-ml-backend','seek-write','missing-append-guard','heap-pointer']:raise ValueError('original positional scope narrowed')
   positives=[];negatives=[]
   for mode in result['runs']:
    for row in mode['executions']:
     if row.get('detected_assertion'):negatives.append(row['detected_assertion'])
     else:positives.append(dict(mode=mode['mode'],cases=row['cases'],assertions=row['assertions']))
   if len(negatives)!=4 or sum(x['cases'] for x in positives)!=64:raise ValueError('original positive/negative case count differs')
   runs.append(dict(compiler=label,result_path=str(report),result_sha256=sha(report,4*1048576),calls=calls[start_index:],positives=positives,negatives=negatives,driver_stdout=output.getvalue()))
   print('POSITIONAL_PASS',label,len(calls)-start_index,flush=True)
  for n,h in pins.items():
   if sha(ROOT/n)!=h:raise ValueError('original input changed')
  store.write('RESULT.json',dict(complete=True,runs=runs,calls=len(calls),source_pins=pins,driver_binding='only imports/process execution/retained tempdir/bounded qualified inventory/hash; original ML/C fixtures and driver guard ablations unchanged',SDK_or_Photo_calls=0,parent_tool_terminal_proved=False));store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);print('POSITIONAL_CLOSED',str(root),flush=True);return 0
 except BaseException as error:
  if can_close_failed_prefix(active=active,error=error):
   try:
    store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),settled_calls=calls));store.close()
    if cpu is not None and not cpu.closed:
     if attempted:cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
     else:close_unstarted(cpu)
   except BaseException as failure:retain_after_record(lambda:print('POSITIONAL_CLOSE_RETAIN',repr(failure),flush=True))
   raise
  retain_after_record(lambda:print('POSITIONAL_RETAIN',repr(error),flush=True))
if __name__=='__main__':raise SystemExit(main())
