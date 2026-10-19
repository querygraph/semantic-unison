"""Retained client/proxy composition; only a pinned admitted owner may call it.

No resource acquisition, admission CLI, cancellation, retry or automatic cleanup.
A failure retains every successfully returned handle and any nested failed-start
carrier. The proxy must use this successor's retained kernel, never bench/proxy.
"""
import os
import stat
import time
from shared_cpu_pool import UnresolvedOwnership
from sdk_host_matrix.shared_child import start
from sdk_merge_receiving.plan import require


def wait_socket(path, proxy, deadline):
    while True:
        if proxy.owner.terminal():
            raise RuntimeError('proxy terminal before socket readiness; audit retained owner')
        try:
            observed = os.lstat(path)
        except FileNotFoundError:
            observed = None
        if observed is not None:
            require(stat.S_ISSOCK(observed.st_mode) and observed.st_uid == os.getuid(),
                    'owned native socket required')
            return
        if time.monotonic() >= deadline:
            raise TimeoutError('proxy readiness observation expired')
        time.sleep(.005)


def run(client_command, client_environment, *, proxy_command, proxy_environment,
        socket_path, deadline, pass_fds, read_proxy):
    require(type(deadline) in (int,float) and time.monotonic() < deadline < float('inf'),
            'fresh retained pair observation required')
    try:
        os.lstat(socket_path)
    except FileNotFoundError:
        pass
    else:
        raise ValueError('one-use socket already exists; refuse before launch')
    proxy = client = None
    client_result = proxy_result = None
    try:
        proxy = start(proxy_command,proxy_environment,pass_fds=pass_fds)
        wait_socket(socket_path,proxy,min(deadline,time.monotonic()+10))
        client = start(client_command,client_environment,pass_fds=pass_fds)
        # Both captures drain while the peer runs. Observation expiry never
        # signals either peer; keep the other handle as part of the carrier.
        client_result = client.finish(deadline)
        proxy_result = proxy.finish(deadline)
        require(not client_result['capture_truncated'] and not proxy_result['capture_truncated'],
                'full client/proxy diagnostics required')
        frame = read_proxy()
        return dict(client=client_result,proxy=proxy_result,raw_proxy=frame,
                    external_sdk_audit_required=True,resource_release_authorized=False)
    except BaseException as error:
        retained = error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'retained transport pair unresolved; keep all owner and resource references')
        if retained is not error:retained.original_failure = error
        retained.transport_handles = [h for h in (proxy,client) if h is not None]
        retained.transport_client_result = client_result
        retained.transport_proxy_result = proxy_result
        if retained is error:raise
        raise retained from error
