"""Pinned generated-shim targets; no standalone admission or native grant."""
import os
import json
import sys
import time
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from sdk_host_matrix.shared_binding import descriptors
from sdk_merge_receiving.admission import PYTHON
from sdk_merge_receiving.plan import require
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.proxy import serve
from sdk_merge_receiving.launcher import launch


def diagnostic(role,error):
    """Only saved identities; never fstat/retry an uncertain FD during logging."""
    native=getattr(error,'proxy_native_child',None)
    return dict(role=role,pid=os.getpid(),failure=repr(error),
        original_failure=repr(getattr(error,'original_failure',None)),
        close_failure=repr(getattr(error,'close_failure',None)),
        retained_fds=list(getattr(error,'retained_fds',())),
        uncertain_closes=list(getattr(error,'uncertain_closes',())),
        native_child_pid=getattr(native,'pid',None),
        native_returncode_observation=getattr(native,'returncode',None),
        process_settlement_proved=False,resource_release_authorized=False)


def proxy_main(config):
    store=None
    try:
        require(set(config)=={'directory','identity','stage','binary','flags','deadline',
            'worker_pid','resource_fds'},'exact pinned proxy configuration required')
        require(os.getppid()==config['worker_pid'] and sys.executable==PYTHON,
                'actual worker parent and qualified interpreter required')
        binding=descriptors(config['resource_fds'])
        store=Store(config['directory'],config['identity'])
        store.write(config['stage']+'-INHERITED.json',dict(proxy_pid=os.getpid(),worker_pid=os.getppid(),
            resource_fds=config['resource_fds'],binding=binding))
        frame=serve(config['directory']+'/'+config['stage']+'.sock',config['binary'],config['flags'],config['deadline'])
        store.write(config['stage']+'-PROXY.json',frame);store.close()
        return 0
    except BaseException as error:
        # The worker/outer owner retain the same leases. No exit on unknown.
        retain_after_record(lambda:print('MERGE-PROXY-RETAINED '+json.dumps(diagnostic('proxy',error)),file=sys.stderr,flush=True))


def launcher_main():
    try:
        launch(sys.argv[1:],os.environ['UNISON_MERGE_BINARY'],os.environ['UNISON_MERGE_SOCKET'],
               float(os.environ['UNISON_MERGE_DEADLINE']))
        return 0
    except BaseException as error:
        retain_after_record(lambda:print('MERGE-LAUNCHER-RETAINED '+json.dumps(diagnostic('launcher',error)),file=sys.stderr,flush=True))
