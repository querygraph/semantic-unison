"""Persist independently read pair evidence before returning a worker outcome.

No admission/CPU/IO ownership is supplied here. All callbacks/configuration must
be pinned admitted executor code, not values selected by a remote packet.
"""
import json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import transport
from sdk_merge_receiving.evidence import bind, unique
from sdk_merge_receiving.plan import require


def call(row, client_environment, *, proxy_command, proxy_environment, socket_path,
         deadline, pass_fds, read_proxy_bytes, persist):
    raw = None
    pair = None
    def read_frame():
        nonlocal raw
        raw = read_proxy_bytes()
        require(type(raw) is bytes and 0<len(raw)<=65536, 'bounded raw proxy file required')
        return json.loads(raw,object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    try:
        pair=transport.run(row['command'],client_environment,proxy_command=proxy_command,
            proxy_environment=proxy_environment,socket_path=socket_path,deadline=deadline,
            pass_fds=pass_fds,read_proxy=read_frame)
        # Persist raw evidence even when the subsequent independent audit fails.
        # The qualified writer must retain any uncertain descriptor on failure.
        persist(row,pair,raw)
        return bind(row,pair,expected_proxy_command=proxy_command,raw_proxy_bytes=raw)
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        retained=UnresolvedOwnership('pair evidence persistence/binding unresolved; retain resources')
        retained.original_failure=error
        retained.transport_pair=pair
        retained.raw_proxy_bytes=raw
        raise retained from error
