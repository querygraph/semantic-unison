"""Build both diagnostic tools and run original inert fixtures only.

No external input argument is accepted. Actual camera inspection needs a
separate admitting owner, exact native epoch checks and coordinated IO window.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT/'src/dngPrivateData.mli', ROOT/'src/dngPrivateData.ml',
           ROOT/'tools/private-dng-framing/inspect.ml']
LIMIT = 331558


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp(path):
    s = os.lstat(path)
    return {name: getattr(s, name) for name in
            ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_nlink')}


def frame(payload=b'xyz', order=b'II'):
    body = order + struct.pack('>I', 17) + payload
    section = b'MakN' + struct.pack('>I', len(body)) + body
    return b'Adobe\0' + section + (b'\0' if len(section) % 2 else b'')


def tiff(block, *, big=False, little=True, typ=1):
    data = bytearray(1024); order = '<' if little else '>'
    if big:
        data[:16] = struct.pack(order+'2sHHHQ', b'II' if little else b'MM', 43, 8, 0, 32)
        data[32:40] = struct.pack(order+'Q', 2)
        data[40:60] = struct.pack(order+'HHQ', 50706, 1, 4) + b'\x01\x07\x01\0' + bytes(4)
        data[60:80] = struct.pack(order+'HHQQ', 50740, typ, len(block), 512)
    else:
        data[:8] = struct.pack(order+'2sHI', b'II' if little else b'MM', 42, 32)
        data[32:34] = struct.pack(order+'H', 2)
        data[34:46] = struct.pack(order+'HHI', 50706, 1, 4) + b'\x01\x07\x01\0'
        data[46:58] = struct.pack(order+'HHII', 50740, typ, len(block), 512)
    data[512:512+len(block)] = block
    return bytes(data)


def main():
    if len(sys.argv) != 1:
        raise ValueError('fixed controls accept no camera/input arguments')
    os.umask(0o077)
    pins = {str(p): sha(p) for p in SOURCES+[Path(__file__).resolve()]}
    workspace = Path(tempfile.mkdtemp(prefix='unison-private-framing-cli-'))
    result = {'schema': 'unison-private-framing-cli-controls/1', 'workspace': str(workspace),
              'source_sha256': pins, 'builds': [], 'controls': [], 'complete': False}
    def save():
        (workspace/'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    environment = dict(os.environ)
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(key, None)
    save()
    for label, compiler in [('stock', '/Users/alexy/.opam/default/bin/ocamlopt'),
                            ('ox', '/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt')]:
        work = workspace/label; work.mkdir(mode=0o700)
        for source in SOURCES: shutil.copyfile(source, work/source.name)
        binary = work/'private-framing-diagnostic'
        command = [compiler, '-I', '+unix', '-w', '+a-70', '-warn-error', '+a-70',
                   'unix.cmxa', 'dngPrivateData.mli', 'dngPrivateData.ml', 'inspect.ml', '-o', str(binary)]
        built = subprocess.run(command, cwd=work, env=environment, text=True,
                               capture_output=True, timeout=20)
        result['builds'].append({'compiler_label': label, 'command': command,
            'returncode': built.returncode, 'stdout': built.stdout, 'stderr': built.stderr})
        save()
        if built.returncode: raise RuntimeError('diagnostic compile failed: '+built.stderr)
        result['builds'][-1].update(binary=str(binary), binary_sha256=sha(binary))
        serial = 0
        def control(name, data, *, recognized=None, expected_bytes=None,
                    mode=0o400, links=1, pipe=False, args=(), code=0):
            nonlocal serial
            serial += 1; source = work/('input-'+str(serial))
            source.write_bytes(data); source.chmod(mode)
            if links == 2: os.link(source, work/('alias-'+str(serial)))
            before = stamp(source)
            argv = [str(binary), *args]
            if pipe:
                call = subprocess.run(argv, input=data, capture_output=True, env=environment, timeout=5)
            else:
                fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
                try:
                    assert stat.S_ISREG(os.fstat(fd).st_mode)
                    call = subprocess.run(argv, stdin=fd, capture_output=True, env=environment, timeout=5)
                finally:
                    os.close(fd)
            row = {'compiler_label': label, 'name': name, 'returncode': call.returncode,
                   'stdout': call.stdout.decode(), 'stderr': call.stderr.decode(), 'before': before,
                   'after': stamp(source)}
            result['controls'].append(row); save()
            assert call.returncode == code and row['before'] == row['after'], row
            diagnostic = json.loads(call.stdout if code == 0 else call.stderr)
            assert diagnostic['diagnostic_only'] is True
            assert diagnostic['semantic_eligibility'] is False and diagnostic['sdk_validation'] is False
            assert diagnostic['full_file_sha256_computed'] is False
            assert diagnostic['native_nanosecond_epoch_fence_performed_by_child'] is False
            assert 0 <= diagnostic['logical_read_bytes'] <= LIMIT
            assert diagnostic['logical_read_bytes'] == diagnostic['requested_read_bytes']
            assert sum(row['length'] for row in diagnostic['read_ranges']) == diagnostic['requested_read_bytes']
            assert all(type(row['offset']) is int and type(row['length']) is int
                       and 0 <= row['offset'] <= len(data) and
                       0 <= row['length'] <= len(data)-row['offset']
                       for row in diagnostic['read_ranges'])
            if code == 0:
                assert diagnostic['read_limit_bytes'] == LIMIT
                assert diagnostic['read_requests'] <= 773
                assert diagnostic['framing_recognized'] is recognized
            if expected_bytes is not None: assert diagnostic['logical_read_bytes'] == expected_bytes
            if recognized:
                assert diagnostic['read_requests'] == len(diagnostic['read_ranges'])
                assert all(row['offset']+row['length'] <= 532 or row['offset'] >= 535
                           for row in diagnostic['read_ranges'])  # xyz payload is never requested.
                assert diagnostic['block_offset'] == 512 and diagnostic['block_length'] == 24
                assert diagnostic['sections'] == [{'payload_offset_in_private_block': 20,
                    'payload_length': 3, 'original_offset': 17, 'byte_order': 'little'}]
        for big in (False, True):
            for little in (False, True):
                control('layout-%s-%s' % (big, little), tiff(frame(), big=big, little=little),
                        recognized=True, expected_bytes=(72 if big else 38)+21)
        control('unrecognized-creator', tiff(b'Other\0'+frame()[6:]), recognized=False, expected_bytes=44)
        control('private-type-decline', tiff(frame(), typ=7), recognized=False, expected_bytes=38)
        control('non-TIFF-decline', bytes(1024), recognized=False, expected_bytes=8)
        for name, kw in [('writable-mode', {'mode': 0o600}), ('multiple-links', {'links': 2}),
                         ('pipe', {'pipe': True}), ('path-argument', {'args': ('/not-opened',)})]:
            control(name, tiff(frame()), code=2, expected_bytes=0, **kw)
    assert all(sha(Path(p)) == value for p, value in pins.items())
    result['complete'] = True; save(); print(json.dumps(result), flush=True)


if __name__ == '__main__': main()
