"""Retained direct-child component; caller must own admission, IO/CPU and pins."""
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'bench/sync'))
from ownership import OwnedGroup
from measure import CapturedStream
from shared_io_pool import UnresolvedIOOwnership,descriptor_observation,uncertainty_records

def invoke(command,environment,deadline,*,pass_fds=(),capture_limit=262144):
    if type(deadline) not in (int,float) or not time.monotonic()<deadline<float('inf'):
        raise ValueError('fresh finite observation deadline required')
    if type(capture_limit) is not int or not 1<=capture_limit<=262144:
        raise ValueError('bounded capture required')
    owner=OwnedGroup(command,env=environment,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=pass_fds)
    streams=[owner.process.stdout,owner.process.stderr];captures=[]
    identities=[]
    fd_numbers=[s.fileno() for s in streams]
    def retain(reason,error=None,uncertain=()):
        records=list(uncertainty_records(error,dict(zip(fd_numbers,identities))))+list(uncertain)
        excluded={item['fd'] for item in records}
        retained=list(getattr(error,'retained_fds',()))+[fd for fd,s in zip(fd_numbers,streams) if not s.closed]
        e=UnresolvedIOOwnership(reason,retained_fds=[fd for fd in retained if fd not in excluded],
            uncertain_closes=records,original_failure=error)
        e.child_owner=owner;e.capture_owners=captures
        raise e from error
    try:
        for fd in fd_numbers:identities.append(descriptor_observation(fd,'shared_sdk_capture'))
        for stream in streams:captures.append(CapturedStream(stream,capture_limit))
        if not owner.await_terminal(max(0,deadline-time.monotonic())):
            retain('SDK observation expired; child retained without signals')
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
    return dict(command=list(command),returncode=owner.process.returncode,timed_out=False,
        capture_truncated=any(x['truncated'] for x in output),stdout=output[0]['text'],stderr=output[1]['text'],
        client_cleanup=dict(pid=pid,returncode=owner.process.returncode,reaped=True,hard_kill_required=False,
            other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True),
        aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False)
