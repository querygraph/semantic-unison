"""Read-only audit of separately completed original scratch fault suites."""
import hashlib,json,re,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed,log_sha
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted
from sdk_fixture_build_owner import tool_sha


def main():
 cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
 if cpu is None:raise ValueError('CPU busy')
 try:
  driver=runpy.run_path(str(ROOT/'tests/clone_scratch/run.py'),run_name='original_pure_mutations_only');source=read_bytes(str(ROOT/'src/copy_stubs.c'),1048576).decode()
  total0=total2=0;pids=[];runs=[]
  for label,folder,terminal in [('stock','u-scratch-current-9d83e2fa17',dict(tool=93759,terminal_chunk='ad106a',exit_code=1,running_session=False,scope='native suite passed; outer summary schema KeyError; known prefix all26settled/CPUclosed')),('ox','u-scratch-current-0518b0da37',dict(tool=28661,terminal_chunk='6ba333',exit_code=0,running_session=False))]:
   work=Path('/private/tmp')/folder;path=work/(label+'-RESULT.json');r=json.loads(read_bytes(str(path),2*1048576));assert r['terminal']=='passed'
   assert [row['mode'] for row in r['runs']]==['fixed','absolute-reservation','missing-reservation-guard']
   start=json.loads(read_bytes(str(work/'START.json'),1048576));assert start['source_pins']==r['sources'] and start['EX_IO'] is False
   for name,digest in r['sources'].items():assert sha(ROOT/name)==digest
   assert tool_sha(r['compiler'])==r['compiler_sha256']
   rawcalls=[];refs=[]
   for index in range(26):
    p=work/('call-%03d.json'%index);out=json.loads(read_bytes(str(p),1048576));closed(out,out['returncode']);assert out['returncode'] in (0,2)
    pid=out['client_cleanup']['pid'];assert type(pid)is int and pid>0 and pid not in pids;pids.append(pid)
    total0+=out['returncode']==0;total2+=out['returncode']==2;rawcalls.append(out);refs.append(dict(path=str(p),sha256=sha(p,1048576),pid=pid,exit_code=out['returncode']))
   expected_probes=[[r['compiler'],'-version'],[r['compiler'],'-config'],['/usr/bin/xcrun','--find','clang'],[r['native_compiler'],'--version']]
   assert [c['command'] for c in rawcalls[:4]]==expected_probes
   cursor=4;names=[];negative=[];derivatives=[]
   for mode in r['runs']:
    build=Path(mode['binary']).parent
    assert sha(mode['binary'],64*1048576)==mode['binary_sha256']
    expected=driver['mutated'](source,mode['mode']).encode();actual=read_bytes(str(build/'copy_stubs.c'),1048576)
    assert actual==expected and hashlib.sha256(actual).hexdigest()==mode['production_copy_sha256']
    assert sha(build/'fixture.c')==r['sources']['tests/clone_scratch/fixture.c'] and sha(build/'test.ml')==r['sources']['tests/clone_scratch/test.ml']
    expected_ml='let path (p : Fspath.t) = p\ntype clone_stage_decline ='+read_bytes(str(ROOT/'src/fs.ml'),1048576).decode().split('type clone_stage_decline =',1)[1].split('(****)',1)[0]
    expected_mli='type clone_stage_decline ='+read_bytes(str(ROOT/'src/fs.mli'),1048576).decode().split('type clone_stage_decline =',1)[1]
    assert read_bytes(str(build/'fs.ml'),1048576).decode()==expected_ml and read_bytes(str(build/'fs.mli'),1048576).decode()==expected_mli
    derivatives.append(dict(mode=mode['mode'],production_copy_sha256=mode['production_copy_sha256'],binary_sha256=mode['binary_sha256']))
    for call in mode['commands']+[mode['execution'],*mode['additional_executions']]:
     out=rawcalls[cursor];cursor+=1;assert out['command']==call['argv'] and out['returncode']==call['exit_code']
     assert log_sha(call['log'])==call['log_sha256'];text=read_bytes(call['log'],262144).decode() if Path(call['log']).stat().st_size else ''
     if call.get('detected_assertion'):
      assert out['returncode']==2 and call['detected_assertion'] in text;negative.append(dict(abi=call['abi'],defect=call['detected_defect'],assertion=call['detected_assertion']))
     else:assert out['returncode']==0
     if call.get('cases'):
      assert call['cases']==182 and call['assertions']==1984;names=re.findall(r'^case (.+)$',text,re.M)
      assert names==re.findall(r'^ok [0-9]+ (.+?) assertions=',text,re.M) and len(names)==182
     if 'native_artifact_manifest' in call:assert sha(call['native_artifact_manifest'],4*1048576)==call['native_artifact_manifest_sha256']
   assert cursor==26 and len(negative)==6
   counts={api:sum(n.startswith(api+'/') for n in names) for api in ('legacy','strict','handles')};assert counts==dict(legacy=61,strict=61,handles=60)
   if label=='stock':
    failure=json.loads(read_bytes(str(work/'KNOWN-FAILED-PREFIX.json'),1048576));assert failure['error']=="KeyError('executions')" and len(failure['settled_calls'])==26
   else:
    outer=json.loads(read_bytes(str(work/'RESULT.json'),1048576));assert outer['complete'] and outer['calls']==26
   runs.append(dict(compiler=label,actual_tool=terminal,result_path=str(path),result_sha256=sha(path,2*1048576),calls=refs,native_cases=names,cases_by_api=counts,assertions=1984,negative_controls=negative,derivatives=derivatives,source_pins=r['sources']))
  assert len(pids)==52 and total0==40 and total2==12
  report=dict(schema='unison-current-clone-scratch-actual/1',runs=runs,calls=52,normal_zero=40,designated_two=12,CPU00_07_fresh_reacquired_closed=True,EX_acquired=False,SDK_or_Photo_calls=0,scope='current native small-APFS scratch ownership/rollback and six private guard removals/compiler; stock outer summary failed after native PASS; not physical exhaustion/full receiving/crash durability/performance')
 finally:
  if not cpu.closed:close_unstarted(cpu)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
