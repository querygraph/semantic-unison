"""One-use native merge owner kernel; no standalone CLI or implied admission.

The entry must authenticate current metadata before calling. Pool objects and
artifact/parent auditors are trusted pinned code, not packet-selected callbacks.
This owns resource lifetime; parent_audit separately proves every external child.
"""
import os
from pathlib import Path
import time
from shared_cpu_pool import UnresolvedOwnership
from shared_io_pool import try_io_cpu_bundle,close_unstarted
from sdk_host_matrix.shared_child import start
from sdk_merge_receiving import admission as A
from sdk_merge_receiving.store import Store


def fd_rows(cpu,io):
    result=[]
    for fd in (*cpu.fds,*io.fds):
        value=os.fstat(fd)
        result.append(dict(fd=fd,device=value.st_dev,inode=value.st_ino))
    return result


def run(packet,admission,*,request_ref,plan_ref,cpu_pool,io_pool,
        artifact_check,parent_audit,environment,start_child=start,now=time.time,
        make_store=Store,describe_fds=fd_rows):
    command=A.worker_command(packet,plan_ref)
    A.check(admission,packet,request_ref=request_ref,plan_ref=plan_ref,command=command,now=now())
    workspace=Path(packet['workspace'])
    # mkdir is the authoritative one-use consume operation, not exists()/ps.
    workspace.mkdir(mode=0o700)
    store=io=cpu=child=None
    child_started=child_attempted=False
    def retain(error):
        original=error
        if not isinstance(error,UnresolvedOwnership):
            error=UnresolvedOwnership('merge owner state unresolved; retain resources and child owners')
            error.original_failure=original
        known=list(error.retained_fds)
        for lease in (cpu,io):
            if lease is not None and not lease.closed:known.extend(lease.fds)
        if store is not None and not store.closed:known.append(store.fd)
        excluded=set(getattr(error,'uncertain_fds',()))
        error.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        error.merge_owner=dict(store=store,io=io,cpu=cpu,child=child,command=command,
                               child_started=child_started,child_attempted=child_attempted,
                               workspace=str(workspace))
        return error
    try:
        native=os.lstat(workspace)
        store=make_store(str(workspace),dict(device=native.st_dev,inode=native.st_ino))
        store.write('ADMISSION-BOUND.json',dict(request=request_ref,plan=plan_ref,
            admission_nonce=admission['nonce'],command=command,
            resource_release_authorized=False,parent_terminal_proved=False))
        bundle=try_io_cpu_bundle(io_pool,cpu_pool,tuple(range(8)))
        if bundle is None:
            store.write('PREENTRY-CONTENTION.json',dict(child_started=False,retry_allowed=False))
            store.close()
            return dict(state='CONTENTION_UNSTARTED_CONSUMED',child_started=False,
                        resource_release_authorized=False,parent_terminal_proved=False)
        io,cpu=bundle
        A.check(admission,packet,request_ref=request_ref,plan_ref=plan_ref,command=command,now=now())
        artifact_check(packet)
        deadline=time.monotonic()+packet['limits']['observation_seconds']
        # start_child carries failed-start owner/capture uncertainty itself.
        child_attempted=True
        child=start_child(command,environment,pass_fds=(*cpu.fds,*io.fds))
        child_started=True
        store.write('OWNER-START.json',dict(owner_pid=os.getpid(),child_pid=child.owner.pid,
            target='current-sdk-merge',command=command,cpu_credits=8,token_indexes=list(range(8)),
            io_mode='EX_GLOBAL',inherited_resource_fds=describe_fds(cpu,io),
            admission_nonce=admission['nonce'],owner_observation_deadline=deadline))
        (workspace/'OWNER-START-READY').mkdir(mode=0o700)
        os.fsync(store.fd)
        outcome=child.finish(deadline)
        audit=parent_audit(packet,store,outcome)
        A.require(type(audit) is dict and audit.get('external_children_settled') is True,
                  'independent external child/helper audit unresolved')
        store.write('OWNER-AUDIT.json',dict(outcome=outcome,audit=audit,
            parent_terminal_proved=False,resource_release_authorized=False))
        # Directory uncertainty retains both leases. CPU uncertainty retains IO.
        store.close()
        cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,
                                             external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,
                                            external_children_settled=True)
        return dict(state='OWNED_WORKER_AND_EXTERNAL_CHILDREN_CLOSED',outcome=outcome,audit=audit,
                    cpu_closed=True,io_closed=True,parent_terminal_proved=False)
    except UnresolvedOwnership as error:
        raise retain(error)
    except BaseException as error:
        if child_attempted:
            raise retain(error) from error
        # No child start was attempted. Once start is called, even an ordinary
        # constructor error remains unknown rather than a safe no-child prefix.
        try:
            if store is not None and not store.closed:
                store.write('PREENTRY-FAILED.json',dict(child_started=False,failure=repr(error)))
                store.close()
            if cpu is not None and not cpu.closed:close_unstarted(cpu)
            if io is not None and not io.closed:close_unstarted(io)
        except BaseException as cleanup:
            retained=retain(cleanup);retained.preentry_failure=error
            raise retained from cleanup
        raise
