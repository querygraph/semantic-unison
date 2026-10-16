"""Finite local-root whole-source-clone receiving on tiny original synthetic bytes.

No server sessions, Photo paths, SDK/Adobe helpers, photographic inputs or media
mounts. Real pinned stock/Ox CLIs run serially inside the containing owner group.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = [('stock', Path('/private/tmp/unison-group-integration-stock-build-20261015.json')),
            ('ox', Path('/private/tmp/unison-group-integration-ox-build-20261015.json'))]
SIZE = 1048576
XMP = 4096
PRIVATE = 8192
RAW = 16384


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp(path):
    s = path.stat()
    return {k: getattr(s, k) for k in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')}


def fixture(path, little):
    order = '<' if little else '>'
    data = bytearray(b'\x95' * SIZE)
    private = b'TestOnly\0private-body-not-a-camera-or-image'
    packet = b'<synthetic-metadata>1</synthetic-metadata>'
    data[:8] = struct.pack(order + '2sHI', b'II' if little else b'MM', 42, 8)
    entries = [(273, 4, 1, RAW), (279, 4, 1, SIZE - RAW),
               (700, 1, len(packet), XMP), (50706, 1, 4, None),
               (50740, 1, len(private), PRIVATE)]
    data[8:10] = struct.pack(order + 'H', len(entries))
    for n, (tag, typ, count, offset) in enumerate(entries):
        start = 10 + 12*n
        data[start:start+8] = struct.pack(order + 'HHI', tag, typ, count)
        data[start+8:start+12] = b'\x01\x01\x00\x00' if offset is None else struct.pack(order + 'I', offset)
    end = 10 + 12*len(entries)
    data[end:end+4] = bytes(4)
    data[XMP:XMP+len(packet)] = packet
    data[PRIVATE:PRIVATE+len(private)] = private
    path.write_bytes(data)
    return len(packet)


def main():
    os.umask(0o077)
    workspace = Path(tempfile.mkdtemp(prefix='unison-private-dng-local-clone-'))
    cases = []
    result = {'state': 'RUNNING', 'workspace': str(workspace), 'cases': cases,
              'scope': 'Tiny generated invalid-photograph DNG-shaped fixture; no real-camera or SDK validity claim. Local roots only, no transport/server session.'}
    def save():
        (workspace / 'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    save()
    for label, receipt_path in RECEIPTS:
        receipt = json.loads(receipt_path.read_text())
        binary = Path(receipt['binary'])
        assert receipt['complete'] and receipt['build_exit'] == 0
        assert sha(binary) == receipt['binary_sha256']
        for little in (True, False):
            for clone in ('off', 'auto'):
                path = workspace / (label + ('-le-' if little else '-be-') + clone)
                path.mkdir(mode=0o700)
                left, right, state = [path / name for name in ('left', 'right', 'state')]
                for p in (left, right, state): p.mkdir(mode=0o700)
                source = left / 'synthetic-private.dng'
                target = right / source.name
                length = fixture(source, little)
                before = sha(source)
                commands = []
                argv = [str(binary), str(left), str(right), '-batch', '-auto', '-fastcheck', 'false',
                        '-times', '-clone', clone, '-semanticdng=true', '-semanticworkers', '3',
                        '-adobevalidate', 'off', '-debug', 'copy', '-debug', 'semantic']
                def sync(stage):
                    log = path / (stage + '.log')
                    with log.open('xb') as output:
                        child = subprocess.Popen(argv, env=dict(os.environ, UNISON=str(state)),
                             stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
                        # Same containing group. On timeout, outer owner settles it.
                        code = child.wait(timeout=10)
                    row = {'stage': stage, 'command': argv, 'pid': child.pid,
                           'actual_wait_exit': code, 'log': str(log), 'log_sha256': sha(log)}
                    commands.append(row)
                    if code:
                        raise RuntimeError(log.read_text(errors='replace'))
                    return log.read_text(errors='replace')
                sync('seed')
                assert sha(target) == before
                basis = path / 'synthetic-prior-inode'
                os.link(target, basis)  # Owned synthetic fixture only.
                prior = stamp(source)
                with source.open('r+b') as f:
                    f.seek(XMP)
                    old = f.read(length)
                    assert old.count(b'>1<') == 1
                    f.seek(XMP)
                    f.write(old.replace(b'>1<', b'>2<'))
                os.utime(source, ns=(source.stat().st_atime_ns, prior['st_mtime_ns'] + 2000000000))
                expected = sha(source)
                text = sync('update')
                assert sha(target) == expected and sha(basis) == before
                assert 'Local semantic fallback:' not in text, text
                if clone == 'auto':
                    assert 'Local source clone completed before semantic planning' in text, text
                assert 'Local semantic workers wrote' not in text, text
                assert 'Local receiver clone preserved' not in text, text
                cloned = 'Local source clone completed before semantic planning' in text
                assert cloned == (clone == 'auto'), text
                target_before_noop = stamp(target)
                sync('noop')
                assert stamp(target) == target_before_noop and sha(source) == expected
                assert sha(basis) == before and sha(target) == expected
                cases.append({'compiler': label, 'little_endian': little, 'clone': clone,
                              'before_sha256': before, 'after_sha256': expected,
                              'exact': True, 'basis_preserved': True, 'noop_five_preserved': True,
                              'semantic_inspection_bypassed': True, 'source_clone_path_used': cloned,
                              'commands': commands})
                save()
    result['state'] = 'EIGHT_PRIVATE_TAG_LOCAL_SOURCE_CLONE_RECEIVING_CASES_PASSED'
    result['cli_count'] = sum(len(c['commands']) for c in cases)
    save()
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
