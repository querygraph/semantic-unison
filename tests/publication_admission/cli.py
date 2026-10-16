"""Two tiny real receiving calls with a fake Python validator, never Adobe."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
sys.path.insert(0,str(ROOT/'tests/private_camera_receiving'))
sys.path.insert(0,str(ROOT/'tests/validation_process'))
from invocation_journal import Journal,audit_attempted
from run import measure_invocation,InvocationFailure,save
from transport import prepare
import records

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-result',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();build=json.loads(a.build_result.read_text());binary=Path(build['workspace'])/'src/unison'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert str(binary)==build['binary'] and sha(binary)==build['binary_sha256']
assert sha(ROOT/'src/semanticRuntime.ml')==build['source_sha256']['src/semanticRuntime.ml']
spec=importlib.util.spec_from_file_location('original_fake_validation_fixture',ROOT/'tests/validation_paths/run.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
w=Path(tempfile.mkdtemp(prefix='unison-publication-admission-cli-',dir='/private/tmp'))
print(w,flush=True);result={'invocations':[],'cases':[],'scope':'two real CLI calls/tiny original bytes/fake Python driver only; no SDK/camera/Photo'}
journal=Journal(result,lambda:save(a.report,result))
for name,memory,success in (('too-large',64,False),('fits',4,True)):
 d=w/name;d.mkdir(mode=0o700)
 for n in ('left','right','state'):(d/n).mkdir(mode=0o700)
 prepare(d)
 source=d/'left/image.dng';data=b'original synthetic non-photographic admission fixture';source.write_bytes(data)
 driver=d/'original-fake-validator.py';driver.write_text(fixture.DRIVER);driver.chmod(0o700)
 driver.with_suffix('.control.json').write_text(json.dumps({'destination':str(d/'right/image.dng'),
     'mode':'pass','build':'fake-publication-admission-1','endpoint':'server'}))
 flags=['-clone','off','-semanticdng=false','-semanticworkers','2','-maxthreads','1',
        '-semanticmaxinflight','1','-semanticpayloadbudget','8','-semanticdescriptorbudget','64',
        '-adobevalidate','require','-adobevalidator',str(driver),'-adobevalidatorhash',sha(driver),
        '-adobevalidatorbuild','fake-publication-admission-1','-adobevalidatorthreads','1',
        '-adobevalidatorworkspace',str(memory),'-validationtreememory','0',
        '-debug','validation-process','-debug','validation-group']
 argv=[str(binary),str(d/'left'),'ssh://localhost/'+str(d/'right'),'-sshcmd',str(d/'launcher.py'),
       '-servercmd',str(binary),'-batch','-auto','-fastcheck','false',*flags]
 env=dict(os.environ,UNISON=str(d/'state'),UNISON_SYNC_BENCH_BINARY=str(binary),
          UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
          UNISON_SYNC_BENCH_PROXY_RECEIPT=str(d/'proxy-result.json'),
          UNISON_SYNC_BENCH_SOCKET=str(d/'rpc.sock'),UNISON_SYNC_BENCH_DEADLINE_SECONDS='20')
 journal.begin({'label':'stock' if '+ox' not in build['compiler_version'] else 'ox',
     'mode':'ordinary','workers':2,'directory':str(d),'stage':'seed'},argv)
 try:outcome=measure_invocation(argv,env,15,d/'proxy.py',strict_group_settlement=True)
 except InvocationFailure as error:outcome=error.outcome
 journal.finish(outcome)
 audit=audit_attempted(result)
 log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
 assert 'Unison server failed: Uncaught exception' not in log,log
 assert outcome['proxy']['server_returncode']==0 and outcome['supervisor_cleanup']['returncode']==0,outcome
 assert source.read_bytes()==data
 if success:
  assert outcome['returncode']==0 and (d/'right/image.dng').read_bytes()==data,outcome
  helpers,groups=records.parse(log),records.parse_groups(log)
  assert len(helpers)==len(groups)==1
  assert helpers[0].pid==groups[0].pid and helpers[0].status==('exit',0)
  assert groups[0].observation=='observed' and groups[0].other_members==0
  assert len(driver.with_suffix('.calls.jsonl').read_text().splitlines())==1
 else:
  assert outcome['returncode']!=0 and 'Receiving resource admission: semantic reservation exceeds' in log,log
  assert not list((d/'right').iterdir()) and not driver.with_suffix('.calls.jsonl').exists()
  assert not records.parse(log) and not records.parse_groups(log)
 result['cases'].append({'name':name,'passed':True,'source_unchanged':True,
      'fake_helper_calls':1 if success else 0,'server_closed_normally':True})
 save(a.report,result)
result.update(complete=True,audit=audit_attempted(result),binary_sha256=sha(binary),
    runtime_source_sha256=sha(ROOT/'src/semanticRuntime.ml'))
save(a.report,result)
