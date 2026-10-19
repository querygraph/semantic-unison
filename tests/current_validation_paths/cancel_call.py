"""Durably save cancellation raw pair and separate pre-signal observations."""
import json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.evidence import unique
from current_validation_paths.signal_transport import run


def call(row,environment,*,proxy_command,proxy_environment,socket_path,deadline,pass_fds,read_proxy_bytes,persist,before_interrupt):
    raw=None;result=None
    def read_frame():
        nonlocal raw
        raw=read_proxy_bytes()
        if type(raw) is not bytes or not 0<len(raw)<=65536:raise ValueError('bounded independent raw proxy required')
        return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite raw proxy')))
    try:
        result=run(row['command'],environment,proxy_command=proxy_command,proxy_environment=proxy_environment,
            socket_path=socket_path,deadline=deadline,pass_fds=pass_fds,read_proxy=read_frame,before_interrupt=before_interrupt)
        if type(raw) is not bytes or not 0<len(raw)<=65536:raise ValueError('transport returned without independently read raw proxy')
        persist(row,result['pair'],raw)
        return result['pair'],raw,dict(fixture_observation=result['fixture_observation'],client_interrupt=result['client_interrupt'])
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('cancellation capture/persistence unresolved')
        if retained is not error:retained.original_failure=error
        retained.cancellation_result=result;retained.cancellation_raw_proxy=raw
        if retained is error:raise
        raise retained from error
