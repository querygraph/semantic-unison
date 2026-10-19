"""Exact Adobe-free batch peer commands; no executable/admission observation."""
from pathlib import PurePosixPath


def canonical(value):
    if (type(value) is not str or not value.startswith('/') or '\x00' in value
            or '..' in PurePosixPath(value).parts or str(PurePosixPath(value)) != value):
        raise ValueError('canonical absolute command path required')
    return value


def schedule(client, server, directory, *, mode, workers=3):
    for path in (client, server, directory): canonical(path)
    if mode not in ('ordinary', 'receiver-clone', 'semantic') or type(workers) is not int or not 1 <= workers <= 3:
        raise ValueError('explicit batch mode and shared8 endpoint budget required')
    root = PurePosixPath(directory)
    flags = ['-clone', 'off' if mode == 'ordinary' else 'auto',
             '-semanticworkers', str(workers), '-semanticcpubudget', str(workers),
             '-maxthreads', str(max(2, workers)), '-semanticvolumejobs', '1',
             '-adobevalidate', 'off', '-debug', 'semantic']
    if mode == 'semantic': flags += ['-semanticdng']
    rows = []
    for stage in ('seed', 'update', 'noop'):
        socket = str(root / (stage+'.sock'))
        if len(socket.encode()) >= 100: raise ValueError('bounded Unix socket path required')
        rows.append(dict(stage=stage, socket_path=socket,
            command=[client, str(root/'left'), 'ssh://localhost/'+str(root/'right'),
                     '-sshcmd', str(root/'launcher.py'), '-servercmd', server,
                     '-batch', '-auto', '-fastcheck', 'false', '-times', *flags],
            server_command=[server, '-server', '__new-rpc-mode', *flags],
            server_flags=list(flags), resource_release_authorized=False))
    return dict(schema='unison-generated-batch-schedule/1', rows=rows,
                endpoint_workers=workers, reserved_credits=8,
                configured_endpoint_plus_owner_bound=2*max(2,workers)+2,
                token_indexes=list(range(8)), io_mode='EX_GLOBAL',
                sdk_calls=0, os_thread_hardcap=False, runtime_admitted=False)
