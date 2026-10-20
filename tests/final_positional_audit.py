"""Independent current-source/call/negative binding; no control rerun or SDK."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed,log_sha
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted
from sdk_fixture_build_owner import tool_sha


def mutation(source,mode):
 op='ssize_t written = pwrite(fd, buffer, (size_t)count, native_offset);'
 def once(old,new):
  if source.count(old)!=1:raise ValueError('exact private mutation anchor missing')
  return source.replace(old,new,1)
 if mode=='fixed':return source
 if mode=='seek-write':return once(op,'ssize_t written = lseek(fd, native_offset, SEEK_SET) < 0 ? -1 :\n    write(fd, buffer, (size_t)count);')
 if mode=='missing-append-guard':return once('else if (flags & O_APPEND) error = EINVAL;','else if (0) error = EINVAL;')
 if mode=='heap-pointer':
  source=once('if (count) memcpy(buffer, String_val(data) + first, (size_t)count);','if (count) memcpy(buffer, String_val(data) + first, (size_t)count);\n  const void *borrowed_pointer = String_val(data) + first;')
  return once(op,'ssize_t written = pwrite(fd, borrowed_pointer, (size_t)count, native_offset);')
 if mode=='forward-bad-progress':return once('if (written < -1 || written > count || (written == -1 && !error))','if (written == -1 && !error)')
 if mode=='forced-ml-backend':
  start=source.index('CAMLprim value unison_semantic_prepare_writer(');end=source.index('CAMLprim value unison_semantic_pwrite(',start);body=source[start:end]
  assert body.count('CAMLreturn(Val_true);')==1
  return source[:start]+body.replace('CAMLreturn(Val_true);','CAMLreturn(Val_false);',1)+source[end:]
 raise ValueError('unknown mode')


def main():
 work=Path('/private/tmp/u-positional-current-6de2a4f3c0');cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire(tuple(range(8)))
 if cpu is None:raise ValueError('CPU busy')
 try:
  result=json.loads(read_bytes(str(work/'RESULT.json'),4*1048576));assert result['complete'] is True and result['calls']==210
  for n,h in result['source_pins'].items():assert sha(ROOT/n)==h
  pids=[];calls=[];zero=two=0;summaries=[];artifacts=0;named=[]
  for run in result['runs']:
   original=json.loads(read_bytes(run['result_path'],4*1048576));assert sha(run['result_path'],4*1048576)==run['result_sha256']
   assert original['sources']==result['source_pins'] and original['terminal']=='passed'
   assert tool_sha(original['compiler'])==original['compiler_sha256']
   rawcalls=[]
   for ref in run['calls']:
    p=work/ref['name'];raw=read_bytes(str(p),1048576);assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];out=json.loads(raw);closed(out,out['returncode'])
    assert out['returncode'] in (0,2);pid=out['client_cleanup']['pid'];assert type(pid)is int and pid>0 and pid not in pids;pids.append(pid)
    zero+=out['returncode']==0;two+=out['returncode']==2;rawcalls.append(out);calls.append(dict(path=str(p),sha256=ref['sha256'],pid=pid,exit_code=out['returncode']))
   expected_probes=[[original['compiler'],'-version'],[original['compiler'],'-config'],['/usr/bin/xcrun','--find','clang'],[original['native_compiler'],'--version'],[original['compiler'],'-where']]
   assert [x['command'] for x in rawcalls[:5]]==expected_probes
   assert rawcalls[0]['stdout'].strip()==original['compiler_version'] and rawcalls[1]['stdout']==original['compiler_config']
   cursor=5
   for mode in original['runs']:
    build=Path(mode['binary']).parent
    assert sha(mode['binary'],64*1048576)==mode['binary_sha256']
    for name,digest in mode['build_files'].items():assert sha(build/name,64*1048576)==digest;artifacts+=1
    source=read_bytes(str(ROOT/'src/semanticFile_stubs.c'),1048576).decode();assert read_bytes(str(build/'semanticFile_stubs.c'),1048576).decode()==mutation(source,mode['mode'])
    assert sha(build/'fixture.c')==result['source_pins']['tests/positional_write/fixture.c']
    test=read_bytes(str(ROOT/'tests/positional_write/test.ml'),1048576).decode();actual=read_bytes(str(build/'test.ml'),1048576).decode();assert actual in (test,test.replace('let with_async_exns f = f ()','let with_async_exns = Sys.with_async_exns'))
    for command in mode['commands']+mode['executions']:
     out=rawcalls[cursor];cursor+=1;assert out['command']==command['argv']
     assert out['returncode']==command['exit_code'] and log_sha(command['log'])==command['log_sha256']
     text=read_bytes(command['log'],262144).decode() if Path(command['log']).stat().st_size else ''
     if 'detected_assertion' in command:assert out['returncode']==2 and command['detected_assertion'] in text
     else:assert out['returncode']==0
     if 'native_artifact_manifest' in command:assert sha(command['native_artifact_manifest'],4*1048576)==command['native_artifact_manifest_sha256']
     if mode['mode']=='fixed' and 'cases' in command:
      cases=re.findall(r'^case (.+)$',text,re.M);passed=re.findall(r'^ok [0-9]+ (.+?) assertions=',text,re.M);assert cases==passed and len(cases)==59
      named.append(dict(compiler=run['compiler'],named_native_cases=cases))
   assert cursor==len(rawcalls)
   assert sum(x['cases'] for x in run['positives'])==64 and sum(x['assertions'] for x in run['positives'])==1131 and len(run['negatives'])==4
   summaries.append(dict(compiler=run['compiler'],positive_cases=64,assertions=1131,negative_assertions=run['negatives']))
  assert zero==202 and two==8 and len(pids)==210
  report=dict(schema='unison-current-positional-native-audit/1',actual_owner=dict(tool=73365,initial_chunk='68ce3c',terminal_chunk='d6f63a',exit_code=0,running_session=False),workspace=str(work),result_sha256=sha(work/'RESULT.json',4*1048576),source_pins=result['source_pins'],calls=calls,normal_zero=zero,designated_two=two,artifact_entries_rehashed=artifacts,summaries=summaries,named_cases=named,CPU00_07_fresh_reacquired_closed=True,EX_acquired=False,SDK_or_Photo_calls=0,scope='original fixed59 native pwrite cases plus5 ML-positive and4 designated private guard-ablation controls percompiler; not receiving/publication/crash durability/physicalIO/RSS proof')
 finally:
  if not cpu.closed:close_unstarted(cpu)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
