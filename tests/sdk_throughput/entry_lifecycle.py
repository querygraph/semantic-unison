"""Real child/FD boundary refusals; disposable inner grants and zero SDK calls."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
from sdk_throughput import entry,worker
import shared_binding
import shared_dispatch as dispatch
from lifecycle import Lease
from persistence import save
from private_camera_receiving.close import close_descriptors
HERE=Path(__file__).resolve()


def argv(path,digest,workspace):
    return [sys.executable,str(HERE),'--worker','--plan',str(path),'--plan-sha256',digest,'--workspace',str(workspace)]


def child():
    path,digest,w=Path(sys.argv[3]),sys.argv[5],Path(sys.argv[7])
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
    plan=json.loads(raw);real_sha=entry.artifact_sha
    def artifact(p):
        return 'a'*64 if str(p)==entry.PYTHON or str(p).startswith('/inert/') else real_sha(p)
    def refuse(*args,**kwargs):
        (w/'BOUNDARY-REACHED').write_text('guard accepted; receiving and SDK deliberately unstarted\n')
        raise ValueError('original pre-SDK worker refusal')
    with patch.object(entry,'child_argv',side_effect=argv),patch.object(entry,'artifact_sha',side_effect=artifact), \
         patch.object(shared_binding,'inventory',return_value=tuple(tuple(x) for x in plan['disposable_inventory'])), \
         patch.object(worker,'execute',side_effect=refuse),patch('sdk_multifile.clone.prepare_inputs',side_effect=AssertionError('no clone permitted')):
        try:entry.worker_entry(SimpleNamespace(plan=str(path),plan_sha256=digest,workspace=str(w)),plan)
        except ValueError as error:
            save(w,dict(schema='unison-sdk-receiving-comparison-worker/1',complete=False,phase='PREPARING_NO_CALL',cases=[],invocations=[],
                        semantic_eligibility_claimed=False,pixel_equivalence_claimed=False,throughput_qualified=False,failure=str(error)))
            return 7
    raise AssertionError('worker must refuse')


def controls():
    root=Path(tempfile.mkdtemp(prefix='u-st-boundary-',dir='/private/tmp'));root.chmod(0o700);cases=[]
    for count in (8,7):
        w=root/str(count);w.mkdir(mode=0o700)
        for name in ('cpu','io'):(w/name).mkdir(mode=0o700)
        cpu,io=Lease(w/'cpu',count),Lease(w/'io',1)
        plan=dict(workspace=str(w),inputs=[],sources=[],interpreter=dict(sha256='a'*64),
                  binaries={k:dict(label=k,path='/inert/'+k,sha256='a'*64) for k in ('stock','ox')},
                  tool=dict(path='/inert/sdk',sha256='a'*64,build_id=entry.BUILD,threads=1),
                  disposable_inventory=[(os.fstat(fd).st_dev,os.fstat(fd).st_ino) for fd in cpu.fds+io.fds])
        path=w/'plan.json';path.write_text(json.dumps(plan)+'\n');digest=hashlib.sha256(path.read_bytes()).hexdigest()
        class CPU:
            def try_acquire(self,indexes):return cpu
        class IO:
            def try_acquire(self):return io
        with patch.object(dispatch.Pool,'read',return_value=CPU()),patch.object(dispatch,'checked_io_request',return_value=(IO(),time.time()+60)):
            code=dispatch.run(entry.TARGET,argv(path,digest,w),w,8,io_admission=dict(path='/disposable-only',sha256='0'*64))
        closed=json.loads((w/'SHARED-CLOSED.json').read_text());proof=json.loads((w/'SHARED-SERVER-AUDIT.json').read_text())
        result=json.loads((w/'RESULT.json').read_text())
        assert code==7 and cpu.closed and io.closed and closed['child']['reaped']
        assert closed['child']['returncode']==7 and closed['child']['other_group_members_absent_before_reap']
        assert (w/'BOUNDARY-REACHED').exists()==(count==8)
        assert result['failure']==('original pre-SDK worker refusal' if count==8 else 'exact9inherited descriptions required')
        assert proof['functional_status']=='FAILED' and proof['attempted_cli_invocations']==0
        for folder,n in [('cpu',count),('io',1)]:
            for i in range(n):
                fd=os.open(w/folder/str(i),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:close_descriptors([fd])
        cases.append(dict(inherited_descriptors=count+1,boundary_reached=count==8,workspace=str(w),child=closed['child'],parent_audit=proof,fresh_disposable_locks_reacquired=True))
    summary=dict(cases=cases,scope='Two actual Python children and real inherited FD guard/parent failed-prefix audit. Disposable inner pools; admission, inventory, child argv and artifact SHA explicitly doubled. Zero clone/CLI/SDK/payload/canonical IO; no native qualification.')
    save(root,summary);print(json.dumps(dict(workspace=str(root),cases=2,sdk_calls=0,children_reaped=True)))


if __name__=='__main__':
    if sys.argv[1:2]==['--worker']:raise SystemExit(child())
    if sys.argv[1:]==['--controls']:controls()
    else:raise ValueError('fixed --controls or owned --worker only')
