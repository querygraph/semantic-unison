"""Original tiny managed-cache loader and disposable native close-fault controls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def main():
 modules=['semanticHash','semanticFile','componentHash','formatExtension','xmpObservation','xmpMerge','dngSemantic','dngExtended','dngLayout','dngComponents']
 work=Path(tempfile.mkdtemp(prefix='unison-cache-loader-controls-',dir='/private/tmp'));work.chmod(0o700)
 sources=[ROOT/'src'/(m+ext) for m in modules for ext in ('.ml','.mli','.ox.mli.in') if (ROOT/'src'/(m+ext)).exists()]
 sources += [ROOT/'src'/n for n in ('semantic_mode_filter.ml','semanticHash_stubs.c','semanticHash_evp.h','semanticFile_stubs.c')]
 sources += [Path(__file__),ROOT/'tests/semantic/cache_loader.ml',ROOT/'tests/semantic/cache_loader_fault_stubs.c',ROOT/'tests/semantic/cache_loader_native.ml',ROOT/'tests/semantic/cache_namespace.ml',ROOT/'tests/semantic/cache_namespace_native.ml',ROOT/'tests/semantic/cache_store.ml']
 result=dict(complete=False,calls=[],source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},work=str(work),SDK_invoked=False,media_payload_opened=False,production_fault_switch=False)
 def call(argv,expected=0):
  out=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+90);result['calls'].append(out);save(work,result)
  c=out['client_cleanup']
  if not(c['reaped'] and c['other_group_members_absent_before_reap']):raise UnresolvedOwnership('cache loader control group unresolved')
  assert out['returncode']==expected and not out['capture_truncated'],out['stderr']
  return out
 mode=work/'semantic-mode-filter';shutil.copyfile(ROOT/'src/semantic_mode_filter.ml',work/'semantic_mode_filter.ml')
 call(['/Users/alexy/.opam/default/bin/ocamlopt',str(work/'semantic_mode_filter.ml'),'-o',str(mode)])
 for label,switch in [('stock','default'),('ox','5.2.0+ox')]:
  compiler='/Users/alexy/.opam/'+switch+'/bin/ocamlopt';version=call([compiler,'-version'])['stdout'].strip()
  target=work/label;target.mkdir(mode=0o700)
  for module in modules:
   for ext in ('.mli','.ml'):(target/(module+ext)).write_text(call([str(mode),version,str(ROOT/'src'/(module+ext))])['stdout'])
  for name in ('semanticHash_stubs.c','semanticHash_evp.h','semanticFile_stubs.c'):shutil.copyfile(ROOT/'src'/name,target/name)
  for name in ('cache_loader.ml','cache_loader_fault_stubs.c','cache_loader_native.ml','cache_namespace.ml','cache_namespace_native.ml','cache_store.ml'):shutil.copyfile(ROOT/'tests/semantic'/name,target/name)
  before=Path.cwd()
  try:
   os.chdir(target)
   call([compiler,'-c','cache_loader_fault_stubs.c'])
   call([compiler,'-ccopt','-Dclose=unison_cache_control_close','-ccopt','-Dopenat=unison_cache_control_openat','-ccopt','-Dpread=unison_cache_control_pread','-ccopt','-Dfsync=unison_cache_control_fsync','-c','semanticFile_stubs.c'])
   command=[compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c']
   for module in modules:command += [module+'.mli',module+'.ml']
   command += ['cache_loader.ml','semanticFile_stubs.o','cache_loader_fault_stubs.o','-o','cache-loader-controls']
   call(command);call([str(target/'cache-loader-controls')])
   namespace=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
   namespace += ['cache_namespace.ml','semanticHash_stubs.o','semanticFile_stubs.o','cache_loader_fault_stubs.o','-o','cache-namespace-controls']
   call(namespace);call([str(target/'cache-namespace-controls')])
   store=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
   store += ['cache_store.ml','semanticHash_stubs.o','semanticFile_stubs.o','cache_loader_fault_stubs.o','-o','cache-store-controls']
   call(store);call([str(target/'cache-store-controls')])
   if label=='ox':
    leak=target/'owner_only_uncertainty.ml';leak.write_text('let leak (state:DngComponents.cache_ownership) = Domain.Safe.spawn (fun () -> ignore(DngComponents.cache_retained_descriptors state))\n')
    refused=call([compiler,'-c',str(leak)],expected=2)
    assert 'nonportable' in refused['stderr'] or 'contended' in refused['stderr']
    leak=target/'owner_only_namespace.ml';leak.write_text('let leak (state:DngComponents.cache_namespace) = Domain.Safe.spawn (fun () -> ignore(DngComponents.cache_namespace_created state))\n')
    refused=call([compiler,'-c',str(leak)],expected=2)
    assert 'nonportable' in refused['stderr'] or 'contended' in refused['stderr']
   fault_pin=hashlib.sha256((target/'semanticFile_stubs.o').read_bytes()).hexdigest()
   shutil.copyfile(target/'semanticFile_stubs.o',target/'semanticFile_fault_stubs.o')
   # Recompile the untouched native source without macros and run its own probe.
   call([compiler,'-c','semanticFile_stubs.c'])
   native=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
   native += ['cache_loader_native.ml','semanticHash_stubs.o','semanticFile_stubs.o','-o','cache-loader-native']
   call(native);call([str(target/'cache-loader-native')])
   namespace=[compiler,'-I','+unix','unix.cmxa']+[m+'.cmx' for m in modules]
   namespace += ['cache_namespace_native.ml','semanticHash_stubs.o','semanticFile_stubs.o','-o','cache-namespace-native']
   call(namespace);call([str(target/'cache-namespace-native')])
   result.setdefault('fault_native_sha256',{})[label]=fault_pin
   result.setdefault('control_artifacts',{})[label]={n:hashlib.sha256((target/n).read_bytes()).hexdigest() for n in ('cache-loader-controls','cache-loader-native','cache-namespace-controls','cache-namespace-native','cache-store-controls','semanticFile_stubs.o','semanticFile_fault_stubs.o','cache_loader_fault_stubs.o')};save(work,result)
  finally:os.chdir(before)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in result['source_pins'].items())
 result['complete']=True;save(work,result);print(work,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
