"""Read-only independent binding of retained baseline artifacts and owned calls."""
import hashlib,io,json,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import closed,sha
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted
from sdk_fixture_build_owner import tool_sha


def archive_sources(archive,tree,base,patches):
 raw=read_bytes(str(archive),64*1048576);count=0
 with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
  if tar.pax_headers.get('comment')!=base:raise ValueError('Git archive commit binding differs')
  for member in tar.getmembers():
   name=member.name;q=Path(name)
   if q.is_absolute() or '..' in q.parts:raise ValueError('archive escape')
   if not member.isfile() or not (q.suffix in ('.ml','.mli','.c','.h') or q.name in ('Makefile','Makefile.OCaml')):continue
   original=tar.extractfile(member).read();expected=hashlib.sha256(original).hexdigest()
   if name in patches:
    if expected!=patches[name]['base_sha256']:raise ValueError('patch base differs')
    expected=patches[name]['patched_sha256']
   if member.size and sha(tree/name,16*1048576)!=expected:raise ValueError('archive/source difference: '+name)
   if not member.size and (tree/name).stat().st_size!=0:raise ValueError('empty source changed')
   count+=1
 return dict(archive_sha256=hashlib.sha256(raw).hexdigest(),archive_source_files=count)


def owner(work,base,calls,patches):
 r=json.loads(read_bytes(str(work/'RESULT.json'),2*1048576));rows=[]
 if r['complete'] is not True or r['base']!=base or r['calls']!=calls:raise ValueError('baseline incomplete')
 for index in range(calls):
  p=work/('call-%02d.json'%index);out=json.loads(read_bytes(str(p),4*1048576));closed(out,0)
  if type(out['client_cleanup']['pid']) is not int or out['client_cleanup']['pid']<=0:raise ValueError('child identity absent')
  rows.append(dict(path=str(p),sha256=sha(p,4*1048576),pid=out['client_cleanup']['pid'],command=out['command']))
 if rows[-1]['command']!=[r['binary'],'-ui','text','-selftest']:raise ValueError('selftest command differs')
 if rows[0]['command']!=['/usr/bin/git','archive','--format=tar','--output='+str(work/'SOURCE.tar'),base]:raise ValueError('export command differs')
 if sha(r['binary'],64*1048576)!=r['binary_sha256'] or tool_sha(r['compiler'])!=r['compiler_sha256']:raise ValueError('binary/compiler changed')
 return dict(workspace=str(work),result_sha256=sha(work/'RESULT.json',2*1048576),binary=r['binary'],binary_sha256=r['binary_sha256'],compiler=r['compiler'],compiler_sha256=r['compiler_sha256'],calls=rows,**archive_sources(work/'SOURCE.tar',work/'source',base,patches))


def audit():
 cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
 if cpu is None:raise ValueError('standing CPU busy; no audit started')
 try:
  refs=json.loads(read_bytes(str(ROOT/'doc/upstream-baseline-source-preparation-v2-20261019.json'),65536))
  original=owner(Path('/private/tmp/u-original-stock-a7bd5af941'),'375ea3ad2cace8584c508ef463332066d85e1d4e',5,{})
  ox=owner(Path('/private/tmp/u-upstream-ox-67ff102c3b'),refs['base'],7,refs['files'])
  path=Path('/private/tmp/unison-genuine-upstream-stock-build-20261017-001/RESULT.json');raw=read_bytes(str(path),2*1048576)
  if hashlib.sha256(raw).hexdigest()!='68b8321b344409f4e6011588a616de6a3a96119c08fd9dba50a33bd6d32c4c2e':raise ValueError('prior genuine stock receipt differs')
  r=json.loads(raw)
  if r['complete'] is not True or r['build_exit']!=0 or r['selftest_exit']!=0 or r['source_origin']['commit']!=refs['base']:raise ValueError('prior upstream failed')
  if sha(r['binary'],64*1048576)!=r['binary_sha256'] or tool_sha(Path(r['compiler']).resolve())!=r['compiler_sha256']:raise ValueError('prior artifact/compiler changed')
  stock=dict(receipt=str(path),receipt_sha256=hashlib.sha256(raw).hexdigest(),binary=r['binary'],binary_sha256=r['binary_sha256'],compiler_sha256=r['compiler_sha256'],scope='retained historical build/selftest; new direct-child ledger NOT claimed',**archive_sources(Path(r['source_origin']['archive']),Path(r['workspace']),refs['base'],{}))
  result=dict(schema='unison-three-baseline-artifact-binding/1',original_stock=original,upstream_stock=stock,minimal_upstream_ox=ox,EX_acquired=False,SDK_calls=0,performance_claim=False)
 finally:
  if not cpu.closed:close_unstarted(cpu)
 result['audit_CPU00_07_closed']=True
 return result
if __name__=='__main__':print(json.dumps(audit(),indent=2))
