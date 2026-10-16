#!/usr/bin/env python3
"""Generate bounded synthetic CFA fixtures and qualify their SDK validation."""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

SEED = 0x6D2B79F5


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def seed_dng(path, width, height):
    if min(width, height) < 16 or width * height > 32000000:
        raise ValueError('fixture must have dimensions >=16 and at most 32 million samples')
    tags = []
    def tag(code, kind, count, payload):
        tags.append((code, kind, count, payload))
    def shorts(code, *values):
        tag(code, 3, len(values), struct.pack('<' + 'H' * len(values), *values))
    def longs(code, *values):
        tag(code, 4, len(values), struct.pack('<' + 'I' * len(values), *values))
    def rational(code, *values, signed=False):
        tag(code, 10 if signed else 5, len(values),
            b''.join(struct.pack('<ii' if signed else '<II', n, d) for n, d in values))
    def text(code, value):
        tag(code, 2, len(value) + 1, value.encode('ascii') + b'\0')
    longs(254, 0); longs(256, width); longs(257, height)
    shorts(258, 16); shorts(259, 1); shorts(262, 32803)
    text(271, 'Unison'); text(272, 'Synthetic CFA benchmark')
    longs(273, 0); shorts(274, 1); shorts(277, 1)
    longs(278, height); longs(279, width * height * 2); shorts(284, 1)
    shorts(33421, 2, 2); tag(33422, 1, 4, bytes([0, 1, 1, 2]))
    tag(50706, 1, 4, bytes([1, 4, 0, 0])); tag(50707, 1, 4, bytes([1, 1, 0, 0]))
    text(50708, 'Unison Synthetic CFA benchmark')
    tag(50710, 1, 3, bytes([0, 1, 2])); shorts(50711, 1)
    shorts(50713, 1, 1); rational(50714, (0, 1)); longs(50717, 65535)
    rational(50718, (1, 1), (1, 1)); longs(50719, 0, 0); longs(50720, width, height)
    rational(50721, *[(1 if i in (0, 4, 8) else 0, 1) for i in range(9)], signed=True)
    rational(50728, (1, 1), (1, 1), (1, 1)); shorts(50778, 21)
    longs(50829, 0, 0, height, width)
    tag(50972, 1, 16, bytes(16))  # Patched with the independently computed raw MD5.
    tags.sort()
    base = 8 + 2 + len(tags) * 12 + 4
    extra, entries, digest_offset = bytearray(), [], None
    for code, kind, count, payload in tags:
        if len(payload) <= 4:
            value = payload.ljust(4, b'\0')
        else:
            if len(extra) & 1:
                extra += b'\0'
            offset = base + len(extra)
            if code == 50972:
                digest_offset = offset
            value = struct.pack('<I', offset)
            extra += payload
        entries.append([code, kind, count, value])
    if len(extra) & 1:
        extra += b'\0'
    raw_offset = base + len(extra)
    for entry in entries:
        if entry[0] == 273:
            entry[3] = struct.pack('<I', raw_offset)
    header = b'II*\0' + struct.pack('<I', 8) + struct.pack('<H', len(tags)) + b''.join(
        struct.pack('<HHI', code, kind, count) + value for code, kind, count, value in entries)
    raw_digest, state = hashlib.md5(), SEED
    gradient = [x * 34000 // max(1, width - 1) for x in range(width)]
    with path.open('wb') as output:
        output.write(header + bytes(4) + extra)
        for y in range(height):
            row = array('H')
            background = 8000 + y * 18000 // max(1, height - 1)
            for x in range(width):
                state = (1664525 * state + 1013904223) & 0xFFFFFFFF
                noise = (state >> 20) - 2048
                bias = (2000 if not (y & 1 or x & 1) else -1500 if y & 1 and x & 1 else 0)
                row.append(max(0, min(65535, background + gradient[x] + bias + noise)))
            if sys.byteorder != 'little':
                row.byteswap()
            data = row.tobytes()
            output.write(data); raw_digest.update(data)
        output.seek(digest_offset)
        output.write(raw_digest.digest())
    return dict(width=width, height=height, raw_bytes=width * height * 2,
                raw_md5=raw_digest.hexdigest(), seed=SEED,
                pattern='16-bit RGGB CFA; horizontal/vertical gradients, color biases, fixed LCG uniform noise')


def tags(path):
    with path.open('rb') as source:
        header = source.read(8)
        endian = '<' if header[:2] == b'II' else '>'
        if struct.unpack_from(endian + 'H', header, 2)[0] != 42:
            raise ValueError('expected bounded classic TIFF fixture')
        source.seek(struct.unpack_from(endian + 'I', header, 4)[0])
        count = struct.unpack(endian + 'H', source.read(2))[0]
        result = [struct.unpack(endian + 'HHII', source.read(12)) for _ in range(count)]
    return endian, result


def receipt(driver, build_id, path, expected_pass, invoke=subprocess.run):
    pin = sha256(path)
    command = [str(driver), '--unison-dng-validation-v1', '--expected-sha256', pin,
               '--expected-size', str(path.stat().st_size), '--threads', '1', '--', str(path.resolve())]
    start = time.monotonic()
    child = invoke(command, capture_output=True, text=True, timeout=300)
    elapsed = time.monotonic() - start
    lines = child.stdout.splitlines()
    assert len(lines) == 10 and lines[0] == 'UNISON-DNG-VALIDATION 1' and lines[-1] == 'END', child.stderr
    report = dict(line.split(' ', 1) for line in lines[1:-1])
    assert report['candidate-sha256'] == pin and report['candidate-size'] == str(path.stat().st_size)
    assert report['driver-build'] == build_id and child.returncode == 0
    passed = (report['structure'] == 'valid' and report['decode'] == 'success' and
              report['raw-digest'] == 'valid' and report['errors'] == '0')
    assert passed == expected_pass, (report, child.stderr)
    if not expected_pass:
        assert report['raw-digest'] == 'mismatch' and int(report['errors']) > 0
    return dict(receipt=report, exit=child.returncode, stderr=child.stderr,
                qualification_wall_seconds=elapsed)


def generate(build, output, width=6000, height=4000, invoke=subprocess.run):
    build, output = build.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((build / 'build-manifest.json').read_text())
    driver, writer = build / 'unison-adobe-validator', build / 'fixture-writer'
    assert sha256(driver) == manifest['executable_sha256'] and manifest['threads'] == 1
    assert manifest['qualification'].startswith('passed '), 'driver must already be qualified'
    source = output / 'seed.dng'
    specification = seed_dng(source, width, height)
    source_control = receipt(driver, manifest['build_id'], source, True, invoke)
    fixtures = []
    for codec, compression in [('uncompressed', 1), ('jpeg', 7), ('jxl', 52546)]:
        target = output / (codec + '.dng')
        child = invoke([str(writer), codec, str(source), str(target)],
                               capture_output=True, text=True, timeout=600)
        assert child.returncode == 0, (codec, child.stdout, child.stderr)
        endian, entries = tags(target)
        actual = next(value & 65535 for tag, kind, count, value in entries if tag == 259)
        assert actual == compression, (codec, actual)
        positive = receipt(driver, manifest['build_id'], target, True, invoke)
        damaged = output / (codec + '-bad-digest.dng')
        damaged.write_bytes(target.read_bytes())
        offset = next(value for tag, kind, count, value in entries if tag in (50972, 51111) and kind == 1 and count == 16)
        with damaged.open('r+b') as changed:
            changed.seek(offset); byte = changed.read(1); changed.seek(offset)
            changed.write(bytes([byte[0] ^ 1]))
        negative = receipt(driver, manifest['build_id'], damaged, False, invoke)
        damaged.unlink()
        fixtures.append(dict(codec=codec, filename=target.name, size_bytes=target.stat().st_size,
                             sha256=sha256(target), compression=actual, positive=positive, negative=negative))
        print(f'Qualified {codec}: {target.stat().st_size / 1048576:.1f} MiB, raw digest valid; damaged digest rejected.', flush=True)
    result = dict(specification=specification, source_sha256=sha256(source), source_control=source_control,
                  writer_sha256=sha256(writer), fixtures=fixtures)
    (output / 'fixtures.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--width', type=int, default=6000)
    parser.add_argument('--height', type=int, default=4000)
    args = parser.parse_args()
    generate(args.sdk_build, args.output, args.width, args.height)
