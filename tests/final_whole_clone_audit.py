"""Read-only current whole-clone caller/native and designated-parent binding."""
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
 if cpu is None:raise ValueError('standing CPU busy')
 try:
  driver=runpy.run_path(str(ROOT/'tests/whole_file_clone/run.py'),run_name='pure_transformations_only');runs=[];pids=[];zeros=twos=artifacts=linked=0
  specs=[('stock','u-whole-current-8f26ad70cb',55677,'daab31'),('ox','u-whole-current-1fc5d49e60',99536,'6c48f3')]
  for label,folder,tool,terminal in specs:
   root=Path('/private/tmp')/folder;outer=json.loads(read_bytes(str(root/'RESULT.json'),2*1048576));assert outer['complete'] is True and len(outer['calls'])==34
   ref=outer['original_result'];assert sha(ref['path'],16*1048576)==ref['sha256'];result=json.loads(read_bytes(ref['path'],16*1048576));assert result['success'] is True
   assert result['source_pins']==outer['source_pins'] and len(outer['source_pins'])==329
   for name,digest in {**outer['source_pins'],**outer['fixture_pins']}.items():assert sha(ROOT/name)==digest
   assert tool_sha(result['compiler']['path'])==result['compiler']['sha256']
   for name,digest in result['linked_objects'].items():assert sha(name,64*1048576)==digest;linked+=1
   for ref in result['artifacts'].values():
    assert Path(ref['path']).stat().st_size==ref['bytes']
    assert (sha(ref['path'],64*1048576) if ref['bytes'] else log_sha(ref['path']))==ref['sha256'];artifacts+=1
   calls=[];parent_source=None;case_logs=[]
   assert len(result['commands'])==34
   for original,pin in zip(result['commands'],outer['calls']):
    p=root/pin['name'];raw=read_bytes(str(p),1048576);assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'];out=json.loads(raw);closed(out,out['returncode'])
    assert out['command']==original['argv'] and out['returncode']==original['exit'] and log_sha(original['log'])==original['log_sha256']
    pid=out['client_cleanup']['pid'];assert type(pid)is int and pid>0 and pid not in pids;pids.append(pid)
    assert out['returncode'] in (0,2);zeros+=out['returncode']==0;twos+=out['returncode']==2
    for item in original['private_inputs'].values():assert sha(item['path'],64*1048576)==item['sha256']
    if out['command'][0]=='git':
     assert out['command']==['git','-C',str(ROOT),'show','330d04829c43f6a19f6d5af1a95cf3ea24d24635:src/copy.ml'];parent_source=out['stdout']
    if out['command'][0].endswith('-test'):
     text=out['stdout']+out['stderr'];matches=[c for c in result['cases'] if re.sub(r'^[0-9]+-','',Path(original['log']).name)==c['name']+'.log'];assert len(matches)==1;case=matches[0]
     assert case['observed_exit']==out['returncode']
     if case['expected_failure']:assert out['returncode']==2 and case['expected_failure'] in out['stderr']
     else:assert out['returncode']==0 and sum(line.startswith('PASS ') for line in out['stdout'].splitlines())==case['groups']
     case_logs.append(dict(case=case['name'],exit_code=out['returncode'],groups=case['groups'],expected_failure=case['expected_failure'],stdout=out['stdout'],stderr=out['stderr']))
    calls.append(dict(path=str(p),sha256=pin['sha256'],pid=pid,exit_code=out['returncode']))
   assert len(case_logs)==10 and [x['groups'] for x in case_logs[:5]]==[15,17,9,12,7]
   parent=result['parent_negative'];assert parent['commit']=='330d04829c43f6a19f6d5af1a95cf3ea24d24635' and hashlib.sha256(parent_source.encode()).hexdigest()==parent['source_sha256']
   snapshot=Path(result['production_build'])/'src';work=Path(result['work']);current_copy=driver['HOOK']+read_bytes(str(snapshot/'copy.ml'),1048576).decode()
   parent_copy=driver['HOOK']+parent_source+'\nlet copyFile ?clone_owned:_ = copyFile\n'
   seen=[]
   for command in result['commands']:
    if 'copyForTest.ml' in command['private_inputs']:
     data=read_bytes(command['private_inputs']['copyForTest.ml']['path'],1048576).decode();assert data in (current_copy,parent_copy);seen.append('current' if data==current_copy else 'historical-parent')
   assert 'current' in seen and 'historical-parent' in seen
   decoder=read_bytes(str(snapshot/'wholeFileClone.ml'),1048576).decode()
   guard='if r.completed <> 0L || r.mutation <> No_effect ||\n          not (decline_consistent scope r) then'
   assert decoder.count(guard)==1
   bad_decoder=decoder.replace(guard,'if r.completed <> 0L ||\n          not (decline_consistent scope r) then',1)
   fs=driver['instrument_fs'](read_bytes(str(snapshot/'fs.ml'),1048576).decode());assert fs.count('Fault.probe_close_slot descriptor owned')==1
   old_close_fs=fs.replace('Fault.probe_close_slot descriptor owned','Fault.legacy_probe_close_slot descriptor owned',1)
   for name,allowed in [('wholeFileCloneForTest.ml',[decoder,bad_decoder]),('fsForTest.ml',[fs,old_close_fs])]:
    versions=[]
    for command in result['commands']:
     if name in command['private_inputs']:
      data=read_bytes(command['private_inputs'][name]['path'],1048576).decode();assert data in allowed;versions.append(data)
    assert set(versions)==set(allowed)
   assert read_bytes(str(work/'wholeFileCloneForTest_stubs.c'),1048576).decode()==driver['instrument_native'](read_bytes(str(snapshot/'wholeFileClone_stubs.c'),1048576).decode())
   runs.append(dict(compiler=label,actual_owner=dict(tool=tool,terminal_chunk=terminal,exit_code=0,running_session=False),outer_result_path=str(root/'RESULT.json'),outer_result_sha256=sha(root/'RESULT.json',2*1048576),source_pins=outer['source_pins'],fixture_pins=outer['fixture_pins'],case_logs=case_logs,calls=calls,parent_negative=parent,scope='current full Copy source with private Fs hooks/current matched support objects; exact parent is negative caller only, not a full parent binary'))
  assert len(pids)==68 and zeros==58 and twos==10
  report=dict(schema='unison-final-whole-clone-current-actual/1',runs=runs,direct_children=68,normal_zero=zeros,designated_two=twos,generated_artifact_entries_rehashed=artifacts,matched_linked_objects_rehashed=linked,CPU00_07_fresh_reacquired_closed=True,EX_acquired=False,SDK_or_Photo_calls=0,scope='60fixed wholeclone groups/536assertions plus5designated controls/compiler; actual smallAPFS named/ownership plus simulated FDsharing/cursor/typed result; not physical sharing/performance/fullCLI/other-platform proof')
 finally:
  if not cpu.closed:close_unstarted(cpu)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
