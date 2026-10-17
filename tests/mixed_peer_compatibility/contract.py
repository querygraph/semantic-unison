"""Fixed command contract only; no process launch or resource acquisition."""
from pathlib import Path

CASES = (('stock', 'current-client'), ('stock', 'old-client'),
         ('ox', 'current-client'), ('ox', 'old-client'))
STAGES = ('seed', 'update', 'noop')
CURRENT_FLAGS = ('-semanticworkers', '2', '-maxthreads', '2',
                 '-semanticdng', 'true', '-adobevalidate', 'off', '-clone', 'auto')
OLD_FLAGS = ('-maxthreads', '2')
LIMITS = dict(cases=4, calls=12, endpoint_workers=2, owner_credits=2,
              total_credits=8, call_observation_seconds=30,
              owner_observation_seconds=300, sdk_calls=0)


def command(artifacts, workspace, index, stage):
    if type(index) is not int or not 0 <= index < len(CASES) or stage not in STAGES:
        raise ValueError('exact mixed-peer case and stage required')
    if set(artifacts) != {'stock', 'ox', 'old-stock'}:
        raise ValueError('exact current stock/Ox and retained old artifact set required')
    paths = {name: Path(value) for name, value in artifacts.items()}
    directory = Path(workspace) / str(index)
    if not Path(workspace).is_absolute() or any(not p.is_absolute() for p in paths.values()):
        raise ValueError('absolute artifact and workspace paths required')
    current, orientation = CASES[index]
    old_client = orientation == 'old-client'
    client = paths['old-stock' if old_client else current]
    server = paths[current if old_client else 'old-stock']
    client_flags = OLD_FLAGS if old_client else CURRENT_FLAGS
    server_flags = CURRENT_FLAGS if old_client else OLD_FLAGS
    argv = [str(client), str(directory/'left'), 'ssh://localhost/'+str(directory/'right'),
            '-batch', '-auto', '-fastcheck', 'false', '-sshcmd', str(directory/stage/'launcher.py'),
            '-servercmd', str(server), *client_flags]
    return argv, list(server_flags)
