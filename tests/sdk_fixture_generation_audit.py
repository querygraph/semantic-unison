"""Metadata/protocol-only postclosure audit; never reopen generated DNG payloads."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed
from camera_sdk_receiving.sdk_audit import receipt,BUILD
from sdk_merge_receiving.data import stamp
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted


def main():
 cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire((0,))
 if cpu is None:raise ValueError('CPU00 busy')
 try:
  plan=ROOT/'doc/sdk-fixture-generation-plan-v2-20261019.json';assert sha(plan,2*1048576)=='048d0ae7aac95e89d3bae5aaf74e9d5bd2842df38ffd3ec42eefe7101d3b424c';p=json.loads(read_bytes(str(plan),2*1048576));work=Path(p['workspace'])
  r=json.loads(read_bytes(str(work/'RESULT.json'),2*1048576));assert r['complete'] is True and r['SDK_calls']==13 and len(r['calls'])==13 and r['source_hash_bytes']==0
  assert r['source_pins']==p['source_pins'];assert len(p['source_pins'])==571
  for n,h in p['source_pins'].items():assert sha(ROOT/n)==h
  for ref in p['prerequisites']:assert sha(ref['path'],2*1048576)==ref['sha256']
  for ref in p['sources']:assert stamp(os.lstat(ref['path']))==ref['identity']
  manifest_ref=r['input_manifest'];raw=read_bytes(manifest_ref['path'],1048576);assert len(raw)==manifest_ref['bytes'] and hashlib.sha256(raw).hexdigest()==manifest_ref['sha256'];manifest=json.loads(raw)
  assert set(manifest)=={'schema','cases','ancestry'} and manifest['schema']=='unison-current-sdk-merge-inputs/1'
  for ref in manifest['ancestry']:assert sha(ref['path'],2*1048576)==ref['sha256']
  generation=json.loads(read_bytes(str(work/'GENERATION.json'),2*1048576));assert generation['calls']==r['calls'] and generation['reports']==r['reports']
  refs={}
  for case in manifest['cases']:
   for state,ref in case['states'].items():refs[case['codec'],state]=ref
  assert len(refs)==12 and len({ref['path'] for ref in refs.values()})==12
  calls=[];pids=[];findings=[];states=[]
  for index,pin in enumerate(r['calls']):
   path=work/pin['name'];raw=read_bytes(str(path),1048576);assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'];out=json.loads(raw);closed(out,0)
   pid=out['client_cleanup']['pid'];assert type(pid)is int and pid>0 and pid not in pids;pids.append(pid)
   if index==0:
    clone=json.loads(read_bytes(str(work/'uncompressed-CLONE.json'),1048576));assert out['command']==[p['writer']['path'],'jxl',clone['path'],str(Path(p['destination'])/'jxl.dng')]
   else:
    report=r['reports'][index-1];ref=refs[report['codec'],report['state']];assert ref==report['reference']
    expected=[p['validator']['path'],'--unison-dng-validation-v1','--expected-sha256',ref['sha256'],'--expected-size',str(ref['bytes']),'--threads','1','--',ref['path']];assert out['command']==expected
    parsed=receipt(out['stdout'].encode('ascii'),candidate_sha256=ref['sha256'],candidate_bytes=ref['bytes'],build_id=BUILD);assert parsed==report['report'] and parsed['raw_digest_verified'] is True
    assert report['identity']==generation['state_epochs'][ref['path']]==stamp(os.lstat(ref['path'])) and report['identity']['st_mode']==0o100400 and report['identity']['st_nlink']==1
    findings.append(dict(codec=report['codec'],state=report['state'],candidate=ref,report=parsed,epoch=report['identity']));states.append((report['codec'],report['state']))
   calls.append(dict(path=str(path),sha256=pin['sha256'],pid=pid,command=out['command'],exit_code=0))
  assert states==[(codec,state) for codec in ('uncompressed','jpeg','jxl') for state in ('base','left','right','target')]
  result=dict(schema='unison-generated-sdk-fixtures-actual-audit/1',actual_owner=dict(tool=76654,initial_chunk='e2ad8d',terminal_chunk='590918',exit_code=0,running_session=False),plan=dict(path=str(plan),sha256='048d0ae7aac95e89d3bae5aaf74e9d5bd2842df38ffd3ec42eefe7101d3b424c'),workspace=str(work),result_sha256=sha(work/'RESULT.json',2*1048576),input_manifest=manifest_ref,source_pins_verified=571,prerequisites_verified=6,calls=calls,findings=findings,retained_source_epochs_unchanged=2,input_payload_reopened_by_audit=False,execution_artifact_reopened_by_audit=False,EX_acquired_by_audit=False,scope='one2768writer generated JXL and12readonly scalarstates independently2724validated with rawdigestvalid; not actual merge receiving/pixel/corpus/production proof')
 finally:
  if not cpu.closed:close_unstarted(cpu)
 result['audit_CPU00_closed']=True;print(json.dumps(result,indent=2))
if __name__=='__main__':main()
