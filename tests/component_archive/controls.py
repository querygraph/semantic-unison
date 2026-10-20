"""Production-linked empty-root archive hint controls; no SDK or transport."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def objects(text,name):
 match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S);assert match,name
 return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()

def main():
 p=argparse.ArgumentParser();p.add_argument('--stock-build',type=Path,required=True);p.add_argument('--ox-build',type=Path);a=p.parse_args()
 work=Path(tempfile.mkdtemp(prefix='unison-archive-hints-',dir='/private/tmp'));work.chmod(0o700)
 result=dict(complete=False,calls=[],source_pins={},linked_artifacts={},private_archives=[],work=str(work),SDK_invoked=False,transport_invoked=False,real_media_opened=False)
 for path in (Path(__file__),ROOT/'tests/component_archive/probe.ml'):
  result['source_pins'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 def call(argv,cwd,env):
  previous=Path.cwd()
  try:
   os.chdir(cwd);out=invoke(argv,env,time.monotonic()+60)
  finally:os.chdir(previous)
  result['calls'].append(out);save(work,result)
  c=out['client_cleanup']
  if not(c['reaped'] and c['other_group_members_absent_before_reap']):raise UnresolvedOwnership('archive probe group unresolved')
  assert out['returncode']==0 and not out['capture_truncated'],out['stderr']
 for label,path in [('stock',a.stock_build)]+([('ox',a.ox_build)] if a.ox_build else []):
  receipt=json.loads(path.read_text());assert receipt['complete'] and receipt['build_exit']==0 and receipt['build_system']=='make'
  for relative,digest in receipt['source_sha256'].items():
   if relative.startswith('src/'):
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    result['source_pins'][str(ROOT/relative)]=digest
  assert hashlib.sha256(Path(receipt['compiler']).read_bytes()).hexdigest()==receipt['compiler_sha256']
  build=Path(receipt['workspace'])/'src';text=(build/'Makefile.OCaml').read_text()
  modules=objects(text,'OCAMLOBJS');modules=modules[:modules.index('update.cmx')+1];cobjects=objects(text,'COBJS')
  paths=[build/name for name in modules+cobjects];paths += [p.with_suffix('.o') for p in paths if p.suffix=='.cmx']
  pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};result['linked_artifacts'].update(pins)
  case=work/label;case.mkdir(mode=0o700)
  for name in ('left','right','state'):(case/name).mkdir(mode=0o700)
  source=case/'probe.ml';source.write_bytes((ROOT/'tests/component_archive/probe.ml').read_bytes())
  includes=[build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic']
  argv=[receipt['compiler']]+[v for directory in includes for v in ('-I',str(directory))]+['-I','+unix','-I','+str','unix.cmxa','str.cmxa']
  argv += [str(build/name) for name in modules]+[str(source)]+[str(build/name) for name in cobjects]+['-o',str(case/'probe')]
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',UNISON=str(case/'state'))
  call(argv,case,env)
  for phase in ('write','read','off','missing'):call([str(case/'probe'),str(case),phase,'first'],case,env)
  call([str(case/'probe'),str(case),'write','second'],case,env)
  archives=[p for p in (case/'state').iterdir() if p.is_file() and p.read_bytes().startswith(b'Unison archive format 23\n')]
  assert len(archives)==2
  hinted=[p for p in archives if p.read_bytes()[-136:-128]==b'UAX\0\0\0\0\0'];assert len(hinted)==1
  target=hinted[0];original=target.read_bytes();assert len(original)<1048576
  (case/'original-hinted-archive.bin').write_bytes(original)
  changed=original[:-1]+bytes([original[-1]^1]);target.write_bytes(changed)
  call([str(case/'probe'),str(case),'bad','second'],case,env)
  result['private_archives'].append(dict(label=label,corrupted_only_optional_checksum=True,path=str(target),original_sha256=hashlib.sha256(original).hexdigest(),changed_sha256=hashlib.sha256(changed).hexdigest()))
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in pins.items())
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in result['source_pins'].items())
 result['complete']=True;save(work,result);print(work,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
