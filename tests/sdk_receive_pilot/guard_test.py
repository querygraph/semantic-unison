#!/usr/bin/env python3
"""Finite process/argv/call-cap controls; fake executable only, no SDK."""
import hashlib,json,os,pathlib,shutil,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[2]
work=pathlib.Path(tempfile.mkdtemp(prefix='unison-receive-guard-',dir='/private/tmp'))
source=root/'tests/sdk_receive_pilot/guard.py';guard=work/'guard.py';shutil.copyfile(source,guard);guard.chmod(0o700)
fixture=work/'original.dng';fixture.write_bytes(b'original finite guard bytes')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mock=work/'mock.py';mock.write_text('#!/usr/bin/python3\nprint("original mock callee entered")\n');mock.chmod(0o700)
calls=work/'calls';calls.mkdir()
config={'workspace':str(work),'group':os.getpgid(0),'calls':str(calls),'executable':str(mock),'executable_sha256':sha(mock),'allowed_sha256':[sha(fixture)],'mode':'MOCK'}
def save():guard.with_suffix('.json').write_text(json.dumps(config))
save();args=['--unison-dng-validation-v1','--expected-sha256',sha(fixture),'--expected-size',str(fixture.stat().st_size),'--threads','1','--',str(fixture)]
def invoke(good):
 r=subprocess.run([str(guard),*args],capture_output=True,text=True,timeout=5,env=dict(os.environ,PYTHONOPTIMIZE='1'))
 assert (r.returncode==0)==good,r.stdout+r.stderr
 assert ('original mock callee entered' in r.stdout)==good
 return r
config['group']+=100000;save();invoke(False);assert not list(calls.iterdir())
config['group']=os.getpgid(0);config['executable_sha256']='0'*64;save();invoke(False);assert not list(calls.iterdir())
config['executable_sha256']=sha(mock);config['allowed_sha256']=[];save();invoke(False);assert not list(calls.iterdir())
config['allowed_sha256']=[sha(fixture)];save()
for _ in range(10):invoke(True)
requirement=invoke(False);assert 'finite SDK call cap reached' in requirement.stderr
assert len(list(calls.iterdir()))==10
receipt={'scope':'guard-only finite controls; mock executable, zero SDK calls','workspace':str(work),'positive_mock_entries':10,'rejected_before_entry':['wrong group','wrong executable pin','unlisted input','eleventh call'],'guard_sha256':sha(source),'actual_processes':14,'sdk_calls':0}
(work/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
