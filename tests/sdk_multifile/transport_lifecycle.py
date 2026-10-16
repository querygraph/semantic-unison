"""Real loopback transport with original tiny endpoints; zero SDK/native calls."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
from sdk_multifile import worker
from sdk_multifile.plan import BUILD
from invocation import SCRIPT_NAMES,artifact_sha
from persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def controls():
    w=Path(tempfile.mkdtemp(prefix='u-smr-wire-',dir='/private/tmp'));w.chmod(0o700)
    endpoint=w/'original-endpoint';source=Path(__file__).with_name('fake_endpoint.py')
    endpoint.write_text('#!'+sys.executable+'\n'+source.read_text().replace("ROOT=Path(__file__).resolve().parents[2]",'ROOT=Path('+repr(str(ROOT))+')'))
    endpoint.chmod(0o700)
    inert=w/'never-executed-sdk';inert.write_text('Original non-executable test sentinel; no SDK code.\n')
    data={'uncompressed.dng':b'original tiny wire first', 'jpeg.dng':b'original distinct wire second'}
    sources=[dict(candidate_id=n,sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for n,v in data.items()]
    plan=dict(workspace=str(w),sources=sources,tool=dict(path=str(inert),sha256=artifact_sha(inert),threads=1,build_id=BUILD),
              binaries={label:dict(label=label,path=str(endpoint),sha256=artifact_sha(endpoint)) for label in ('stock','ox')},
              transport_source_sha256={n:artifact_sha(ROOT/'bench/sync'/n) for n in SCRIPT_NAMES})
    def prepare(d,label):
        for name,value in data.items():
            with (d/'left'/name).open('xb') as f:f.write(value)
        return dict(original_tiny_preparation=True,native_clone_proved=False)
    result=worker.execute(plan,w,time.monotonic()+200,prepare_sources=prepare,
                          read_proxy=lambda path:json.loads(path.read_text()),persist=lambda value:save(w,value))
    assert result['complete'] and result['parent_audit']['sdk_helpers_settled']==4
    helpers=[];launchers=[]
    for label in ('stock','ox'):
        d=w/label;hs=json.loads((d/'ORIGINAL-HELPERS.json').read_text());launcher=json.loads((d/'ORIGINAL-LAUNCHER.json').read_text())
        assert len(hs)==2
        for out in hs+[launcher]:
            assert out['returncode']==0 and out['client_cleanup']['reaped'] and out['client_cleanup']['other_group_members_absent_before_reap']
        helpers+=hs;launchers.append(launcher)
    assert len({o['client_cleanup']['pid'] for o in helpers})==4
    summary=dict(worker_result=result,original_helpers=helpers,original_launchers=launchers,
                 scope='Actual worker/Invoker/copied proxy+launcher/2original clients/2original servers/4Python hash helpers. Synthetic SDK protocol only; fake endpoints are not Unison/compiler builds. Zero SDK/retained payload/canonical IO/native clone; no actual receiving qualification.')
    (w/'CONTROL-RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(workspace=str(w),actual_original_clients=2,actual_original_servers=2,actual_original_helpers=4,sdk_calls=0)),flush=True)


if __name__=='__main__':
    try:controls()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),flush=True))
