"""Read-only binding of original fixed receipt-policy matrix; no SDK calls."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import closed,sha,log_sha
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted
from sdk_fixture_build_owner import tool_sha


def main():
 work=Path('/private/tmp/u-validation-policy-c3ef49a206')
 cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
 if cpu is None:raise ValueError('standing CPU busy')
 try:
  result=json.loads(read_bytes(str(work/'RESULT.json'),1048576));assert result['complete'] and result['calls']==34
  source=read_bytes(str(ROOT/'tests/final_validation_policy/findings.ml'),65536).decode()
  modes=re.findall('"([a-z-]+)"',re.search(r'let modes=\[(.*?)\]',source,re.S).group(1));assert len(modes)==len(set(modes))==19
  expected=[]
  for policy in ('require','warn'):
   for mode in modes:
    outcome='passed' if mode in ('valid','missing','warnings') else ('warning' if policy=='warn' else 'rejected')
    expected.append(f'PASS policy={policy} mode={mode} finding={outcome} helper-reaped=true group-before-reap=0')
  expected.append('PASS off no-inspection no-execution; 38 finding/policy cases')
  calls=[]
  for i in range(34):
   p=work/('call-%02d.json'%i);out=json.loads(read_bytes(str(p),4*1048576));closed(out,0)
   assert type(out['client_cleanup']['pid']) is int and out['client_cleanup']['pid']>0
   calls.append(dict(path=str(p),sha256=sha(p,4*1048576),pid=out['client_cleanup']['pid'],command=out['command']))
  assert len({x['pid'] for x in calls})==34
  for label,run_index in [('stock',16),('ox',33)]:
   program=next(p for p in result['programs'] if p['compiler']==label)
   out=json.loads(read_bytes(str(work/('call-%02d.json'%run_index)),4*1048576))
   assert out['stdout'].splitlines()==expected and program['stdout']==out['stdout']
   assert out['command']==[program['program'],program['helper']]
   assert sha(program['program'],64*1048576)==program['program_sha256']
   assert sha(program['helper'],64*1048576)==program['helper_sha256']
   compiler=calls[run_index-1]['command'][0];assert tool_sha(Path(compiler).resolve())==program['compiler_sha256']
   for name,digest in result['source_pins'].items():
    assert sha(ROOT/name)==digest==sha(work/label/Path(name).name)
  warnings=[]
  receipt=ROOT/'tests/qualification/cpu-ceiling-dependent-composition-actual-20261018.json'
  prior=json.loads(read_bytes(str(receipt),4*1048576))
  cases=['warn-error','warn-pass','require-error','off','warn-inspection-error','warn-mutation','warn-active-cancel','warn-before-delivery-cancel','warn-delivery-cancel','warn-delivery-abort','warn-printer-error']
  for step in prior['steps']:
   if step['case']!='validation-warning':continue
   for name,digest in step['production_sha256'].items():assert sha(ROOT/name)==digest
   z=step['result'];assert z['success'] is True
   for name,digest in z['source_pins'].items():assert sha(ROOT/'src'/name)==digest
   for name,digest in z['test_pins'].items():assert sha(ROOT/'tests/validation_warning'/name)==digest
   for ref in step['artifacts']:
    if ref['bytes']==0:
     assert log_sha(ref['path'])==ref['sha256'];continue
    raw=read_bytes(ref['path'],4*1048576);assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
   assert [row['case'] for row in z['runs']]==cases
   logs=[]
   for row in z['runs']:
    call=row['execution'];assert call['exit']==0 and row['mode']=='fixed' and row['designated_negative_detected'] is False
    assert log_sha(call['log'])==call['log_sha256']
    text=read_bytes(call['log'],262144).decode();assert 'PASS case='+row['case']+' ' in text
    logs.append(dict(case=row['case'],log=call['log'],sha256=call['log_sha256']))
   c=step['closure'];assert c['tokens_closed'] is True and c['child']['returncode']==0 and c['child']['reaped'] is True and c['child']['other_group_members_absent_before_reap'] is True
   warnings.append(dict(compiler=step['compiler'],production_sources=len(step['production_sha256']),linked_sources=len(z['source_pins']),test_sources=len(z['test_pins']),cases=logs,actual_parent=prior['actual_tool'],scope='rebound historical current-source warning companion; not a new execution/native UI/SDK proof'))
  assert len(warnings)==2
  report=dict(schema='unison-final-validation-finding-policy/1',actual_tool=dict(session=8018,terminal_chunk='480d0d',exit_code=0,running_session=False),result_path=str(work/'RESULT.json'),result_sha256=sha(work/'RESULT.json',1048576),source_pins=result['source_pins'],programs=result['programs'],calls=calls,warning_companions=warnings,modes=modes,policies=['require','warn'],finding_cases_per_compiler=38,off_cases_per_compiler=1,SDK_calls=0,EX_acquired=False,scope='production DngValidation/HelperSupervisor with original synthetic receipts and synthetic inspection snapshots; no receiving-path publication/real executable hash or SDK proof')
 finally:
  if not cpu.closed:close_unstarted(cpu)
 report['CPU00_07_fresh_reacquired_closed']=True
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
