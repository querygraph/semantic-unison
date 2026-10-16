"""Actual shared SDK worker-boundary refusals; disposable grants, zero SDK calls."""
import fcntl,hashlib,json,os,sys,tempfile,time
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch
import shared_execute as entry
import shared_binding
import shared_dispatch as dispatch
from persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
sys.path.insert(0,str(entry.ROOT/'tests/camera_sdk_concurrency'))
from lifecycle import Lease
from synthetic_case import create_file
from private_camera_receiving.close import close_descriptors
HERE=Path(__file__).resolve()
def argv(path,digest,workspace):return [sys.executable,str(HERE),'--worker','--plan',str(path),'--plan-sha256',digest,'--workspace',str(workspace)]
def child():
    path,digest,w=Path(sys.argv[3]),sys.argv[5],Path(sys.argv[7]);raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
    plan=json.loads(raw);args=SimpleNamespace(plan=str(path),plan_sha256=digest,workspace=str(w));real_sha=entry.artifact_sha
    def artifact(p):
        if str(p)==entry.PYTHON or str(p).startswith('/inert/'):return 'a'*64
        return real_sha(p)
    original_kernel=entry.Kernel
    def refuse(*args,**kw):
        create_file(w/'BOUNDARY-REACHED',b'inherited guard accepted; SDK call kernel deliberately unstarted')
        if plan['control_mode']=='fake':return original_kernel(*args,**kw)
        raise ValueError('original pre-SDK boundary refusal')
    with patch.object(entry,'child_argv',side_effect=argv),patch.object(entry,'artifact_sha',side_effect=artifact), \
         patch.object(shared_binding,'inventory',return_value=tuple(tuple(x) for x in plan['disposable_inventory'])),patch.object(entry,'Kernel',side_effect=refuse):
        try:return entry.worker(args,plan)
        except ValueError as error:
            save(w,dict(schema='unison-shared-sdk-kernel/1',complete=False,phase='PREPARING_NO_CALL',rows=[],invocations=[],resource_release_authorized=False,failure=repr(error)))
            return 7
    raise AssertionError('SDK kernel must never execute')
def controls():
    root=Path(tempfile.mkdtemp(prefix='u-shm-entry-',dir='/private/tmp'));root.chmod(0o700);cases=[]
    for mode,count in [('refuse',8),('refuse',7),('fake',8)]:
        w=root/(mode+'-'+str(count));w.mkdir(mode=0o700)
        for name in ['cpu','io']:(w/name).mkdir(mode=0o700)
        cpu,io=Lease(w/'cpu',count),Lease(w/'io',1)
        fixtures=[]
        for i,codec in enumerate(['uncompressed','jpeg','jxl']):
            p=w/('tiny-'+str(i));create_file(p,b'fake');st=p.stat()
            fixtures.append(dict(codec=codec,path=str(p),sha256=hashlib.sha256(b'fake').hexdigest(),size=4,identity={k:getattr(st,k) for k in entry.FIELDS}))
        plan=dict(control_mode=mode,workspace=str(w),tools={k:dict(executable='/inert/'+k,sha256='a'*64,build_id=b) for k,b in [('reference',entry.REFERENCE),('experimental',entry.EXPERIMENTAL)]},
            fixtures=fixtures,host_memory_bytes=1073741824,interpreter=dict(sha256='a'*64),disposable_inventory=[(os.fstat(fd).st_dev,os.fstat(fd).st_ino) for fd in cpu.fds+io.fds])
        if mode=='fake':
            from shared_component import HELPER
            helper=w/'original-fake.py'
            text=HELPER.replace('PYTHON',sys.executable).replace("os.environ['UNISON_ORIGINAL_MATRIX_FAKE']","'pass'")
            create_file(helper,text.encode());helper.chmod(0o700)
            for tool in plan['tools'].values():tool.update(executable=str(helper),sha256=hashlib.sha256(helper.read_bytes()).hexdigest())
        path=w/'plan.json';path.write_text(json.dumps(plan)+'\n');digest=hashlib.sha256(path.read_bytes()).hexdigest()
        class CPU:
            def try_acquire(self,indexes):return cpu
        class IO:
            def try_acquire(self):return io
        pool=IO();deadline=time.time()+60
        with patch.object(dispatch.Pool,'read',return_value=CPU()),patch.object(dispatch,'checked_io_request',return_value=(pool,deadline)):
            code=dispatch.run(entry.TARGET,argv(path,digest,w),w,8,io_admission=dict(path='/disposable-only',sha256='0'*64))
        closed=json.loads((w/'SHARED-CLOSED.json').read_text());proof=json.loads((w/'SHARED-SERVER-AUDIT.json').read_text())
        expected_exit=0 if mode=='fake' else 7
        assert code==expected_exit and cpu.closed and io.closed and closed['child']['reaped'] and closed['child']['returncode']==expected_exit and closed['child']['other_group_members_absent_before_reap']
        assert (w/'BOUNDARY-REACHED').exists()==(count==8)
        assert proof['attempted_direct_calls']==(12 if mode=='fake' else 0) and proof['functional_status']==('PASSED' if mode=='fake' else 'FAILED')
        for folder,n in [('cpu',count),('io',1)]:
            for i in range(n):
                fd=os.open(w/folder/str(i),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:close_descriptors([fd])
        cases.append(dict(control_mode=mode,workspace=str(w),inherited_fds=count+1,boundary_reached=count==8,parent_proof=proof,child=closed['child'],disposable_descriptors_closed=True,fresh_disposable_locks_reacquired=True))
    save(root,dict(cases=cases,scope='3actualPython workerchildren/newtarget parentaudit/realinheritedFDguard; twozero-callrefusals +onecomplete12originalfakehelpercalls. Admission/canonicalinventory/childargv/interpreterSHA are explicitdoubles; tinyfixtures/fakehelperSHA real. ZeroSDK/Photo/camera/canonicalEXIO.'))
    print(json.dumps(dict(workspace=str(root),cases=3,actual_children_reaped=True,actual_fake_helpers=12,sdk_calls=0)))
if __name__=='__main__':
    try:
        if sys.argv[1:2]==['--worker']:raise SystemExit(child())
        if sys.argv[1:]==['--controls']:controls()
        else:raise ValueError('fixed worker or --controls only')
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='BOUNDARY_OWNERSHIP_RETAINED',error=repr(error),retained_fds=error.retained_fds)),flush=True))
