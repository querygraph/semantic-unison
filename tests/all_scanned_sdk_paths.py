"""Pure owner-context path evidence; not OS argv tracing or namespace authority."""
import os
from pathlib import PurePosixPath
import re

PREFIX = re.compile(r'^\[(server: )?validation-input\] ')
PATTERN = re.compile(r'Helper input v0 pid=(none|[1-9][0-9]{0,9}) '
    r'candidate-sha256=([0-9a-f]{64}) candidate-bytes=(0|[1-9][0-9]{0,18}) '
    r'path-hex=(unavailable|[0-9a-f]{2,8192}) borrowed-output=(true|false)')
STAGE = re.compile(r'validation-scan-([1-9][0-9]*)-[0-9a-f]{8}-[0-9a-f]{8}')
FILE = re.compile(r'\.validation-([1-9][0-9]*)-[0-9a-f]{8}-[0-9a-f]{8}\.dng')


def parse(log):
    if type(log) is not str or len(log.encode('utf-8')) > 4 * 1048576:
        raise ValueError('bounded input diagnostic log required')
    rows = []
    for line in log.splitlines():
        prefix = PREFIX.match(line)
        if prefix is None: continue
        match = PATTERN.fullmatch(line[prefix.end():])
        if match is None: raise ValueError('malformed owner input observation')
        pid, digest, size, encoded, borrowed = match.groups()
        if pid == 'none' or int(pid) >= 2**31 or int(size) >= 2**63 or encoded == 'unavailable':
            raise ValueError('spawned helper and full bounded input path required')
        try: raw = bytes.fromhex(encoded)
        except ValueError as error: raise ValueError('invalid input path hex') from error
        if b'\0' in raw: raise ValueError('input path contains NUL')
        path = os.fsdecode(raw)
        if not path.startswith('/') or any(p in ('.', '..', '') for p in path.split('/')[1:]):
            raise ValueError('canonical absolute owner input path required')
        rows.append(dict(endpoint='server' if prefix.group(1) else 'client', pid=int(pid),
                         sha256=digest, bytes=int(size), path=path, borrowed=borrowed == 'true'))
        if len(rows) > 4096: raise ValueError('owner input observation count limit')
    return rows


def audit(log, *, directory, endpoint_pids, helpers, phase):
    rows = parse(log)
    if phase == 'baseline':
        if rows: raise ValueError('off baseline has helper input observations')
        return dict(inputs=[], private_owner_context_observed=True, OS_argv_traced=False)
    if phase != 'validate' or len(rows) != 2 or set(endpoint_pids) != {'client', 'server'}:
        raise ValueError('exact two-endpoint owner input contract required')
    if {r['endpoint'] for r in rows} != {'client', 'server'}:
        raise ValueError('one owner input per endpoint required')
    base = PurePosixPath(directory) / 'state'
    for row in rows:
        matches = [h for h in helpers['endpoints'] if h['endpoint'] == row['endpoint'] and h['pid'] == row['pid']]
        if (len(matches) != 1 or not row['borrowed']
                or matches[0]['report']['candidate-sha256'] != row['sha256']
                or matches[0]['report']['candidate-size'] != str(row['bytes'])):
            raise ValueError('owner input/helper candidate binding differs')
        path = PurePosixPath(row['path'])
        stage, file = STAGE.fullmatch(path.parent.name), FILE.fullmatch(path.name)
        owner = endpoint_pids[row['endpoint']]
        if (type(owner) is not int or not 0 < owner < 2**31 or path.parent.parent != base
                or stage is None or file is None or int(stage.group(1)) != owner
                or int(file.group(1)) != owner):
            raise ValueError('input not bound to endpoint private stage outside replicas')
    return dict(inputs=rows, private_owner_context_observed=True, OS_argv_traced=False,
                scope='pinned owner context path and helper join; cooperative namespace fences, not hostile sandbox proof')
