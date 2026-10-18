"""Retained coordinator settlement kernel; no launch/admission/lock entrypoint."""
import os
import subprocess
import time
from shared_cpu_pool import UnresolvedOwnership
from mixed_peer_compatibility.parent import audit_saved
from mixed_peer_compatibility.contract import RETAINED_FORK


def members(group):
    query=subprocess.run(['/bin/ps','-axo','pid=,pgid=,stat='],capture_output=True,text=True,timeout=1)
    if query.returncode or query.stderr:
        raise ValueError('mixed-peer group census failed')
    found=[]
    for row in query.stdout.splitlines():
        fields=row.split()
        if len(fields)!=3 or not fields[0].isdigit() or not fields[1].isdigit():
            raise ValueError('mixed-peer group census malformed')
        if int(fields[1])==group:
            found.append({'pid':int(fields[0]),'state':fields[2]})
    return found


def observe_and_reap(owner, read_result, artifacts, workspace, deadline, peer_contract=RETAINED_FORK):
    """Audit separate server owners BEFORE group census and direct wait4.

    Never signal a process or infer parent tool terminal. Caller retains IO/CPU
    descriptors and must retain this carrier if observation becomes unknown.
    """
    try:
        if not owner.await_terminal(max(0,deadline-time.monotonic())):
            raise ValueError('mixed-peer observation expired; retain without signals')
        result=read_result()
        proof=audit_saved(result,artifacts,workspace,peer_contract)
        while True:
            rows=members(owner.pid)
            if all(row['pid']==owner.pid for row in rows) and owner.terminal():
                break
            if time.monotonic()>=deadline:
                raise ValueError('mixed-peer worker group unsettled')
            time.sleep(.005)
        waited,status,_=os.wait4(owner.pid,0)
        if waited!=owner.pid:
            raise ValueError('mixed-peer worker reap identity differs')
        owner.reaped=True
        owner.process.returncode=os.waitstatus_to_exitcode(status)
        closure=dict(pid=waited,returncode=owner.process.returncode,reaped=True,
                     other_group_members_absent_before_reap=True,members_before_reap=rows)
        # Exit/result contradictions are a functional failure after known OS
        # settlement, not fabricated process uncertainty.
        functional=proof['functional']=='PASS' and closure['returncode']==0
        return dict(worker=closure,independent_audit=proof,functional_pass=functional)
    except UnresolvedOwnership as error:
        error.mixed_peer_worker=owner
        raise
    except BaseException as original:
        error=UnresolvedOwnership('mixed-peer coordinator proof unresolved')
        error.original_failure=original
        error.mixed_peer_worker=owner
        raise error from original
