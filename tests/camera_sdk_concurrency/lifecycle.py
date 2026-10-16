"""Real Python header/FD probes with disposable inner locks; no receiving call."""
import fcntl,hashlib,json,os,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import execute as entry
import shared_dispatch as dispatch
from private_camera_receiving.close import close_descriptors
from persistence import save
HERE=Path(__file__).resolve()

class Lease:
    def __init__(self,directory,count):
        self.fds=[];self.closed=False
        try:
            for i in range(count):
                fd=os.open(directory/str(i),os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_CLOEXEC,0o600)
                self.fds.append(fd);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:
            close_descriptors(self.fds);raise
        self.fds=tuple(self.fds)
    def close_after_verified_settlement(self,**proof):
        assert all(v is True for v in proof.values()) and not self.closed
        close_descriptors(self.fds);self.closed=True

def argv(plan,digest,workspace):
    return [sys.executable,str(HERE),'--worker','--plan',str(plan),'--plan-sha256',digest,'--workspace',str(workspace)]

def child():
    path,digest,w=sys.argv[3],sys.argv[5],Path(sys.argv[7])
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    plan=json.loads(Path(path).read_text());args=SimpleNamespace(plan=path,plan_sha256=digest,workspace=str(w))
    real_sha=entry.artifact_sha
    def artifact(path):return 'a'*64 if str(path)==entry.PYTHON else real_sha(path)
    def refuse(*args,**kw):
        from synthetic_case import create_file
        create_file(w/'BOUNDARY-REACHED',b'header accepted; kernel deliberately unstarted')
        raise ValueError('original pre-receiving probe refusal')
    with patch.object(entry,'child_argv',side_effect=argv),patch.object(entry,'artifact_sha',side_effect=artifact), \
         patch.object(entry.worker,'execute',side_effect=refuse):
        try:entry.worker_entry(args,plan)
        except ValueError as error:
            save(w,dict(schema='unison-concurrent-synthetic-worker/1',complete=False,phase='PREPARING_NO_CALL',
                invocations=[],cases=[],sdk_validation_claimed=False,semantic_eligibility_claimed=False,failure=str(error)))
            return 7
    raise AssertionError('real receiving kernel must never run')

def controls():
    root=Path(tempfile.mkdtemp(prefix='u-crs-fd-',dir='/private/tmp'));root.chmod(0o700);cases=[]
    for count in (8,7):
        w=root/str(count);w.mkdir(mode=0o700)
        plan=dict(workspace=str(w),tool=dict(build_id=entry.worker.BUILD),interpreter=dict(sha256='a'*64))
        path=w/'plan.json';path.write_text(json.dumps(plan));digest=hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ('cpu','io'):(w/name).mkdir(mode=0o700)
        cpu,io=Lease(w/'cpu',count),Lease(w/'io',1)
        class CPU:
            def try_acquire(self,indexes):return cpu
        class IO:
            def try_acquire(self):return io
        io_pool=IO();deadline=entry.time.time()+60
        with patch.object(dispatch.Pool,'read',return_value=CPU()), \
             patch.object(dispatch,'checked_io_request',return_value=(io_pool,deadline)):
            code=dispatch.run(entry.TARGET,argv(path,digest,w),w,8,io_admission=dict(path='/disposable-only',sha256='0'*64))
        closed=json.loads((w/'SHARED-CLOSED.json').read_text());result=json.loads((w/'RESULT.json').read_text())
        proof=json.loads((w/'SHARED-SERVER-AUDIT.json').read_text())
        assert code==7 and cpu.closed and io.closed and closed['child']['reaped']
        assert closed['child']['returncode']==7 and closed['child']['other_group_members_absent_before_reap']
        assert (w/'BOUNDARY-REACHED').exists()==(count==8)
        assert result['failure']==('original pre-receiving probe refusal' if count==8 else 'nine inherited descriptions required')
        assert proof['functional_status']=='FAILED' and proof['attempted_cli_invocations']==0
        for folder,n in [('cpu',count),('io',1)]:
            for index in range(n):
                fd=os.open(w/folder/str(index),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:close_descriptors([fd])
        cases.append(dict(workspace=str(w),inherited_descriptors=count+1,entry_passed=count==8,
                          actual_child=closed['child'],disposable_locks_closed=True,fresh_lock_reacquisition=True,parent_audit=proof))
    summary=dict(workspace=str(root),cases=cases,
        scope='actual2Python header children/disposable inner flock+FD inheritance; parent admission/command and interpreter hash are explicit doubles; kernel always refused; no canonical IO/receiving/helper/SDK/Photo')
    save(root,summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':
    if sys.argv[1:2]==['--worker']:raise SystemExit(child())
    if sys.argv[1:]==['--controls']:controls();raise SystemExit(0)
    raise ValueError('fixed --controls or owned --worker only')
