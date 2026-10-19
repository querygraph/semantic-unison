"""Source-owned client cancellation transport; never an admission or cleanup.

The fixture observer runs after both handles exist and before either reap.
Only SIGINT of the exact still-live direct client is available. Observation
expiry, callback failure, signal uncertainty or finish failure retain both
handles; there is no timeout kill, retry or inherited-FD release here.
"""
import os,signal,time
from shared_cpu_pool import UnresolvedOwnership
from sdk_host_matrix.shared_child import start
from sdk_merge_receiving.transport import wait_socket


class ClientInterrupt:
    def __init__(self,handle):
        self.handle=handle;self.attempted=False;self.record=None
    def send(self):
        if self.attempted:raise ValueError('client SIGINT already attempted; no retry')
        self.attempted=True
        owner=self.handle.owner
        if owner.reaped or type(owner.pid) is not int or not 0<owner.pid<2**31:
            raise ValueError('exact unreaped direct client required')
        if owner.terminal():raise ValueError('client already terminal; no signal sent')
        # WNOWAIT/non-reaped ownership reserves this child PID throughout send.
        # ESRCH is uncertainty, never a successful synthetic cancellation.
        os.kill(owner.pid,signal.SIGINT)
        self.record=dict(pid=owner.pid,signal=int(signal.SIGINT),sent=True,
            client_reaped_before_signal=False,resource_release_authorized=False)
        return dict(self.record)


def run(command,environment,*,proxy_command,proxy_environment,socket_path,
        deadline,pass_fds,read_proxy,before_interrupt):
    if type(deadline) not in (int,float) or not time.monotonic()<deadline<float('inf'):
        raise ValueError('fresh finite observation required')
    if not callable(before_interrupt):raise ValueError('trusted source fixture observer required')
    try:os.lstat(socket_path)
    except FileNotFoundError:pass
    else:raise ValueError('one-use socket already exists')
    proxy=client=interrupt=None;client_result=proxy_result=observation=None
    try:
        proxy=start(proxy_command,proxy_environment,pass_fds=pass_fds)
        wait_socket(socket_path,proxy,min(deadline,time.monotonic()+10))
        client=start(command,environment,pass_fds=pass_fds)
        interrupt=ClientInterrupt(client)
        observation=before_interrupt(client,deadline)
        if time.monotonic()>=deadline:raise TimeoutError('fixture observation expired; no signal')
        sent=interrupt.send()
        client_result=client.finish(deadline)
        proxy_result=proxy.finish(deadline)
        if client_result['capture_truncated'] or proxy_result['capture_truncated']:
            raise ValueError('complete cancellation captures required')
        frame=read_proxy()
        return dict(pair=dict(client=client_result,proxy=proxy_result,raw_proxy=frame,
            external_sdk_audit_required=True,resource_release_authorized=False),
            fixture_observation=observation,client_interrupt=sent,
            publication_proved=False,resource_release_authorized=False)
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'named cancellation unresolved; retain both direct handles and inherited resources')
        if retained is not error:retained.original_failure=error
        retained.transport_handles=[h for h in (proxy,client) if h is not None]
        retained.transport_client_result=client_result;retained.transport_proxy_result=proxy_result
        retained.client_interrupt=interrupt;retained.fixture_observation=observation
        retained.retained_fds=tuple(dict.fromkeys((*retained.retained_fds,*pass_fds)))
        if retained is error:raise
        raise retained from error
