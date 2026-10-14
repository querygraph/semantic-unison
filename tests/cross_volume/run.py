#!/usr/bin/env python3
"""Owned HFS+ image versus private APFS roots; no photos or SDK calls."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import random
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', action='append', required=True, metavar='LABEL=PATH')
p.add_argument('--report', required=True, type=Path)
a = p.parse_args()
if platform.system() != 'Darwin':
    p.error('this native image qualification requires macOS')
binaries = {}
for item in a.binary:
    label, sep, path = item.partition('=')
    if not sep or not re.fullmatch('[A-Za-z0-9_-]+', label) or label in binaries:
        p.error('use unique LABEL=PATH binary arguments')
    binaries[label] = Path(path).expanduser().resolve()
root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('fixtures', root/'bench/sync/fixtures.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
work = Path(tempfile.mkdtemp(prefix='unison-cross-volume-', dir='/private/tmp'))
mount, image = work/'mount', work/'fixture.dmg'
mount.mkdir()
result = {'complete': False, 'workspace': str(work), 'cases': [], 'commands': [],
          'scope': 'Local cross-volume byte/clone/fallback/no-op checks on owned synthetic data; not physical-sharing, crash, remount or photo qualification',
          'physical_topology': 'HFS+ image backed by the same internal APFS storage; distinct logical volumes, not independent physical devices',
          'binaries': {label: {'path': str(path), 'sha256': f.sha256(path)} for label, path in binaries.items()}}
def save():
    a.report.write_text(json.dumps(result, indent=2)+'\n')
    (work/'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
def command(argv, name, env=None):
    child = subprocess.run(list(map(str, argv)), env=env, capture_output=True, timeout=60)
    log = work/(name+'.log')
    log.write_bytes(child.stdout+b'\n'+child.stderr)
    result['commands'].append({'argv': list(map(str, argv)), 'exit': child.returncode,
                               'log': str(log), 'sha256': f.sha256(log)})
    save()
    if child.returncode:
        raise RuntimeError(log.read_text(errors='replace'))
    return child.stdout
def owned_images():
    info = plistlib.loads(subprocess.check_output(['hdiutil', 'info', '-plist']))
    return [entry for entry in info['images']
            if Path(entry['image-path']).resolve() == image.resolve()]
attached = False
print('Workspace:', work, flush=True)
save()
try:
    command(['hdiutil', 'create', '-size', '128m', '-fs', 'HFS+', '-volname',
             'UnisonPrivateFixture', '-type', 'UDIF', '-nospotlight', image], 'create')
    # If attach partially succeeds, finally still queries this exact owned image.
    attached = True
    info = plistlib.loads(command(['hdiutil', 'attach', '-nobrowse', '-noautoopen',
        '-mountpoint', mount, '-plist', image], 'attach'))
    entries = [entry for entry in info['system-entities'] if entry.get('mount-point') == str(mount)]
    assert len(entries) == 1 and entries[0]['volume-kind'] == 'hfs'
    assert work.stat().st_dev != mount.stat().st_dev
    apfs = Path('/System/Volumes/Data')
    assert apfs.stat().st_dev == work.stat().st_dev
    volume = plistlib.loads(command(['diskutil', 'info', '-plist', apfs], 'apfs-info'))
    assert volume['FilesystemType'].lower() == 'apfs'
    result['filesystem'] = {'apfs_device': work.stat().st_dev, 'hfs_device': mount.stat().st_dev,
                            'apfs_uuid': volume.get('VolumeUUID'), 'hfs_entity': entries[0]}
    for label, binary in binaries.items():
        for direction in ('hfs-to-apfs', 'apfs-to-hfs'):
            for mode in ('generic-auto', 'generic-off', 'dng-auto'):
                name = label+'-'+direction+'-'+mode
                state = work/(name+'-state')
                state.mkdir()
                apfs_root, hfs_root = work/(name+'-apfs'), mount/(name+'-hfs')
                apfs_root.mkdir()
                hfs_root.mkdir()
                source, target = (hfs_root, apfs_root) if direction == 'hfs-to-apfs' else (apfs_root, hfs_root)
                is_dng = mode == 'dng-auto'
                filename = 'fixture-é.'+('dng' if is_dng else 'bin')
                path = source/filename
                if is_dng:
                    metadata = f.create(path, 2097152, 8192, 7)
                else:
                    path.write_bytes(random.Random(195).randbytes(2097152))
                before = f.sha256(path)
                argv = [binary, source, target, '-batch', '-auto', '-fastcheck', 'false', '-times',
                        '-clone', 'off' if mode == 'generic-off' else 'auto',
                        '-semanticdng='+str(is_dng).lower(), '-semanticworkers', '2',
                        '-adobevalidate', 'off', '-debug', 'copy', '-debug', 'semantic']
                def sync(stage):
                    assert f.sha256(binary) == result['binaries'][label]['sha256']
                    command(argv, name+'-'+stage, dict(os.environ, UNISON=str(state)))
                    return (work/(name+'-'+stage+'.log')).read_text(errors='replace')
                sync('seed')
                assert f.sha256(target/filename) == before
                basis_parent = work if direction == 'hfs-to-apfs' else mount
                basis = basis_parent/(name+'-basis')
                os.link(target/filename, basis)
                stamp = path.stat()
                if is_dng:
                    after = f.edit(path, metadata)
                else:
                    with path.open('r+b') as stream:
                        stream.seek(123456)
                        stream.write(b'private exact binary edit')
                    after = f.sha256(path)
                # HFS timestamps are coarse; make the intended edit observable.
                os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns+2000000000))
                log = sync('update')
                assert f.equal_files(path, target/filename) and f.sha256(basis) == before
                semantic = 'Local semantic workers wrote' in log
                generic = 'Local receiver clone preserved' in log
                expected_clone = direction == 'hfs-to-apfs' and mode != 'generic-off'
                assert semantic == (expected_clone and is_dng), log
                assert generic == (expected_clone and not is_dng), log
                preserved = re.findall(r'Local receiver clone preserved (\d+) logical bytes', log)
                if generic:
                    assert preserved == [str(2097152-131072)], log
                inode = (target/filename).stat().st_ino
                sync('noop')
                assert (target/filename).stat().st_ino == inode
                assert f.sha256(path) == after == f.sha256(target/filename)
                assert f.sha256(basis) == before
                assert len(list(source.iterdir())) == len(list(target.iterdir())) == 1
                result['cases'].append({'label': label, 'direction': direction, 'mode': mode,
                    'before_sha256': before, 'after_sha256': after, 'exact': True,
                    'basis_preserved': True, 'noop_inode_preserved': True,
                    'semantic_clone': semantic, 'generic_receiver_clone': generic})
                result['cases'][-1]['generic_inherited_logical_bytes'] = int(preserved[0]) if preserved else None
                save()
                print('PASS', name, flush=True)
    result['matrix_passed'] = True
finally:
    if attached:
        images = owned_images()
        assert len(images) <= 1, 'ambiguous owned image attachment'
        if images:
            device = next(entry['dev-entry'] for entry in images[0]['system-entities']
                          if entry.get('content-hint') == 'GUID_partition_scheme')
            command(['hdiutil', 'detach', device], 'detach')
        result['detached'] = not owned_images()
    result['complete'] = result.get('matrix_passed', False) and result.get('detached', False)
    result['source_sha256'] = {str(path.relative_to(root)): f.sha256(path)
                              for path in [Path(__file__), root/'bench/sync/fixtures.py']}
    save()
print('Receipt:', a.report)
