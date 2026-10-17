"""Real disposable worker lifecycle; explicit plan/admission/inventory doubles.

No canonical IO, SDK, Adobe or retained media. Run only --controls under CPU8.
"""
from contextlib import ExitStack
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

import private_maker_execute as entry
import private_maker_slice as slice_reader
from private_maker_plan_test import fixture
from private_maker_shape_test import fixture as tiny_bytes
from private_camera_receiving.close import close_descriptors
from shared_io_pool import UnresolvedIOOwnership,descriptor_observation
from shared_process_owner import retain_after_record
from shared_cpu_pool import UnresolvedOwnership
import shared_dispatch as dispatch

sys.path.insert(0,str(Path(__file__).resolve().parent/'sdk_host_matrix'))
import shared_binding
HERE=Path(__file__).resolve()


class Lease:
    def __init__(self,directory,count):
        self.fds=[];self.closed=False
        try:
            for index in range(count):
                fd=os.open(directory/str(index),os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o600)
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
    plan=entry.document(args.plan,args.plan_sha256);work=Path(args.workspace)
    inventory=entry.document(work/'DISPOSABLE-INVENTORY.json')
    def injected_close(fds):
        # This original fake raises BEFORE any OS close attempt. Do not retry:
        # the fd deliberately stays open until this control worker exits.
        assert len(fds)==1
        observation=descriptor_observation(fds[0],'injected_no_OS_close_attempt')
        raise UnresolvedIOOwnership('injected source-close uncertainty',uncertain_closes=[observation])
    with ExitStack() as stack:
        stack.enter_context(patch.object(entry,'worker_argv',side_effect=argv))
        stack.enter_context(patch.object(shared_binding,'inventory',return_value=tuple(tuple(r) for r in inventory)))
        if (work/'INJECT-CLOSE').exists():
            stack.enter_context(patch.object(slice_reader,'close_descriptors',side_effect=injected_close))
        try:return entry.worker(args,plan)
        except UnresolvedOwnership as error:
            entry.save(work/'SLICE-OWNERSHIP-RETAINED.json',dict(worker_pid=os.getpid(),
                uncertain_closes=list(error.uncertain_closes),numeric_close_retry=False,
                injection_preceded_any_OS_close_attempt=True))
            # A test-specific recovery acknowledgement permits process exit,
            # not retrying the uncertain descriptor number or claiming close.
            while not (work/'CONTROL-EXIT-ACK').exists():time.sleep(.005)
            return 7


def controls():
    root=Path(tempfile.mkdtemp(prefix='unison-maker-lifecycle-',dir='/private/tmp'));cases=[]
    for mode in ('candidate','declined','stale-source','uncertain-close'):
        work=root/mode;work.mkdir(mode=0o700)
        for name in ('cpu','io'):(work/name).mkdir(mode=0o700)
        cpu=Lease(work/'cpu',8);io=Lease(work/'io',1)
        original=work/'authored-tiny';original.write_bytes(tiny_bytes(kind=99 if mode=='declined' else 7))
        original.chmod(0o400);epoch=slice_reader.stamp(os.lstat(original))
        plan=fixture();plan['workspace']=str(work)
        plan['source']=dict(path=str(original),identity=dict(epoch))
        plan['geometry']=dict(payload_offset=0,payload_length=128,original_offset=1000,
            byte_order='little',ifd_offset=0,max_requested_read_bytes=3078)
        if mode=='stale-source':plan['source']['identity']['st_ino']+=1
        if mode=='uncertain-close':(work/'INJECT-CLOSE').write_text('explicit no-OS-close fake\n')
        plan_path=work/'plan.json';entry.save(plan_path,plan)
        digest=hashlib.sha256(plan_path.read_bytes()).hexdigest()
        inherited=cpu.fds+io.fds
        entry.save(work/'DISPOSABLE-INVENTORY.json',[[os.fstat(fd).st_dev,os.fstat(fd).st_ino] for fd in inherited])
        class CPU:
            def try_acquire(self,indexes):assert indexes==tuple(range(8));return cpu
        class IO:
            def try_acquire(self):return io
        io_pool=IO();deadline=time.time()+60;owners=[];actual_factory=dispatch.OwnedGroup
        def owner(*a,**k):
            current=actual_factory(*a,**k);owners.append(current)
            if mode=='uncertain-close':
                original_wait=current.await_terminal
                current.await_terminal=lambda seconds:original_wait(min(seconds,.5))
            return current
        class RetentionObserved(BaseException):pass
        def fresh_locks(*,busy):
            for folder,count in (('cpu',8),('io',1)):
                for index in range(count):
                    fd=os.open(work/folder/str(index),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try:
                        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        except BlockingIOError:assert busy
                        else:assert not busy
                    finally:close_descriptors([fd])
        def retained(record):
            record();assert mode=='uncertain-close' and len(owners)==1
            assert not cpu.closed and not io.closed and not owners[0].reaped
            assert not owners[0].terminal() and (work/'SLICE-OWNERSHIP-RETAINED.json').exists()
            assert not (work/'RESULT.json').exists() and not (work/'SHARED-CLOSED.json').exists()
            fresh_locks(busy=True)
            raise RetentionObserved()
        # Only this disposable stale-identity case uses its unchanged real
        # epoch for the parent's final source fence; worker saw the stale one.
        def parent_plan(*a):
            value=json.loads(json.dumps(plan));value['source']['identity']=dict(epoch);return value
        with ExitStack() as stack:
            stack.enter_context(patch.object(dispatch.Pool,'read',return_value=CPU()))
            stack.enter_context(patch.object(dispatch,'checked_io_request',return_value=(io_pool,deadline)))
            stack.enter_context(patch.object(entry,'checked_plan',side_effect=parent_plan))
            stack.enter_context(patch.object(dispatch,'OwnedGroup',side_effect=owner))
            stack.enter_context(patch.object(dispatch,'retain_after_record',side_effect=retained))
            try:
                code=dispatch.run(dispatch.SLICE_TARGET,argv(plan,interpreter=sys.executable,
                    plan_path=str(plan_path),plan_sha256=digest),work,8,
                    io_admission={'path':'/disposable-admission','sha256':'0'*64})
                assert mode!='uncertain-close'
            except RetentionObserved:
                # Control-specific recovery: injected function never attempted
                # OS close, no external children, and process exit closes all
                # copies. No numeric-FD retry or production recovery recipe.
                (work/'CONTROL-EXIT-ACK').write_text('exit without fd retry\n')
                assert owners[0].await_terminal(2)
                closure=dispatch.settle(owners[0],time.monotonic()+3)
                assert closure['reaped'] and closure['returncode']==7 and closure['other_group_members_absent_before_reap']
                cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                entry.save(work/'CONTROL-RECOVERY-CLOSED.json',dict(child=closure,
                    numeric_close_retry=False,original_retention_preserved=True))
                code=7
        if mode!='uncertain-close':
            closure=entry.document(work/'SHARED-CLOSED.json')['child']
            assert code==(1 if mode=='stale-source' else 0)
            result=entry.document(work/'RESULT.json')
            assert result['complete']==(mode!='stale-source')
            if mode in ('candidate','declined'):
                assert result['diagnostic']['outcome']==('CANDIDATE_SHAPE' if mode=='candidate' else 'DECLINED_CANDIDATE_SHAPE')
        assert closure['reaped'] and closure['other_group_members_absent_before_reap'] and cpu.closed and io.closed
        assert slice_reader.stamp(os.lstat(original))==epoch
        fresh_locks(busy=False)
        cases.append(dict(mode=mode,workspace=str(work),child=closure,source_epoch_unchanged=True,
            inner_io_cpu_closed=True,fresh_inner_locks_reacquired=True,
            retained_before_control_recovery=mode=='uncertain-close'))
    summary=dict(cases=cases,canonical_io_acquired=False,retained_media_accessed=False,
        scope='Four actual workers with disposable9FD inheritance; plan/admission/namespace/inventory are explicit doubles; unknown close is injected before any OS attempt, recovered only by acknowledged worker exit.')
    entry.save(root/'RESULT.json',summary);print(json.dumps(summary),flush=True)


if __name__=='__main__':
    try:
        if sys.argv[1:2]==['--worker']:raise SystemExit(child())
        if sys.argv[1:]==['--controls']:controls()
        else:raise ValueError('fixed lifecycle controls only')
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
