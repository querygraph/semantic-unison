"""Actual24-row original-fake loopback controls; no SDK or retained payload."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
from sdk_throughput import worker
from sdk_throughput.plan import comparison
from sdk_throughput.audit import audit
from sdk_multifile.plan import BUILD
from invocation import SCRIPT_NAMES,artifact_sha
from persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def controls():
    w=Path(tempfile.mkdtemp(prefix='u-st-wire-',dir='/private/tmp'));w.chmod(0o700)
    source=ROOT/'tests/sdk_multifile/fake_endpoint.py';text=source.read_text()
    guard="if not d.name in ('stock','ox') or not d.parent.name.startswith('u-smr-wire-'):"
    assert text.count(guard)==1
    text=text.replace(guard,"if d.name not in ('stock-w1','stock-w3','ox-w1','ox-w3') or d.parent.name not in ('r0','r1','r2','r3','r4','r5') or not d.parent.parent.name.startswith('u-st-wire-'):")
    text=text.replace('ROOT=Path(__file__).resolve().parents[2]','ROOT=Path('+repr(str(ROOT))+')')
    endpoint=w/'original-endpoint';endpoint.write_text('#!'+sys.executable+'\n'+text);endpoint.chmod(0o700)
    sentinel=w/'never-executed-sdk';sentinel.write_text('Original non-executable sentinel, not SDK code.\n')
    data={'uncompressed.dng':b'original tiny comparison one','jpeg.dng':b'original distinct comparison two'}
    plan=dict(workspace=str(w),sources=[dict(candidate_id=n,sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for n,v in data.items()],
              binaries={label:dict(label=label,path=str(endpoint),sha256=artifact_sha(endpoint)) for label in ('stock','ox')},
              tool=dict(path=str(sentinel),sha256=artifact_sha(sentinel),build_id=BUILD,threads=1),
              transport_source_sha256={n:artifact_sha(ROOT/'bench/sync'/n) for n in SCRIPT_NAMES})
    (w/'CONTROL-PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    def prepare(d,row):
        for name,value in data.items():
            with (d/'left'/name).open('xb') as f:f.write(value)
        return dict(original_tiny_preparation=True,native_clone_proved=False)
    result=worker.execute(plan,w,time.monotonic()+200,prepare_sources=prepare,
                          read_proxy=lambda q:json.loads(q.read_text()),persist=lambda value:save(w,value))
    rows=comparison(plan['binaries'],plan['tool'],w)['rows']
    proof=audit(result,plan,raw_proxy_receipts=[json.loads((Path(r['directory'])/'seed-proxy.json').read_text()) for r in rows])
    assert result['complete'] and proof['sdk_helpers_settled']==48 and proof['measured_rows']==20
    helpers=[];launchers=[]
    for row in rows:
        d=Path(row['directory']);hs=json.loads((d/'ORIGINAL-HELPERS.json').read_text());launcher=json.loads((d/'ORIGINAL-LAUNCHER.json').read_text())
        assert len(hs)==2
        for out in hs+[launcher]:
            assert out['returncode']==0 and out['client_cleanup']['reaped'] and out['client_cleanup']['other_group_members_absent_before_reap']
        helpers+=hs;launchers.append(launcher)
        for source in plan['sources']:
            for side in ('left','right'):
                assert artifact_sha(d/side/source['candidate_id'])==source['sha256']
    assert len(helpers)==48 and len(launchers)==24
    receipt=dict(parent_audit=proof,original_helper_outcomes=helpers,original_launcher_outcomes=launchers,
                 scope='Actual24row worker/Invoker/copied loopback transport with24original fake clients/servers and48Python hash helpers. SDK frames synthetic; no SDK/Unison binary/retained payload/canonical IO/native clone. Timings are control-process timings only, never a receiving benchmark.')
    (w/'CONTROL-RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(workspace=str(w),rows=24,actual_original_helpers=48,actual_launchers=24,sdk_calls=0,retained_payload_reads=0)),flush=True)


if __name__=='__main__':
    try:controls()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
