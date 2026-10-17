"""Finite original owned publication fault fixtures; no transport/media/SDK."""
import hashlib,json,os,shutil,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def main():
 work=Path(tempfile.mkdtemp(prefix='unison-owned-publication-',dir='/private/tmp'));work.chmod(0o700)
 sources=[ROOT/p for p in ['src/stagePublication.ml','src/stagePublication.mli','src/stagePublication_stubs.c','tests/stage_publication_owned/fixture.c','tests/stage_publication_owned/test.ml','tests/stage_publication_owned/controls.py','tests/stage_publication/run.py','tests/stage_publication/fixture.c','tests/stage_publication/test.ml']]
 result=dict(complete=False,work=str(work),source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},calls=[],SDK_invoked=False,transport_invoked=False,photo_payload_opened=False)
 def call(argv,cwd):
  old=Path.cwd()
  try:
   os.chdir(cwd);r=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+90)
  finally:os.chdir(old)
  result['calls'].append(r);save(work,result)
  c=r['client_cleanup']
  if not(c['reaped'] and c['other_group_members_absent_before_reap']):raise UnresolvedOwnership('owned publication probe child unresolved')
  assert r['returncode']==0 and not r['capture_truncated'],r['stderr']
 for label,switch in [('stock','default'),('ox','5.2.0+ox')]:
  compiler=Path('/Users/alexy/.opam')/switch/'bin/ocamlopt'
  result.setdefault('compilers',{})[str(compiler)]=hashlib.sha256(compiler.read_bytes()).hexdigest()
  case=work/label;case.mkdir(mode=0o700)
  for p in sources[:5]:shutil.copyfile(p,case/p.name)
  for name in ['stagePublication.mli','stagePublication.ml','fixture.c']:call([str(compiler),'-I','+unix','-c',name],case)
  call([str(compiler),'-I','+unix','unix.cmxa','fixture.o','stagePublication.cmx','test.ml','-o','probe'],case)
  call([str(case/'probe'),str(case)],case)
  call([sys.executable,str(ROOT/'tests/stage_publication/run.py'),'--ocamlopt',str(compiler)],case)
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in result['source_pins'].items())
 result['complete']=True;save(work,result);print(work,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
