"""Production-linked component worker controls; original tiny inputs, no SDK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
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
 p=argparse.ArgumentParser();p.add_argument('--stock-build',required=True,type=Path);p.add_argument('--ox-build',required=True,type=Path);a=p.parse_args()
 work=Path(tempfile.mkdtemp(prefix='unison-component-worker-controls-',dir='/private/tmp'))
 result=dict(complete=False,calls=[],linked_artifacts={},source_pins={},work=str(work),SDK_invoked=False,real_media_opened=False)
 for source in [Path(__file__),ROOT/'tests/workers/components.ml']:
  result['source_pins'][str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
 def call(argv,cwd):
  previous=Path.cwd()
  try:
   os.chdir(cwd);out=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+60)
  finally:os.chdir(previous)
  result['calls'].append(out);save(work,result)
  c=out['client_cleanup']
  if not(c['reaped'] and c['other_group_members_absent_before_reap']):raise UnresolvedOwnership('component worker child/group unresolved')
  assert out['returncode']==0 and not out['capture_truncated'],out['stderr']
 def objects(text,name):
  match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S);assert match,name
  return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
 for label,path in [('stock',a.stock_build),('ox',a.ox_build)]:
  receipt=json.loads(path.read_text());assert receipt['complete'] and receipt['build_exit']==0 and receipt['build_system']=='make'
  for relative,digest in receipt['source_sha256'].items():
   if relative.startswith('src/'):
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    result['source_pins'][str(ROOT/relative)]=digest
  assert hashlib.sha256(Path(receipt['compiler']).read_bytes()).hexdigest()==receipt['compiler_sha256']
  build=Path(receipt['workspace'])/'src';text=(build/'Makefile.OCaml').read_text()
  modules=objects(text,'OCAMLOBJS');modules=modules[:modules.index('semanticWorkers.cmx')+1];cobjects=objects(text,'COBJS')
  paths=[build/name for name in modules+cobjects];paths += [p.with_suffix('.o') for p in paths if p.suffix=='.cmx']
  pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};result['linked_artifacts'].update(pins)
  target=work/label;target.mkdir(mode=0o700);source=target/'components.ml';source.write_bytes((ROOT/'tests/workers/components.ml').read_bytes())
  data=bytearray(8192);struct.pack_into('<2sHIH',data,0,b'II',42,8,5)
  for i,entry in enumerate([(273,4,1,4096),(279,4,1,1024),(700,1,16,1024),(50706,1,4,1025),(50740,1,128,3072)]):struct.pack_into('<HHII',data,10+12*i,*entry)
  data[1024:1040]=b'<x>one</x>      ';data[4096:5120]=b'P'*1024
  (target/'fixture.dng').write_bytes(data);(target/'unsupported.bin').write_bytes(b'original unsupported fixture')
  includes=[build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic']
  argv=[receipt['compiler']]+[v for p in includes for v in ('-I',str(p))]+['-I','+unix','-I','+str','unix.cmxa','str.cmxa']
  argv += [str(build/name) for name in modules]+[str(source)]+[str(build/name) for name in cobjects]+['-o',str(target/'components')]
  call(argv,target);call([str(target/'components')],target)
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in result['source_pins'].items())
 result['complete']=True;save(work,result);print(work,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
