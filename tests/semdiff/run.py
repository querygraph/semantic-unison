#!/usr/bin/env python3
"""End-to-end controls for unison -semdiff and unison-dngscan -semdiff.

Synthetic DNG and JPEG fixtures only, in a private temporary directory: a
shuttle root and a long-term root beside which the review tree and the
dng-compare archive are created. Runs the real binaries and checks the files
they leave, the summaries, the dng-compare index and a restore from a
-preservefull delta. dng-compare (uv, metadata_index.py, preserve_apo.py,
metadata_rules.json and the exiftool-rs worker) is found through
DNG_COMPARE_HOME or ~/src/dng-compare; without it the archive checks are
skipped and reported as skipped."""
import argparse, hashlib, json, os, pathlib, shutil, sqlite3, struct, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True, help='text-UI unison binary of this build')
p.add_argument('--dngscan', required=True, help='unison-dngscan of the same build')
a = p.parse_args()
home = pathlib.Path(os.environ.get('DNG_COMPARE_HOME', pathlib.Path.home() / 'src/dng-compare'))
have_dng_compare = (home / 'preserve_apo.py').is_file() and shutil.which('uv') and shutil.which('xdelta3')


def dng(rating, raw_flip=None, size=262144):
    """Minimal little-endian DNG: one strip of raw data, a primary XMP packet."""
    b = bytearray(bytes((i * 71 + 19) % 256 for i in range(size)))
    struct.pack_into('<2sHI', b, 0, b'II', 42, 8)
    packet = (f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
              f'<rdf:Description rdf:about="" xmp:Rating="{rating}"/></rdf:RDF>').encode()
    packet += b' ' * (2048 - len(packet))
    entries = [(273, 4, 1, 8192), (279, 4, 1, size - 8192), (700, 1, 2048, 1024), (50706, 1, 4, 0x00000401)]
    struct.pack_into('<H', b, 8, len(entries))
    for i, e in enumerate(entries):
        struct.pack_into('<HHII', b, 10 + 12 * i, *e)
    struct.pack_into('<I', b, 10 + 12 * len(entries), 0)
    b[1024:1024 + 2048] = packet
    if raw_flip is not None:
        b[8192 + raw_flip] ^= 1
    return bytes(b)


def jpeg(label, scan=b'\x12\x34\x56'):
    def seg(marker, body): return bytes([0xff, marker]) + struct.pack('>H', len(body) + 2) + body
    xmp = b'http://ns.adobe.com/xap/1.0/\x00' + f'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><rdf:Description rdf:about="" xmp:Label="{label}"/></rdf:RDF></x:xmpmeta>'.encode()
    return (b'\xff\xd8' + seg(0xe1, xmp) + seg(0xdb, bytes(65)) + seg(0xc0, b'\x08\x00\x01\x00\x01\x01\x01\x11\x00')
            + seg(0xda, b'\x01\x01\x00\x00\x3f\x00') + scan + b'\xff\xd9')


checks = 0
def check(ok, message):
    global checks
    if not ok:
        sys.exit('FAIL: ' + message)
    checks += 1

sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory(prefix='unison-semdiff-') as td:
    t = pathlib.Path(td).resolve()
    left, vol = t / 'shuttle/foto', t / 'photo'
    right = vol / 'foto'
    files = {
        'same.DNG': (dng(1), dng(1)),
        'meta.DNG': (dng(3), dng(1)),
        'image.DNG': (dng(1, raw_flip=5), dng(1)),
        'same.jpg': (jpeg('Blue'), jpeg('Blue')),
        'meta.jpg': (jpeg('Red'), jpeg('Blue')),
        'image.jpg': (jpeg('Blue', b'\x99'), jpeg('Blue')),
        'missing.DNG': (dng(2), None),
    }
    for name, (l, r) in files.items():
        (left / '2026/A/s1').mkdir(parents=True, exist_ok=True)
        (left / '2026/A/s1' / name).write_bytes(l)
        if r is not None:
            (right / '2026/A/s1').mkdir(parents=True, exist_ok=True)
            (right / '2026/A/s1' / name).write_bytes(r)
    # Found by name under a renamed session folder; and a whole absent session.
    (left / '2026/A/s2').mkdir(parents=True); (right / '2026/A/renamed').mkdir(parents=True)
    (left / '2026/A/s2/moved.DNG').write_bytes(dng(4)); (right / '2026/A/renamed/moved.DNG').write_bytes(dng(4))
    (left / '2026/B/s3').mkdir(parents=True)
    (left / '2026/B/s3/new.txt').write_bytes(b'new session\n')
    before = {p: sha(p) for p in left.rglob('*') if p.is_file()}

    env = dict(os.environ, UNISON=str(t / 'unisondir'))
    (t / 'unisondir').mkdir()
    def unison(*args):
        r = subprocess.run([a.unison, str(left), str(right), '-semdiff', '-batch', '-semdiffscanner', a.dngscan, *args],
                           env=env, capture_output=True, text=True)
        check(r.returncode == 0, 'unison exited %d:\n%s%s' % (r.returncode, r.stdout, r.stderr))
        return r.stdout + r.stderr

    full = ['-preserve', '-preservefull', '-sameview'] if have_dng_compare else ['-sameview']
    out = unison(*full)
    report = next((t / 'unisondir').glob('semdiff-*.jsonl'))
    records = {json.loads(l)['rel']: json.loads(l)['targets'][0] for l in report.read_text().splitlines()}
    status = {k: v['status'] for k, v in records.items()}
    check(status['2026/A/s1/same.DNG'] == 'identical' and status['2026/A/s1/same.jpg'] == 'identical', 'identical pairs')
    check(status['2026/A/s1/image.DNG'] == 'image-differs' and status['2026/A/s1/image.jpg'] == 'image-differs', 'image differences')
    check(status['2026/A/s1/meta.DNG'] == 'metadata-only' and status['2026/A/s1/meta.jpg'] == 'metadata-only', 'metadata-only pairs')
    check(records['2026/A/s2/moved.DNG']['how'] == 'name' and status['2026/A/s2/moved.DNG'] == 'identical', 'match by name')
    check(status['2026/A/s1/missing.DNG'] == 'missing' and status['2026/B/s3/new.txt'] == 'missing', 'missing files')
    if have_dng_compare:
        check(records['2026/A/s1/meta.DNG']['sameview'] is True, 'Rating change is the same view')
        check(any(d['tag'] == 'XMP:XMP-xmp:Rating' for d in records['2026/A/s1/meta.DNG']['differences']), 'Rating difference recorded')
    # Catch-up: creation only, missing paths only, the absent session as one directory.
    check((right / '2026/A/s1/missing.DNG').read_bytes() == files['missing.DNG'][0], 'missing file caught up')
    check((right / '2026/B/s3/new.txt').is_file(), 'absent session caught up')
    check(not (right / '2026/A/s2').exists(), 'file found by name was not copied again')
    check((right / '2026/A/s1/meta.DNG').read_bytes() == files['meta.DNG'][1], 'long-term metadata-only file untouched')
    check((right / '2026/A/s1/image.DNG').read_bytes() == files['image.DNG'][1], 'long-term conflicting file untouched')
    if have_dng_compare:
        # Conflicts kept in the default tree beside foto/, same relative paths.
        check((vol / 'review/2026/A/s1/image.DNG').read_bytes() == files['image.DNG'][0], 'conflict copied to review/')
        check((vol / 'review/2026/A/s1/image.jpg').read_bytes() == files['image.jpg'][0], 'JPEG conflict copied to review/')
        archive = vol / 'dng-compare/shuttle-foto'
        db = sqlite3.connect(archive / 'metadata/differences.sqlite3')
        check(db.execute("SELECT COUNT(*) FROM files WHERE path='2026/A/s1/meta.DNG'").fetchone()[0] == 1, 'indexed in dng-compare')
        restored = t / 'restored.DNG'
        r = subprocess.run(['uv', 'run', 'python', 'preserve_apo.py', 'restore', str(archive), '2026/A/s1/meta.DNG', str(restored)],
                           cwd=home, capture_output=True, text=True)
        check(r.returncode == 0 and restored.read_bytes() == files['meta.DNG'][0], 'restore from the -preservefull delta')
        out = unison(*full)
        check('safe to wipe: 9 of 9 files' in out, 'second run: everything safe\n' + out)
        # -review reruns on the conflicts only; -suffix and -suffix=NAME copy beside the original.
        out = unison('-preserve', '-review', '-suffix')
        check((right / '2026/A/s1/image_2.DNG').read_bytes() == files['image.DNG'][0], 'numbered suffix copy')
        out = unison('-preserve', '-review', '-suffix=shuttle')
        check((right / '2026/A/s1/image_shuttle.jpg').read_bytes() == files['image.jpg'][0], 'named suffix copy')
        out = unison('-preserve', '-review', '-suffix')
        check(not (right / '2026/A/s1/image_3.DNG').exists(), 'an identical numbered copy is reused')
        # Wipe the shuttle and refill it: nothing on the long-term root is deleted, and the archive keeps its rows.
        shutil.rmtree(left / '2026')
        (left / '2026/C').mkdir(parents=True); (left / '2026/C/later.DNG').write_bytes(dng(5))
        out = unison(*full)
        check((right / '2026/A/s1/meta.DNG').is_file() and (right / '2026/C/later.DNG').is_file(), 'wipe and refill')
        check(db.execute("SELECT COUNT(*) FROM files WHERE path='2026/A/s1/meta.DNG'").fetchone()[0] == 1, 'earlier rows kept')
    else:
        print('SKIPPED: dng-compare archive, preservation and conflict-copy checks (no dng-compare, uv or xdelta3)')
    check(all(sha(p) == h for p, h in before.items() if p.exists()), 'shuttle files unchanged')
    print('PASS%d semdiff controls%s' % (checks, '' if have_dng_compare else ' (dng-compare checks skipped)'))
