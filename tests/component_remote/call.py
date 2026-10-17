"""Retained direct probe and separately-owned proxy; no aggregate timeout kill."""
import os
from pathlib import Path
import subprocess
import sys
import time
from component_remote.io import load, read
from shared_cpu_pool import UnresolvedOwnership, close_descriptors
from shared_process_owner import settle
from ownership import OwnedGroup
from sdk_host_matrix.shared_child import invoke

def execute(argv,environment,directory,deadline):
    supervisor=None;streams=[]
    def retain(reason,original=None):
        error=UnresolvedOwnership(reason,retained_fds=getattr(original,'retained_fds',()),
                                  uncertain_fd=getattr(original,'uncertain_fd',None))
        error.uncertain_closes=getattr(original,'uncertain_closes',())
        error.original_failure=original;error.native_owners=[supervisor]
        raise error from original
    try:
        try:
            for name in ('supervisor-stdout.txt','supervisor-stderr.txt'):
                streams.append(os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o600))
            supervisor=OwnedGroup([sys.executable,str(directory/'proxy.py')],env=environment,
                strict_group_settlement=True,stdin=subprocess.DEVNULL,stdout=streams[0],stderr=streams[1])
        finally:close_descriptors(streams)
        socket=Path(environment['UNISON_SYNC_BENCH_SOCKET']);startup=min(deadline,time.monotonic()+5)
        while not socket.exists():
            if supervisor.terminal() or time.monotonic()>=startup:
                retain('proxy failed before probe entry; retain supervisor for independent recovery')
            time.sleep(.005)
        outcome=invoke(argv,environment,deadline,capture_limit=262144)
        # invoke preserves its own native/capture owners on uncertainty. No
        # conventional benchmark wrapper may replace that exception with text.
        if not supervisor.await_terminal(max(0,min(5,deadline-time.monotonic()))):
            retain('proxy observation elapsed; retain supervisor without signals')
        proxy=load(directory/'proxy.json')
        if not (proxy.get('input_pump_joined') is True and
                (proxy.get('server_cleanup') is None or proxy['server_cleanup'].get('reaped') is True)):
            retain('proxy native/pump closure missing')
        stopped=settle(supervisor,time.monotonic()+5)
        stopped['group_cleanup_before_leader_reap']=stopped['other_group_members_absent_before_reap']
        outcome.update(supervisor_cleanup=stopped,proxy=proxy,
          supervisor_output=read(directory/'supervisor-stdout.txt',262144).decode('utf-8','replace')+
                            read(directory/'supervisor-stderr.txt',262144).decode('utf-8','replace'),
          supervisor_capture_truncated=False)
        return outcome
    except UnresolvedOwnership as error:
        # Preserve the actual inner carrier (including every uncertain-close
        # identity, child/capture reference and cause), plus this separate owner.
        error.component_proxy_owner=supervisor
        raise
    except BaseException as error:
        retain('component call state unresolved; retain every owner',error)
