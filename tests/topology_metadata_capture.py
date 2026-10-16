"""Fixed bounded metadata-only census; observations never assert physical lanes."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import resource
import subprocess
import sys
import time

COMMANDS = (
    ('disk-list', ('/usr/sbin/diskutil', 'list', '-plist')),
    ('apfs-list', ('/usr/sbin/diskutil', 'apfs', 'list', '-plist')),
    ('root-info', ('/usr/sbin/diskutil', 'info', '-plist', '/')),
    ('quasar-info', ('/usr/sbin/diskutil', 'info', '-plist', '/Volumes/Quasar')),
    ('ten-info', ('/usr/sbin/diskutil', 'info', '-plist', '/Volumes/Ten')),
    ('block-registry', ('/usr/sbin/ioreg', '-a', '-r', '-c', 'IOBlockStorageDevice')),
)


def main():
    if len(sys.argv) != 2:
        raise SystemExit('one absent private output directory required')
    os.umask(0o077)
    output = Path(sys.argv[1])
    output.mkdir(mode=0o700)
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1048576, 2 * 1048576))
    started = time.time()
    rows = []
    for label, command in COMMANDS:
        before = time.time()
        stdout, stderr = output / (label + '.stdout'), output / (label + '.stderr')
        with stdout.open('xb') as out, stderr.open('xb') as err:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            timeout = False
            try:
                code = process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                timeout = True
                process.kill()
                code = process.wait()
        raw = stdout.read_bytes()
        parsed = None
        if code == 0:
            try:
                value = plistlib.loads(raw)
                parsed = {'type': type(value).__name__,
                          'top_level_count': len(value) if isinstance(value, (dict, list)) else None}
            except Exception as error:
                parsed = {'error_type': type(error).__name__}
        row = {'command': list(command), 'pid': process.pid, 'actual_wait_exit': code,
               'timed_out': timeout, 'start_unix': before, 'end_unix': time.time(),
               'plist_shape_only': parsed, 'artifacts': []}
        for path in (stdout, stderr):
            data = path.read_bytes()
            row['artifacts'].append({'path': str(path), 'bytes': len(data),
                                     'sha256': hashlib.sha256(data).hexdigest()})
        rows.append(row)
    result = {'schema': 'unison-topology-metadata-observation/1', 'commands': rows,
              'start_unix': started, 'end_unix': time.time(),
              'physical_member_adapter_qualified': False,
              'scope': 'Fixed read-only metadata commands only. No device media or photograph opened. Command success and plist parsing do not establish complete/stable physical topology. Disk arbitration/OS daemon work is outside owned child group.'}
    with (output / 'RESULT.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
