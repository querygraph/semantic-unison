"""Original fake-helper composition only; no native SDK execution mode exists."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/camera_sdk_concurrency'))
from persistence import save
from shared_kernel import Kernel
from shared_child import invoke
from shared_result import audit
from shared_plan import REFERENCE,EXPERIMENTAL
HELPER='''#!PYTHON
import os,sys
args=sys.argv;experimental='--host-memory-bytes' in args
threads=int(args[args.index('--threads')+1]);mode=os.environ['UNISON_ORIGINAL_MATRIX_FAKE']
fields=[('candidate-sha256',args[args.index('--expected-sha256')+1]),('candidate-size',args[args.index('--expected-size')+1]),
('driver-build','unison-sdk171-2724-v3-area-memory-unqualified' if experimental else 'unison-sdk171-2724-v1-single'),
('structure','valid'),('decode','success'),('raw-digest','valid'),('errors','0'),('warnings','1' if experimental and mode=='warning' else '0')]
print('UNISON-DNG-VALIDATION 1\\n'+'\\n'.join(k+' '+v for k,v in fields)+'\\nEND')
if experimental and mode!='missing':
 area='tasks=0 started=0 finish=0 calls=0 active=0 peak=0 max-partition=0 reference=1' if threads==1 else f'tasks=1 started=1 finish=1 calls={threads} active=0 peak={threads} max-partition={threads} reference=0'
 print('UNISON-HOST-AREA 1 '+area,file=sys.stderr)
 print('UNISON-HOST-MEMORY 1 limit=1073741824 used=0 peak=4096 live=0 denied=0',file=sys.stderr)
'''

def controls(directory):
    root=Path(directory)
    if not root.is_absolute() or root.exists():raise ValueError('fresh private component namespace required')
    root.mkdir(mode=0o700)
    helper=root/'original-fake.py';helper.write_text(HELPER.replace('PYTHON',sys.executable));helper.chmod(0o700)
    reference=dict(executable=str(helper),build_id=REFERENCE)
    experimental=dict(executable=str(helper),build_id=EXPERIMENTAL)
    fixtures=[dict(codec=c,path='/inert-never-opened/'+c,sha256=str(i+1)*64,size=123+i) for i,c in enumerate(['uncompressed','jpeg','jxl'])]
    cases=[]
    for mode,expected in [('pass',12),('warning',2),('missing',2)]:
        work=root/mode;work.mkdir(mode=0o700);kernel=Kernel(reference,experimental,fixtures,1073741824);calls=[]
        def call(case):
            out=invoke(case['command'],dict(os.environ,UNISON_ORIGINAL_MATRIX_FAKE=mode),time.monotonic()+5)
            calls.append(out);return out
        failure=None
        try:result=kernel.execute(invoke=call,persist=lambda d:save(work,d))
        except ValueError as error:failure=repr(error);result=json.loads((work/'RESULT.json').read_text())
        assert len(calls)==expected
        assert all(o['client_cleanup']['reaped'] and o['client_cleanup']['other_group_members_absent_before_reap'] and o['returncode']==0 for o in calls)
        assert all(e['state']=='OUTCOME' for e in result['invocations'])
        if mode=='pass':
            assert result['complete'];audit(reference,experimental,fixtures,1073741824,result['rows'])
        else:assert not result['complete'] and failure and len(result['invocations'])==2
        cases.append(dict(mode=mode,calls=len(calls),functional_complete=result['complete'],failure=failure,
                          result_path=str(work/'RESULT.json'),result_sha256=hashlib.sha256((work/'RESULT.json').read_bytes()).hexdigest()))
    save(root,dict(cases=cases,actual_original_fake_children=16,sdk_calls=0,
        scope='12success +2warning-divergence +2missing-telemetry original fake-helper calls; exactjournal/actualdirectgroupwait/boundedcapture/durablepersist/functionaljoin. Inert fixture paths never opened. Fake protocol fields are NOT SDK verification.',
        native_runtime_qualified=False,io_cpu_release_authorized=False))
    print(json.dumps(dict(workspace=str(root),cases=cases,actual_original_fake_children=16,sdk_calls=0)))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--controls',required=True,type=Path);a=p.parse_args();controls(a.controls)
