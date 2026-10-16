"""Actual disposable-lock worker refusals; zero probe/helper/SDK execution."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import shutil
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixed_validation import execute as entry,boundary
from mixed_validation.inventory import paths
from mixed_validation.plan_test import fixture
from sdk_multifile.clone import stamp
from private_camera_receiving.close import close_descriptors
from camera_sdk_concurrency.persistence import save
from shared_process_owner import retain_after_record
from shared_cpu_pool import UnresolvedOwnership
from mixed_validation.audit import audit as audit_task
import shared_binding
import shared_dispatch as dispatch

HERE=Path(__file__).resolve()


def artifact(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


class Lease:
    def __init__(self,directory,count):
        self.fds=[];self.closed=False
        try:
            for i in range(count):
                fd=os.open(directory/str(i),os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_CLOEXEC,0o600)
                self.fds.append(fd);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:close_descriptors(self.fds);raise
        self.fds=tuple(self.fds)
    def close_after_verified_settlement(self,**proof):
        assert not self.closed and all(v is True for v in proof.values())
        close_descriptors(self.fds);self.closed=True


def argv(plan,*,interpreter,plan_path,plan_sha256):
    return [interpreter,str(HERE),'--worker','--plan',plan_path,'--plan-sha256',plan_sha256,
            '--workspace',plan['workspace']]


def child():
    args=SimpleNamespace(plan=sys.argv[3],plan_sha256=sys.argv[5],workspace=sys.argv[7])
    plan=entry.checked_plan(args.plan,args.plan_sha256)
    inventory=entry.document(Path(args.workspace)/'DISPOSABLE-INVENTORY.json')
    def refuse(*a,**k):
        (Path(args.workspace)/'BOUNDARY-REACHED').write_text('actual inherited guard passed; no probes started\n')
        raise ValueError('deliberate pre-probe control refusal')
    actual_invoke=entry.invoke;calls=[]
    def fake_call(command,*a,**k):
        outcome=actual_invoke(command,*a,**k)
        ledger=dict(sdk=int(Path(command[1]).with_suffix('.calls').read_text()),
                    metadata=int(Path(command[2]).with_suffix('.calls').read_text()))
        audit_task(outcome,command=command,metadata_version='13.10',
                   expected_helpers=ledger,require_admission=True)
        (Path(args.workspace)/('FAKE-LEDGER-'+str(len(calls))+'.json')).write_text(json.dumps(ledger))
        calls.append(ledger)
        return outcome
    with ExitStack() as stack:
        stack.enter_context(patch.object(entry,'worker_argv',side_effect=argv))
        stack.enter_context(patch.object(boundary,'worker_argv',side_effect=argv))
        stack.enter_context(patch.object(shared_binding,'inventory',return_value=tuple(tuple(x) for x in inventory)))
        if not (Path(args.workspace)/'EXECUTE-FAKES').exists():
            stack.enter_context(patch.object(entry,'execute_plan',side_effect=refuse))
        else:stack.enter_context(patch.object(entry,'invoke',side_effect=fake_call))
        try:return entry.worker(args,plan)
        except ValueError as error:
            if not (Path(args.workspace)/'RESULT.json').exists():
                save(args.workspace,dict(schema='unison-mixed-validation-worker/1',complete=False,
                     phase='PREPARING_NO_CALL',invocations=[],failure=repr(error)))
            return 7
    raise AssertionError('control must refuse before probe')


def controls(*,success=False):
    root=Path(tempfile.mkdtemp(prefix='unison-mixed-lifecycle-',dir='/private/tmp'));cases=[]
    common=root/'inert';common.write_bytes(b'private inert artifact; never executed')
    stock=root/'stock';stock.write_bytes(b'inert stock')
    ox=root/'ox';ox.write_bytes(b'inert ox')
    source=root/'tiny-original.dng';source.write_bytes(b'authored tiny source');source.chmod(0o644)
    sdk=metadata=common
    if success:
        old=json.loads((HERE.parents[1]/'qualification/mixed-validation-memory-admission-actual-20261016.json').read_text())
        rows=[r for r in old['rows'] if r['label'] in ('stock','ox')]
        for row,destination in zip(rows,(stock,ox)):
            for name,digest in row['report']['sources'].items():
                assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
            shutil.copyfile(Path(row['report']['workspace'])/'probe',destination);destination.chmod(0o700)
        original=Path(rows[0]['report']['workspace'])/'pass'
        sdk=root/'validator.py';metadata=root/'metadata.py'
        sdk.write_text((original/'validator.py').read_text().replace('synthetic-mixed-v1','unison-sdk171-2724-v1-single'))
        metadata.write_text((original/'metadata.py').read_text().replace('synthetic-only','13.10'))
        sdk.chmod(0o700);metadata.chmod(0o700)
    for count in ((8,) if success else (8,7)):
        w=root/('case-'+str(count));w.mkdir(mode=0o700)
        for name in ('cpu','io'):(w/name).mkdir(mode=0o700)
        cpu=Lease(w/'cpu',count);io=Lease(w/'io',1)
        identities=[(os.fstat(fd).st_dev,os.fstat(fd).st_ino) for fd in cpu.fds]
        if count==7:identities.append((os.fstat(cpu.fds[0]).st_dev,999999999))
        identities.append((os.fstat(io.fds[0]).st_dev,os.fstat(io.fds[0]).st_ino))
        (w/'DISPOSABLE-INVENTORY.json').write_text(json.dumps(identities))
        plan=fixture();plan['workspace']=str(w)
        for row,executable in zip(plan['probes'],(stock,ox)):
            row['executable']=artifact(executable);row['build_receipt']=artifact(common)
        for k in ('executable','manifest'):plan['sdk'][k]=artifact(common)
        for k in ('executable','inventory'):plan['metadata'][k]=artifact(common)
        if success:
            plan['sdk']['executable']=artifact(sdk);plan['metadata']['executable']=artifact(metadata)
            (w/'EXECUTE-FAKES').write_text('authored fake tools only\n')
        plan['input']=artifact(source);plan['input_epoch']=stamp(os.lstat(source))
        plan['ancestry']=[artifact(common)];plan['source_pins']=[artifact(p) for p in paths()]
        p=w/'plan.json';p.write_text(json.dumps(plan));digest=artifact(p)['sha256']
        class CPU:
            def try_acquire(self,indexes):return cpu
        class IO:
            def try_acquire(self):return io
        io_pool=IO();deadline=entry.time.time()+60
        with patch.object(dispatch.Pool,'read',return_value=CPU()),\
             patch.object(dispatch,'checked_io_request',return_value=(io_pool,deadline)):
            code=dispatch.run(dispatch.MIXED_TARGET,argv(plan,interpreter=sys.executable,plan_path=str(p),plan_sha256=digest),
                              w,8,io_admission=dict(path='/disposable-admission-only',sha256='0'*64))
        closed=json.loads((w/'SHARED-CLOSED.json').read_text())
        proof=json.loads((w/'SHARED-SERVER-AUDIT.json').read_text())
        exit_proof=json.loads((w/'SHARED-WORKER-EXIT-AUDIT.json').read_text())
        expected_exit=0 if success else 7
        assert code==expected_exit and closed['child']['reaped'] and closed['child']['returncode']==expected_exit
        assert closed['child']['other_group_members_absent_before_reap'] and cpu.closed and io.closed
        assert proof['functional_status']==('PASSED' if success else 'FAILED') and proof['attempted_probes']==(2 if success else 0)
        assert exit_proof['worker_exit_bound'] is True and exit_proof['resource_release_authorized'] is False
        assert (w/'BOUNDARY-REACHED').exists()==(count==8 and not success)
        for folder,n in (('cpu',count),('io',1)):
            for i in range(n):
                fd=os.open(w/folder/str(i),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:close_descriptors([fd])
        cases.append(dict(workspace=str(w),descriptors=count+1,boundary_reached=count==8,
                          child=closed['child'],parent_audit=proof,exit_audit=exit_proof,inner_locks_closed=True,
                          fresh_inner_locks_reacquired=True))
    summary=dict(workspace=str(root),cases=cases,scope=('One actual worker/two compiled stock+Ox probes/four authored fake helpers/32hash tasks/native tiny clones; ' if success else 'Two actual Python refusal workers; ')+'disposable inherited flock descriptions/real parent prefix audit; admission, command entry script and inventory are explicit doubles; no canonicalIO/SDK/Photo')
    save(root,summary);print(json.dumps(summary),flush=True)


if __name__=='__main__':
    try:
        if sys.argv[1:2]==['--worker']:raise SystemExit(child())
        if sys.argv[1:]==['--controls']:controls()
        elif sys.argv[1:]==['--success-controls']:controls(success=True)
        else:raise ValueError('fixed controls or parent-owned worker only')
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print('MIXED_LIFECYCLE_RETAINED '+repr(error),flush=True))
