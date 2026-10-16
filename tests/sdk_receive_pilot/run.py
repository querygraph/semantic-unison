#!/usr/bin/env python3
"""Build/qualify a finite SDK receive pilot. Default is build-only, no Adobe calls."""
import argparse,hashlib,json,os,pathlib,shlex,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/adobe'))
from phase import supervise,invoke_contained

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def write(path,value):pathlib.Path(path).write_text(json.dumps(value,indent=2)+'\n')
def require(condition,message):
 if not condition:raise RuntimeError(message)
def contained_cli(receipt,work):
 r=json.loads(receipt.read_text());build=pathlib.Path(r['workspace']);compiler=r['compiler']
 require(r['complete'] and r['build_exit']==r['selftest_exit']==0,'build not qualified')
 require(sha(r['binary'])==r['binary_sha256'] and sha(compiler)==r['compiler_sha256'],'binary/compiler mismatch')
 for name,digest in r['source_sha256'].items():
  if name.startswith('src/'):require(sha(ROOT/name)==digest,'production source changed: '+name)
 work.mkdir();shutil.copyfile(build/'src/helperSupervisor_stubs.c',work/'helperSupervisor_stubs.c')
 flags=[value for sub in ['src','src/ubase','src/system','src/system/generic','src/lwt','src/lwt/generic'] for value in ['-I',str(build/sub)]]
 # Reuse the exact Make link command, replacing only output/helper C object.
 commands=[shlex.split(line) for line in (build/'build.log').read_text().splitlines() if line.startswith(compiler+' ') and ' -o unison ' in line]
 require(len(commands)==1,'unique actual Make link command required')
 command=commands[0];command[command.index('-o')+1]=str(work/'unison')
 for i,arg in enumerate(command):
  if arg=='helperSupervisor_stubs.o':command[i]=str(work/'helperSupervisor_stubs.o')
 log=work/'build.log'
 with log.open('w') as output:
  subprocess.run([compiler,*flags,'-ccopt','-DUNISON_BENCH_CONTAINED_HELPERS','-c','helperSupervisor_stubs.c'],cwd=work,stdout=output,stderr=subprocess.STDOUT,check=True)
  inputs=[pathlib.Path(arg) if pathlib.Path(arg).is_absolute() else build/'src'/arg for arg in command if arg.endswith(('.cmx','.o'))]
  linked={str(path):sha(path) for path in inputs}
  subprocess.run(command,cwd=build/'src',stdout=output,stderr=subprocess.STDOUT,check=True)
  require(all(sha(path)==digest for path,digest in linked.items()),'linked inputs changed')
 return {'binary':str(work/'unison'),'sha256':sha(work/'unison'),'build_receipt_sha256':sha(receipt),'compiler':compiler,'helper_backend':'test-only inherited aggregate group; production ML objects unchanged','build_log_sha256':sha(log),'linked_inputs':linked}

def check_admission(packet,work,admission,request_path,command):
 import time
 require(packet['mode']=='prepare','native execution requires a separate build-only preparation')
 require(admission['state']=='ROOT_ADMITTED_FINITE_UNISON_RECEIVE_PILOT_V1','fresh receive admission required')
 require(time.time()<admission['startDeadlineUnix'],'admission expired')
 require(admission['command']==command,'exact admitted command mismatch')
 require(admission['limits']=={'SDK_calls_maximum':10,'generated_inputs_maximum':7,'logical_states_maximum':16,'active_CPU_credits':8,'aggregate_native_wall_seconds':300},'admitted limits mismatch')
 require(admission['request']['path']==str(request_path.resolve()) and admission['request']['sha256']==sha(request_path),'request pin mismatch')
 request=json.loads(request_path.read_text())
 require(request['prepared']=={'path':str(work/'READY.json'),'sha256':sha(work/'READY.json')},'preparation pin mismatch')
 for name,digest in packet['source_pins'].items():require(sha(ROOT/name)==digest,'pilot source changed')
 for record in packet['builds'].values():require(sha(record['binary'])==record['sha256'],'prepared CLI changed')
 for fixture in packet['fixtures']:
  for kind in ['original','edited']:require(sha(fixture[kind])==fixture[kind+'_sha256'],'prepared input changed')
 require(sha(packet['bad_digest']['path'])==packet['bad_digest']['sha256'],'negative input changed')
 require(sha(packet['driver_manifest']['executable'])==packet['driver_manifest']['executable_sha256'],'native executable changed')
 for name in ['WRAPPER-START.json','START.json','RESULT.json','calls','AGGREGATE-CLOSED.json','AGGREGATE-OWNERSHIP-UNRESOLVED.json']:
  require(not (work/name).exists(),'prepared slot already started or unresolved: '+name)

def execute(packet,work,mode,admission=None,admission_pin=None):
 fixtures=packet['fixtures'];bad=pathlib.Path(packet['bad_digest']['path'])
 if mode=='mock':
  mock=work/'MOCK-TOOL.py';mock.write_text('''#!/usr/bin/python3
import os,sys
args=sys.argv[1:];bad=args[2]=='__BAD_SHA__'
print('UNISON-DNG-VALIDATION 1\\ncandidate-sha256 '+args[2]+'\\ncandidate-size '+args[4]+'\\ndriver-build unison-finite-receive-MOCK\\nstructure valid\\ndecode success\\nraw-digest '+('mismatch' if bad else 'valid')+'\\nerrors '+('1' if bad else '0')+'\\nwarnings 0\\nEND')
'''.replace('__BAD_SHA__',sha(bad)));mock.chmod(0o700)
 else:mock=pathlib.Path(packet['driver_manifest']['executable'])
 build_id='unison-finite-receive-MOCK' if mode=='mock' else packet['driver_manifest']['build_id']
 executable_pin=sha(mock) if mode=='mock' else packet['driver_manifest']['executable_sha256']
 guard=work/'guard.py';shutil.copyfile(ROOT/'tests/sdk_receive_pilot/guard.py',guard);guard.chmod(0o700)
 guard_pin=packet['source_pins']['tests/sdk_receive_pilot/guard.py'];require(sha(guard)==guard_pin,'copied guard changed')
 calls=work/'calls';calls.mkdir()
 def phase():
  configuration={'mode':mode.upper(),'workspace':str(work),'group':os.getpgrp(),'calls':str(calls),'executable':str(mock),'executable_sha256':executable_pin,'allowed_sha256':[f[k] for f in fixtures for k in ['original_sha256','edited_sha256']]+[sha(bad)]}
  write(guard.with_suffix('.json'),configuration)
  if mode=='native':
   import time
   require(time.time()<admission['startDeadlineUnix'],'admission expired before owned start')
   with (work/'START.json').open('x') as output:
    json.dump({'group':os.getpgrp(),'unix':time.time(),'admission_sha256':admission_pin},output)
   print('START '+json.dumps({'group':os.getpgrp(),'workspace':str(work)}),flush=True)
  results=[]
  def invoke(command,environment):
   result=invoke_contained(command,environment,60)
   require(not result['timed_out'] and not result['capture_truncated'],'CLI deadline/capture failure')
   return result
  # Three original positive calls plus six mixed-compiler receive updates and
  # one rejected bad-digest update: 10 calls, 7 inputs, 16 logical states.
  for f in fixtures:
   args=['--unison-dng-validation-v1','--expected-sha256',f['original_sha256'],'--expected-size',str(pathlib.Path(f['original']).stat().st_size),'--threads','1','--',f['original']]
   r=invoke([str(guard),*args],dict(os.environ));require(r['returncode']==0,'original control failed')
   lines=r['stdout'].splitlines();require(len(lines)==10 and lines[0]=='UNISON-DNG-VALIDATION 1' and lines[-1]=='END','original receipt framing')
   fields=dict(line.split(' ',1) for line in lines[1:-1]);require(len(fields)==8,'original receipt fields')
   require(fields['candidate-sha256']==f['original_sha256'] and fields['candidate-size']==str(pathlib.Path(f['original']).stat().st_size) and fields['driver-build']==build_id,'original receipt binding')
   require(fields['structure']=='valid' and fields['decode']=='success' and fields['raw-digest']=='valid' and fields['errors']=='0' and int(fields['warnings'])>=0,'original validation failed')
   write(work/(f['codec']+'-original-receipt.json'),r)
  for f in fixtures:
   for direction in ['stock-ox','ox-stock']:
    client,server=direction.split('-');case=work/(f['codec']+'-'+direction);case.mkdir()
    left,right,state,remote=[case/n for n in ['left','right','client-state','server-state']]
    for path in [left,right,state,remote]:path.mkdir()
    binary=packet['builds'][client]['binary'];peer=packet['builds'][server]['binary']
    launcher=case/'loopback.py';launcher.write_text('#!/usr/bin/python3\nimport os,sys\na=sys.argv[1:];i=a.index('+repr(peer)+');os.environ["UNISON"]='+repr(str(remote))+';os.execv(a[i],a[i:])\n');launcher.chmod(0o700)
    config={'adobevalidator':str(guard),'adobevalidatorhash':guard_pin,'adobevalidatorbuild':build_id,'adobevalidatorthreads':'1','adobevalidatetimeout':'30'}
    (remote/'endpoint.prf').write_text(''.join(k+' = '+v+'\n' for k,v in config.items()))
    command=[binary,str(left),'ssh://localhost/'+str(right),'-sshcmd',str(launcher),'-servercmd',peer,'-batch','-auto','-fastcheck','false','-semanticdng=true','-clone','auto','-semanticworkers','1','-maxthreads','1','-debug','semantic']+[value for k,v in config.items() for value in ['-'+k,v]]
    shutil.copyfile(f['original'],left/'image.dng');env=dict(os.environ,UNISON=str(state))
    r=invoke([*command,'-adobevalidate','off'],env);write(case/'baseline.json',r);require(r['returncode']==0,'baseline sync failed')
    shutil.copyfile(f['edited'],left/'image.dng')
    r=invoke([*command,'-adobevalidate','require'],env);write(case/'receive.json',r)
    require(r['returncode']==0 and 'Remote semantic clone wrote' in r['stdout']+r['stderr'],'semantic receive failed')
    require(sha(right/'image.dng')==f['edited_sha256'],'received bytes differ')
    results.append({'codec':f['codec'],'direction':direction,'status':'passed'})
    if f['codec']=='uncompressed' and direction=='stock-ox':
     shutil.copyfile(bad,left/'image.dng');r=invoke([*command,'-adobevalidate','require'],env);write(case/'rejected.json',r)
     require(r['returncode']!=0 and 'SDK driver reported validation errors' in r['stdout']+r['stderr'] and sha(right/'image.dng')==f['edited_sha256'],'bad-digest publication was not refused')
  observed=[json.loads(path.read_text()) for path in sorted(calls.glob('*.json'))]
  require(len(observed)==10 and all(r['pgid']==os.getpgrp() for r in observed),'call count/group mismatch')
  from collections import Counter
  expected=Counter({f['original_sha256']:1 for f in fixtures})
  expected.update({f['edited_sha256']:2 for f in fixtures});expected[sha(bad)]=1
  require(Counter(r['sha256'] for r in observed)==expected,'entry multiplicity mismatch')
  write(work/'RESULT.json',{'mode':mode.upper(),'cases':results,'actual_tool_entries':observed,'sdk_calls':0 if mode=='mock' else len(observed)})
 with (work/'WRAPPER-START.json').open('x') as output:
  json.dump({'pid':os.getpid(),'mode':mode,'admission_sha256':admission_pin},output)
 closure=supervise(phase,work,300)
 write(work/'SUPERVISOR-RETURN.json',{'wrapper_pid':os.getpid(),'aggregate':closure,'scope':'parent returned from aggregate supervisor; not a parent terminal-exit receipt'})
 require(closure['returncode']==0,'finite phase failed')
 print(mode+' phase closed:',work,flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--stock-build',type=pathlib.Path,required=True);p.add_argument('--ox-build',type=pathlib.Path,required=True)
 p.add_argument('--sdk-result',type=pathlib.Path,required=True);p.add_argument('--fixtures',type=pathlib.Path,required=True)
 p.add_argument('--driver-manifest',type=pathlib.Path,required=True);p.add_argument('--workspace',type=pathlib.Path,required=True)
 p.add_argument('--mode',choices=['prepare','mock','native'],default='prepare')
 p.add_argument('--admission',type=pathlib.Path);p.add_argument('--request',type=pathlib.Path)
 a=p.parse_args();work=a.workspace.resolve()
 if a.mode=='native':
  require(a.admission is not None and a.request is not None,'fresh admission/request required')
  packet=json.loads((work/'READY.json').read_text());admission=json.loads(a.admission.read_text())
  check_admission(packet,work,admission,a.request,[sys.executable,*sys.argv])
  execute(packet,work,'native',admission,sha(a.admission));return
 work.mkdir(mode=0o700)
 require(sha(a.sdk_result)=='2cb79ab00574d56da16a66c696f0b82e27749dc43994f5084450e67115a1fae1','accepted SDK v2 result pin required')
 sdk=json.loads(a.sdk_result.read_text());manifest=json.loads(a.driver_manifest.read_text())
 require(sha(manifest['executable'])==manifest['executable_sha256'],'SDK driver pin changed')
 packet={'schema':'unison-finite-sdk-receive-preparation/1','mode':a.mode,'native_release':False,'cpu_credits':8,'native_calls_max':10,'inputs_max':7,'logical_states_max':16,'aggregate_seconds':300,'source_pins':{str(path.relative_to(ROOT)):sha(path) for path in [pathlib.Path(__file__).resolve(),ROOT/'tests/sdk_receive_pilot/guard.py',ROOT/'bench/adobe/phase.py',ROOT/'bench/sync/ownership.py',ROOT/'bench/sync/measure.py']},'builds':{}}
 for kind,receipt in [('stock',a.stock_build),('ox',a.ox_build)]:packet['builds'][kind]=contained_cli(receipt.resolve(),work/kind)
 fixtures=[]
 import struct
 for f in sdk['fixtures']['fixtures']:
  source=(a.fixtures/f['filename']).resolve();data=source.read_bytes();require(sha(source)==f['sha256'] and len(data)==f['size_bytes'],'fixture pin changed')
  require(f['positive']['receipt']['raw-digest']=='valid','original SDK positive missing')
  e='<' if data[:2]==b'II' else '>';require(data[:2] in (b'II',b'MM') and struct.unpack_from(e+'H',data,2)[0]==42,'fixture TIFF shape')
  offset=struct.unpack_from(e+'I',data,4)[0];count=struct.unpack_from(e+'H',data,offset)[0];require(count<=128,'bounded fixture directory')
  tags=[struct.unpack_from(e+'HHII',data,offset+2+12*i) for i in range(count)]
  xmp=[t for t in tags if t[0]==700];require(len(xmp)==1,'single XMP required');_,typ,length,start=xmp[0]
  require(typ==1 and 4<length<=1048576 and start+length<=len(data),'bounded XMP shape')
  original=work/(f['codec']+'-original.dng');original.write_bytes(data)
  packet_bytes=data[start:start+length];at=packet_bytes.index(b'xmp:MetadataDate="')+len(b'xmp:MetadataDate="');require(packet_bytes[at:at+4]==b'2026','fixture date anchor')
  target=data[:start]+packet_bytes[:at]+b'2027'+packet_bytes[at+4:]+data[start+length:]
  edited=work/(f['codec']+'-edited.dng');edited.write_bytes(target)
  fixtures.append({'codec':f['codec'],'original':str(original),'edited':str(edited),'original_sha256':sha(original),'edited_sha256':sha(edited),'xmp_bytes':length})
  if f['codec']=='uncompressed':
   digest=[t for t in tags if t[0]==51111];require(len(digest)==1 and digest[0][1:3]==(1,16),'known NewRawImageDigest shape required')
   damaged=bytearray(target);damaged[digest[0][3]]^=1;bad=work/'bad-raw-digest.dng';bad.write_bytes(damaged)
 packet['fixtures']=fixtures;packet['bad_digest']={'path':str(bad),'sha256':sha(bad)}
 packet['driver_manifest']={'path':str(a.driver_manifest.resolve()),'sha256':sha(a.driver_manifest),'executable':manifest['executable'],'executable_sha256':manifest['executable_sha256'],'build_id':manifest['build_id']}
 write(work/'READY.json',packet)
 print('Prepared:',work/'READY.json',flush=True)
 if a.mode=='prepare':return
 execute(packet,work,a.mode)

if __name__=='__main__':main()
