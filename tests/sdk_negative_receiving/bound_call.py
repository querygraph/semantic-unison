"""Retained transport and durable raw pair before any policy interpretation."""
import json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.transport import run
from sdk_merge_receiving.evidence import unique
from sdk_merge_receiving.plan import require


def call(row,client_environment,*,proxy_command,proxy_environment,socket_path,
         deadline,pass_fds,read_proxy_bytes,persist):
    raw=None;pair=None
    def read_frame():
        nonlocal raw
        raw=read_proxy_bytes();require(type(raw) is bytes and 0<len(raw)<=65536,'bounded raw proxy required')
        return json.loads(raw,object_pairs_hook=unique,
            parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite raw proxy')))
    try:
        pair=run(row['command'],client_environment,proxy_command=proxy_command,
            proxy_environment=proxy_environment,socket_path=socket_path,deadline=deadline,
            pass_fds=pass_fds,read_proxy=read_frame)
        persist(row,pair,raw)
        return pair,raw
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'negative receiving pair transport/persistence unresolved; retain every owner')
        if retained is not error:retained.original_failure=error
        retained.negative_pair=pair;retained.negative_raw_proxy=raw
        if retained is error:raise
        raise retained from error
