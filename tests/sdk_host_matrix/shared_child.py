"""Retained direct-child component; caller must own admission, IO/CPU and pins."""
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'bench/sync'))
from ownership import OwnedGroup
from measure import CapturedStream
from shared_io_pool import UnresolvedIOOwnership,descriptor_observation,uncertainty_records

def validate(deadline, capture_limit, observation_factory, observation_interval):
    if type(deadline) not in (int,float) or not time.monotonic()<deadline<float('inf'):
        raise ValueError('fresh finite observation deadline required')
    if type(capture_limit) is not int or not 1<=capture_limit<=262144:
        raise ValueError('bounded capture required')
    if observation_factory is not None and (not callable(observation_factory)
            or type(observation_interval) not in (int,float)
            or not .01<=observation_interval<=1):
        raise ValueError('bounded synchronous observation configuration required')


def invoke(command,environment,deadline,*,pass_fds=(),capture_limit=262144,
           observation_factory=None,observation_interval=.05):
    validate(deadline,capture_limit,observation_factory,observation_interval)
    return start(command,environment,pass_fds=pass_fds,capture_limit=capture_limit).finish(
        deadline,observation_factory=observation_factory,
        observation_interval=observation_interval)


class PendingChild:
    """Live handle; captures drain immediately, finish observes without signals.

    No destructor/context-manager cleanup. Caller retains this handle and all
    inherited resource FDs while other owned processes run or become uncertain.
    """
    def __init__(self,owner,finish,retain,captures):
        self.owner=owner
        self.capture_owners=captures
        self._finish=finish
        self._retain=retain
        self.finished=False

    def finish(self,deadline,*,observation_factory=None,observation_interval=.05):
        if self.finished:
            raise ValueError('child finish already attempted; retain without retry')
        # Validate before consuming the operation: malformed scheduling inputs
        # do not attempt any descriptor cleanup or process operation.
        try:
            validate(deadline,262144,observation_factory,observation_interval)
        except BaseException as error:
            self._retain('invalid observation for already launched child; retain owner',error)
        self.finished=True
        return self._finish(deadline,observation_factory,observation_interval)


def start(command,environment,*,pass_fds=(),capture_limit=262144):
    return _start(command,environment,pass_fds=pass_fds,capture_limit=capture_limit,
                  capture_type=CapturedStream,maximum_capture=262144)


def _start(command,environment,*,pass_fds,capture_limit,capture_type,maximum_capture):
    # Trusted source composition only: no factory/limit is selected by a packet.
    # Existing SDK entry start() retains its original strict256KiB ceiling.
    if (maximum_capture not in (262144,4*1048576) or type(capture_limit) is not int
            or not 1<=capture_limit<=maximum_capture):
        raise ValueError('bounded capture required')
    command=list(command)
    started_ns=time.monotonic_ns()
    owner=OwnedGroup(command,env=environment,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=pass_fds)
    owner.started_ns=started_ns
    streams=[owner.process.stdout,owner.process.stderr];captures=[]
    identities=[];observer=None;observations=None
    fd_numbers=[s.fileno() for s in streams]
    def retain(reason,error=None,uncertain=()):
        records=list(uncertainty_records(error,dict(zip(fd_numbers,identities))))+list(uncertain)
        excluded={item['fd'] for item in records}
        retained=list(getattr(error,'retained_fds',()))+[fd for fd,s in zip(fd_numbers,streams) if not s.closed]
        e=UnresolvedIOOwnership(reason,retained_fds=[fd for fd in retained if fd not in excluded],
            uncertain_closes=records,original_failure=error)
        e.child_owner=owner;e.capture_owners=captures;e.process_observer=observer
        raise e from error
    try:
        for fd in fd_numbers:identities.append(descriptor_observation(fd,'shared_sdk_capture'))
        for stream in streams:captures.append(capture_type(stream,capture_limit))
    except BaseException as error:
        retain('SDK capture construction unresolved; retain launched child',error)

    def finish(deadline,observation_factory,observation_interval):
        nonlocal observer,observations
        try:
            if observation_factory is None:
                if not owner.await_terminal(max(0,deadline-time.monotonic())):
                    retain('SDK observation expired; child retained without signals')
            else:
                observer=observation_factory(owner)
                while not owner.terminal():
                    if time.monotonic()>=deadline:
                        retain('SDK observation expired; child and observer retained without signals')
                    observer.sample()
                    owner.await_terminal(min(observation_interval,max(0,deadline-time.monotonic())))
                observations=observer.report()
            owner.terminal_observed_ns=time.monotonic_ns()
            while True:
                query=subprocess.run(['/bin/ps','-axo','pid=,pgid=,stat='],capture_output=True,text=True,timeout=1)
                if query.returncode or query.stderr:retain('SDK group census failed')
                members=[]
                for line in query.stdout.splitlines():
                    fields=line.split()
                    if len(fields)!=3 or not fields[0].isdigit() or not fields[1].isdigit():retain('SDK group census malformed')
                    if int(fields[1])==owner.pid:members.append(int(fields[0]))
                if all(pid==owner.pid for pid in members):break
                if time.monotonic()>=deadline:retain('SDK other group members remain; no signals')
                time.sleep(.005)
            pid,status,usage=os.wait4(owner.pid,0)
            if pid!=owner.pid:retain('SDK reap identity differs')
            owner.reaped=True;owner.process.returncode=os.waitstatus_to_exitcode(status)
            owner.reaped_ns=time.monotonic_ns();owner.last_wait4_usage=usage
        except UnresolvedIOOwnership as error:
            if getattr(error,'child_owner',None) is owner:raise
            retain('SDK nested ownership uncertainty; retain child and every descriptor',error)
        except BaseException as error:retain('SDK child/capture state unresolved',error)
        output=[]
        for i,capture in enumerate(captures):
            try:output.append(capture.finish())
            except BaseException as error:
                # finish may have attempted close. Preserve its pre-close identity;
                # neither this component nor an outer cleanup may retry its number.
                retain('SDK capture finish/close unresolved',error,[identities[i]])
        result=dict(command=list(command),returncode=owner.process.returncode,timed_out=False,
            capture_truncated=any(x['truncated'] for x in output),stdout=output[0]['text'],stderr=output[1]['text'],
            client_cleanup=dict(pid=pid,returncode=owner.process.returncode,reaped=True,hard_kill_required=False,
                other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True),
            aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False)
        if observer is not None:result['process_observations']=observations
        return result

    return PendingChild(owner,finish,retain,captures)
