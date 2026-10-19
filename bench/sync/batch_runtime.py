"""Owned-context batch runtime composition; not an admission or CLI entrypoint.

Must be called by trusted source after plan/build/artifact authentication and
actual EXIO→Unison00..07 acquisition. This component cannot grant those rights.
Unknown state retains resources and all returned owners; no retry or cleanup.
"""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import time
from shared_cpu_pool import UnresolvedOwnership
from sdk_host_matrix.shared_binding import descriptors
from sdk_merge_receiving.runtime import program, child_environment
from sdk_merge_receiving.admission import PYTHON
from cached_benchmark.contract import read_bytes
from batch_commands import schedule
from batch_events import Events
from batch_sample import sample
from batch_pair import invoke


def run(corpus, binaries, directory, *, repository, mode, workers, store,
        resource_rows, deadline, artifact_check):
    """Exactly one seed/update/no-op sample; no resource release authority."""
    if (type(binaries) is not dict or set(binaries) != {'client', 'server'}
            or not callable(artifact_check) or type(deadline) not in (int, float)
            or not time.monotonic() < deadline < float('inf')):
        raise ValueError('exact authenticated batch context required')
    root = Path(directory)
    contract = schedule(binaries['client'], binaries['server'], str(root), mode=mode, workers=workers)
    binding = descriptors(resource_rows)
    fds = binding['inherited_fds']
    events = Events(store); pair_pins = {}; scripts = {}; current = None
    try:
        store.fence()
        if store.root != str(root): raise ValueError('runtime/store namespace differs')
        for name in ('left', 'right', 'home', 'tmp', 'state-client', 'state-server'):
            (root/name).mkdir(mode=0o700)
        paths = [str(Path(repository)/'tests'), str(Path(repository)/'tests/sdk_host_matrix'),
                 str(Path(repository)/'bench/sync')]
        imports = '#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr(paths)+'\n'
        scripts[str(root/'launcher.py')] = program(root/'launcher.py', imports+
            'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')
        def call(stage):
            nonlocal current
            row = contract['rows'][len(pair_pins)]
            if row['stage'] != stage: raise ValueError('exact one-use batch call order required')
            if time.monotonic() >= deadline: raise TimeoutError('batch observation expired before new call')
            artifact_check()
            phase_deadline = min(deadline, time.monotonic()+120)
            config = dict(directory=str(root), identity=deepcopy(store.identity), stage=stage,
                          binary=binaries['server'], flags=row['server_flags'], deadline=phase_deadline,
                          worker_pid=os.getpid(), resource_fds=deepcopy(resource_rows))
            proxy = root/(stage+'-proxy.py')
            scripts[str(proxy)] = program(proxy, imports+
                'from sdk_merge_receiving.child_entry import proxy_main\n'+
                'raise SystemExit(proxy_main('+repr(config)+'))\n')
            for path, pin in scripts.items():
                if hashlib.sha256(read_bytes(path,65536)).hexdigest() != pin['sha256']:
                    raise ValueError('generated peer shim changed')
            current = store.write(stage+'-INTENT.json', dict(row=row, proxy_config=config,
                                  scripts=deepcopy(scripts), resource_release_authorized=False))
            env = child_environment(root, 'state-client')
            env.update(UNISON_MERGE_BINARY=binaries['server'], UNISON_MERGE_SOCKET=row['socket_path'],
                       UNISON_MERGE_DEADLINE=str(phase_deadline))
            pair_pins[stage] = invoke(row['command'], env,
                proxy_command=[PYTHON,'-B',str(proxy)],
                proxy_environment=child_environment(root,'state-server'),
                server_command=row['server_command'], socket_path=row['socket_path'],
                deadline=phase_deadline, pass_fds=fds, store=store, name=stage,
                read_proxy_bytes=lambda:store.read(stage+'-PROXY.json',maximum=65536))
            store.write(stage+'-OUTCOME.json',dict(intent=current,pair=pair_pins[stage],
                                                 resource_release_authorized=False))
        result = sample(corpus, root/'left', root/'right', invoke=call, record=events)
        if len(pair_pins) != 3 or len(events.pins) != 6:
            raise ValueError('batch sample evidence incomplete')
        artifact_check()
        pin = store.write('BATCH-RESULT.json',dict(schema='unison-generated-batch-runtime/1',
            result=result, contract=contract, events=events.pins, pairs=pair_pins,
            scripts=scripts, inherited_binding=binding,
            external_children_source_audit_required=True, per_class_path_audit_complete=False,
            resource_release_authorized=False))
        return pin
    except BaseException as error:
        retained = error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'batch runtime incomplete; retain inherited resources and all evidence owners')
        if retained is not error: retained.original_failure = error
        retained.batch_runtime = dict(store=store,events=events,pairs=pair_pins,scripts=scripts,current=current)
        excluded = set(getattr(retained,'uncertain_fds',()))
        retained.retained_fds = tuple(dict.fromkeys(fd for fd in
            (*retained.retained_fds,*fds,*(() if store.closed else (store.fd,))) if fd not in excluded))
        if retained is error: raise
        raise retained from error
