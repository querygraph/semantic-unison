#!/usr/bin/env python3
"""Pure ownership-interface fixtures; no child process or native cleanup claim."""
from types import SimpleNamespace
import measure
import run as sync

original_group, original_capture = measure.OwnedGroup, measure.CapturedStream
fault = KeyboardInterrupt('original interrupt')
class Group:
    def __init__(self,*_args,**_kwargs):
        self.process=SimpleNamespace(stdout=None,stderr=None)
    def await_terminal(self,_timeout):
        raise fault
    def finish(self,**_kwargs):
        usage=SimpleNamespace(ru_utime=0,ru_stime=0,ru_maxrss=1,ru_minflt=0,ru_majflt=0,ru_inblock=0,ru_oublock=0)
        return {'pid':42,'returncode':-15,'reaped':True},usage
class Capture:
    def __init__(self,*_args,**_kwargs):pass
    def finish(self):return {'text':'fixture','bytes':7,'truncated':False}
try:
    measure.OwnedGroup,measure.CapturedStream=Group,Capture
    try:
        measure.run(['NEVER-EXECUTE'],{},1)
    except KeyboardInterrupt as error:
        assert error is fault
        evidence=error.owned_process_outcome
        assert evidence['client_cleanup']=={'pid':42,'returncode':-15,'reaped':True}
        assert evidence['stdout']==evidence['stderr']=='fixture'
    else:raise AssertionError('original interrupt lost')
finally:
    measure.OwnedGroup,measure.CapturedStream=original_group,original_capture
original_run=sync.run
try:
    def fail(*_args,**_kwargs):raise fault
    sync.run=fail
    try:
        sync.measure_invocation(['NEVER-EXECUTE'],{'UNISON_SYNC_BENCH_PROXY_RECEIPT':'/NEVER-EXIST-RECEIPT'},1,None,use_proxy=False)
    except sync.InvocationFailure as error:
        assert error.outcome['client_cleanup']==evidence['client_cleanup']
        assert 'KeyboardInterrupt' in error.outcome['fault']
    else:raise AssertionError('interrupted invocation accepted')
finally:sync.run=original_run
print('PASS original interrupt identity and settled receipt survive both wrappers; pure fixture, no child')
