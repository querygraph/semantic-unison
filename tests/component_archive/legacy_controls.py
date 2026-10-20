"""Actual retained old production reader/writer on current private empty archives."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from component_archive.controls import objects
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for name in ('stock-build','ox-build','legacy-build'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--legacy-sha256',required=True);a=p.parse_args()
 assert sha(a.legacy_build)==a.legacy_sha256
 old=json.loads(a.legacy_build.read_text());assert old['complete'] and old['build_exit']==0
 oldroot=Path(old['workspace']);oldsrc=oldroot/'src'
 assert 'component owner manifest local' not in (oldsrc/'update.ml').read_text()
 assert 'component_owner_reference' not in (oldsrc/'update.mli').read_text()
 assert 'let archiveFormat = 23' in (oldsrc/'update.ml').read_text()
 old_sources={str(oldroot/n):h for n,h in old['source_sha256'].items() if n.startswith('src/')}
 assert all(sha(n)==h for n,h in old_sources.items())
 assert sha(old['binary'])==old['binary_sha256'] and sha(old['compiler'])==old['compiler_sha256']
 work=Path(tempfile.mkdtemp(prefix='unison-archive-legacy-',dir='/private/tmp'));work.chmod(0o700)
 result=dict(complete=False,calls=[],source_pins={},legacy_source_pins=old_sources,linked_artifacts={},cases=[],work=str(work),legacy_receipt_sha256=a.legacy_sha256,legacy_original_cli_invoked=False,SDK_invoked=False,real_media_or_transport=False)
 for source in (Path(__file__),ROOT/'tests/component_archive/legacy_probe.ml',ROOT/'tests/component_archive/probe.ml',ROOT/'tests/component_archive/controls.py'):
  result['source_pins'][str(source)]=sha(source)
 def environment(state):
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',UNISON=str(state))
  for key in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):env.pop(key,None)
  return env
 def call(argv,cwd,env):
  previous=Path.cwd()
  try:
   os.chdir(cwd);out=invoke(argv,env,time.monotonic()+60)
  finally:os.chdir(previous)
  result['calls'].append(out);save(work,result);c=out['client_cleanup']
  if not(c['reaped'] and c['other_group_members_absent_before_reap']):raise UnresolvedOwnership('legacy archive group unresolved')
  assert out['returncode']==0 and not out['capture_truncated'],out['stderr']
 def compile_probe(receipt,source,directory):
  assert sha(receipt['compiler'])==receipt['compiler_sha256']
  build=Path(receipt['workspace'])/'src';text=(build/'Makefile.OCaml').read_text()
  modules=objects(text,'OCAMLOBJS');modules=modules[:modules.index('update.cmx')+1];cobjects=objects(text,'COBJS')
  paths=[build/name for name in modules+cobjects];paths += [path.with_suffix('.o') for path in paths if path.suffix=='.cmx']
  result['linked_artifacts'].update({str(path):sha(path) for path in paths})
  copied=directory/source.name;copied.write_bytes(source.read_bytes())
  includes=[build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic']
  argv=[receipt['compiler']]+[v for path in includes for v in ('-I',str(path))]+['-I','+unix','-I','+str','unix.cmxa','str.cmxa']
  argv += [str(build/name) for name in modules]+[str(copied)]+[str(build/name) for name in cobjects]+['-o',str(directory/'probe')]
  call(argv,directory,environment(directory));return directory/'probe'
 legacy=work/'legacy';legacy.mkdir(mode=0o700)
 legacy_probe=compile_probe(old,ROOT/'tests/component_archive/legacy_probe.ml',legacy)
 def archives(case):
  values={path:path.read_bytes() for path in (case/'state').iterdir() if path.is_file() and path.name.startswith('ar') and path.read_bytes().startswith(b'Unison archive format 23\n')}
  assert len(values)==2 and all(len(data)<1048576 for data in values.values());return values
 magic=b'UAX\0\0\0\0\0'
 for label,path in [('stock',a.stock_build),('ox',a.ox_build)]:
  receipt=json.loads(path.read_text());assert receipt['complete'] and receipt['build_exit']==0
  for name,digest in receipt['source_sha256'].items():
   if name.startswith('src/'):
    assert sha(ROOT/name)==digest,name;result['source_pins'][str(ROOT/name)]=digest
  case=work/label;case.mkdir(mode=0o700)
  for name in ('left','right','state'):(case/name).mkdir(mode=0o700)
  probe=compile_probe(receipt,ROOT/'tests/component_archive/probe.ml',case);env=environment(case/'state')
  for phase in ('write','read'):call([str(probe),str(case),phase,'compat'],case,env)
  before=archives(case);assert sum(data[-136:-128]==magic for data in before.values())==1
  assert all(b'component owner manifest local' not in data for data in before.values())
  cached={path:sha(path) for path in (case/'state'/'manifest-compat').iterdir()};assert len(cached)==1
  call([str(legacy_probe),str(case),'read'],case,env)
  assert archives(case)==before,'retained reader changed current archives'
  call([str(legacy_probe),str(case),'rewrite'],case,env)
  after=archives(case);assert all(data[-136:-128]!=magic for data in after.values())
  assert all(sha(path)==digest for path,digest in cached.items()),'old rewrite changed manifest payload'
  call([str(probe),str(case),'missing','compat'],case,env)
  result['cases'].append(dict(current=label,legacy='retained stock5.2.0 pre-component-RPC fork',old_reader_preserved_exact_archive_bytes=True,old_writer_dropped_hint=True,manifest_payload_preserved=True,current_reload_cache_miss=True,archives_before={str(p):hashlib.sha256(b).hexdigest() for p,b in before.items()},archives_after={str(p):hashlib.sha256(b).hexdigest() for p,b in after.items()}));save(work,result)
 assert all(sha(path)==h for path,h in result['linked_artifacts'].items())
 assert all(sha(path)==h for path,h in result['source_pins'].items())
 assert all(sha(path)==h for path,h in old_sources.items())
 assert sha(old['binary'])==old['binary_sha256'] and sha(a.legacy_build)==a.legacy_sha256
 result['complete']=True;save(work,result);print(work,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
