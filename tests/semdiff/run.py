#!/usr/bin/env python3
"""End-to-end controls for unison -semdiff and unison-dngscan -semdiff.

Synthetic DNG and JPEG fixtures only, in a private temporary directory: a
shuttle root and a long-term root beside which the review tree and the
dng-compare archive are created. Runs the real binaries and checks the files
they leave, the summaries, the dng-compare index and a restore from a
-preservefull delta. dng-compare's metadata_rules.json and exiftool-rs worker
are found through DNG_COMPARE_HOME or ~/src/dng-compare, and its OCaml
dng-archive through DNG_ARCHIVE, PATH or the opam switches; without them the
archive checks are skipped and reported as skipped. Stand-in uv and python
commands first on PATH prove that no Python runs. When dng-compare's Python
tools are present, preserve_apo.py also restores the delta dng-archive wrote."""
import argparse, hashlib, json, os, pathlib, shutil, sqlite3, struct, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True, help='text-UI unison binary of this build')
p.add_argument('--dngscan', required=True, help='unison-dngscan of the same build')
a = p.parse_args()
home = pathlib.Path(os.environ.get('DNG_COMPARE_HOME', pathlib.Path.home() / 'src/dng-compare'))
archiver = next((c for c in [os.environ.get('DNG_ARCHIVE'), shutil.which('dng-archive')] +
                 [str(pathlib.Path.home() / '.opam' / sw / 'bin/dng-archive') for sw in ('5.2.0+ox', 'default')]
                 if c and os.access(c, os.X_OK)), None)
have_dng_compare = (home / 'metadata_rules.json').is_file() and archiver and shutil.which('xdelta3')


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

    # Every disk counts as spinning, so the one-reader-per-disk lock is exercised.
    # Stand-ins first on PATH record any Python that a run starts.
    stand_ins, python_calls = t / 'no-python', t / 'python-calls'
    stand_ins.mkdir()
    for name in ('uv', 'python', 'python3'):
        (stand_ins / name).write_text('#!/bin/sh\necho "%s $*" >> %s\nexit 99\n' % (name, python_calls))
        (stand_ins / name).chmod(0o755)
    env = dict(os.environ, UNISON=str(t / 'unisondir'), UNISON_SEMDIFF_ONE_READER='all',
               DNG_ARCHIVE=archiver or '', PATH=str(stand_ins) + os.pathsep + os.environ['PATH'])
    (t / 'unisondir').mkdir()
    def unison(*args, rc=0):
        r = subprocess.run([a.unison, str(left), str(right), '-semdiff', '-batch', '-semdiffscanner', a.dngscan, *args],
                           env=env, capture_output=True, text=True)
        check(r.returncode == rc, 'unison exited %d:\n%s%s' % (r.returncode, r.stdout, r.stderr))
        return r.stdout + r.stderr

    full = ['-preserve', '-preservefull', '-sameview'] if have_dng_compare else ['-sameview']
    out = unison(*full)
    if have_dng_compare:
        # stdout and stderr are captured apart, so check the lines, not their order.
        check('checking the copied files' in out and 'safe to wipe: 7 of 9 files' in out and
              'safe to wipe: 9 of 9 files' in out, 'status before and after the copy\n' + out)
    report = next((t / 'unisondir').glob('semdiff-*.jsonl'))
    records = {json.loads(l)['rel']: json.loads(l)['targets'][0] for l in report.read_text().splitlines()}
    status = {k: v['status'] for k, v in records.items()}
    check(status['2026/A/s1/same.DNG'] == 'identical' and status['2026/A/s1/same.jpg'] == 'identical', 'identical pairs')
    check(status['2026/A/s1/image.DNG'] == 'image-differs' and status['2026/A/s1/image.jpg'] == 'image-differs', 'image differences')
    check(status['2026/A/s1/meta.DNG'] == 'metadata-only' and status['2026/A/s1/meta.jpg'] == 'metadata-only', 'metadata-only pairs')
    check(records['2026/A/s2/moved.DNG']['how'] == 'name' and status['2026/A/s2/moved.DNG'] == 'identical', 'match by name')
    # Missing on the first pass, copied, then compared by the check after the copy.
    check(status['2026/A/s1/missing.DNG'] == 'identical' and status['2026/B/s3/new.txt'] == 'identical',
          'missing files compared after the copy: %r' % {k: status[k] for k in ('2026/A/s1/missing.DNG', '2026/B/s3/new.txt')})
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
        check((vol / 'review/foto/2026/A/s1/image.DNG').read_bytes() == files['image.DNG'][0], 'conflict copied to review/foto/')
        check((vol / 'review/foto/2026/A/s1/image.jpg').read_bytes() == files['image.jpg'][0], 'JPEG conflict copied to review/foto/')
        archive = vol / 'dng-compare/shuttle-foto'
        db = sqlite3.connect(archive / 'metadata/differences.sqlite3')
        check(db.execute("SELECT COUNT(*) FROM files WHERE path='2026/A/s1/meta.DNG'").fetchone()[0] == 1, 'indexed in dng-compare')
        restored = t / 'restored.DNG'
        r = subprocess.run([archiver, 'restore', str(archive), '2026/A/s1/meta.DNG', str(restored)], capture_output=True, text=True)
        check(r.returncode == 0 and restored.read_bytes() == files['meta.DNG'][0], 'restore from the -preservefull delta')
        check(not python_calls.exists(), 'no Python ran: ' + (python_calls.read_text() if python_calls.exists() else ''))
        if (home / 'preserve_apo.py').is_file() and shutil.which('uv'):
            restored.unlink()
            r = subprocess.run(['uv', 'run', 'python', 'preserve_apo.py', 'restore', str(archive), '2026/A/s1/meta.DNG', str(restored)],
                               cwd=home, capture_output=True, text=True)
            check(r.returncode == 0 and restored.read_bytes() == files['meta.DNG'][0], 'Python restores the OCaml delta')
        out = unison(*full)
        check('safe to wipe: 9 of 9 files' in out, 'second run: everything safe\n' + out)
        # dngc's unified layout. dng-archive writes a new archive's byte section into
        # ARCHIVE/bytes/ (dng-compare 6a28203 and later); an archive written before
        # that has it at the top (recovery.sqlite3 and no bytes/), and `dngc migrate`
        # moves it into bytes/. The reader must find either. Whatever layout the
        # installed dng-archive wrote, switch to the other with the renames dngc.md
        # lists and back: the summary counts the same files preserved in full each time.
        def summary(*extra):
            reports = sorted(str(p) for p in (t / 'unisondir').glob('semdiff-*.jsonl'))
            r = subprocess.run([a.dngscan, '-summarize', *extra, *reports], env=env, capture_output=True, text=True)
            line = [l for l in r.stdout.splitlines() if l.startswith('safe to wipe:')]
            check(len(line) == 1, 'one summary line:\n' + r.stdout + r.stderr)
            return line[0]
        byte_entries = ['recovery.sqlite3', 'recovery.sqlite3-wal', 'recovery.sqlite3-shm', 'recovery.sqlite3-journal',
                        'recovery.sqlite3.engine.json', 'deltas', 'originals', 'manifest.jsonl', 'inventory.json',
                        'directories.json', 'summary.json', 'matching.json', 'xmp-original', 'image-comparison',
                        'finalization-backend.json', '.byte-preservation.lock', 'versions']
        def to_bytes():
            (archive / 'bytes').mkdir()
            for name in byte_entries:
                if (archive / name).exists():
                    (archive / name).rename(archive / 'bytes' / name)
        def to_top():
            for name in byte_entries:
                if (archive / 'bytes' / name).exists():
                    (archive / 'bytes' / name).rename(archive / name)
            (archive / 'bytes').rmdir()
        def restores(byte_section, label):
            restored = t / 'restored-layout.DNG'
            restored.unlink(missing_ok=True)
            r = subprocess.run([archiver, 'restore', str(byte_section), '2026/A/s1/meta.DNG', str(restored)], capture_output=True, text=True)
            check(r.returncode == 0 and restored.read_bytes() == files['meta.DNG'][0], 'restore from ' + label + ':\n' + r.stdout + r.stderr)
        def bytes_layout_checks():
            check((archive / 'bytes/manifest.jsonl').is_file() and not (archive / 'recovery.sqlite3').exists()
                  and (archive / 'provenance.json').is_file() and (archive / 'metadata').is_dir(),
                  'bytes/ holds the byte section; provenance and metadata at the top')
            check(summary() == written, 'same summary from bytes/: %s vs %s' % (summary(), written))
            # dng-compare's shared rule: an archive named as ARCHIVE/bytes is its parent, never nested.
            check(summary('-preservedb', str(archive / 'bytes')) == written, '-preservedb ARCHIVE/bytes reads the same archive')
            check(not (archive / 'bytes/bytes').exists() and not (archive / 'bytes/metadata').exists(), 'no nested bytes/ or metadata/')
            restores(archive / 'bytes', 'ARCHIVE/bytes')
            # A byte section the reader cannot find would drop those files from "preserved in full".
            (archive / 'bytes/manifest.jsonl').rename(archive / 'bytes/manifest.jsonl.away')
            check(summary() != written, 'control: without the manifest the summary changes')
            (archive / 'bytes/manifest.jsonl.away').rename(archive / 'bytes/manifest.jsonl')
        def legacy_layout_checks():
            check((archive / 'manifest.jsonl').is_file() and (archive / 'recovery.sqlite3').is_file()
                  and not (archive / 'bytes').exists(), 'legacy layout: byte section at the top')
            check(summary() == written, 'same summary from the top: %s vs %s' % (summary(), written))
            restores(archive, 'a legacy ARCHIVE')
        new_layout = (archive / 'bytes').is_dir()
        check(new_layout != (archive / 'recovery.sqlite3').is_file(), 'exactly one layout written: %r' % sorted(os.listdir(archive)))
        written = summary()
        check(' 0 preserved in full' not in written, 'the control preserves something in full: ' + written)
        if new_layout:
            bytes_layout_checks(); to_top(); legacy_layout_checks(); to_bytes(); bytes_layout_checks()
        else:
            legacy_layout_checks(); to_bytes(); bytes_layout_checks(); to_top(); legacy_layout_checks()
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
        check(db.execute("SELECT COUNT(*) FROM files WHERE path='2026/A/s1/meta.DNG'").fetchone()[0] == 1, 'earlier rows kept: %r' % db.execute("SELECT path,version,batch FROM files WHERE path='2026/A/s1/meta.DNG'").fetchall())
        # A later shuttle cycle brings new contents at an old path: a new version row, nothing replaced.
        (left / '2026/A/s1').mkdir(parents=True)
        (left / '2026/A/s1/meta.DNG').write_bytes(dng(5)); os.utime(left / '2026/A/s1/meta.DNG', (1e9, 1e9))
        # A dng-archive that keeps no versions (its usage lacks restore's --version
        # LABEL) would replace the earlier record: that path is not preserved again.
        old_archiver = t / 'dng-archive-without-versions'
        old_archiver.write_text('#!/bin/sh\nif [ "$1" = --help ]; then "%s" --help 2>&1 | sed "s/ \\[--version LABEL\\]//"; exit 0; fi\n'
                                'echo "$@" >> "%s.calls"; exec "%s" "$@"\n' % (archiver, old_archiver, archiver))
        old_archiver.chmod(0o755)
        env['DNG_ARCHIVE'] = str(old_archiver)
        out = unison(*full, rc=1)  # not safe to wipe: exit 1
        env['DNG_ARCHIVE'] = archiver
        versions = [v for v, in db.execute("SELECT version FROM files WHERE path='2026/A/s1/meta.DNG' ORDER BY version")]
        check(len(versions) == 2 and versions[0] == '' and versions[1] != '', 'second version recorded: %r' % versions)
        check('already holds another version' in out and 'keeps no versions' in out,
              'a dng-archive without versions never replaces another version\n' + out)
        calls = pathlib.Path(str(old_archiver) + '.calls')
        check(not calls.exists() or 'preserve' not in calls.read_text(), 'nothing preserved by it: ' + (calls.read_text() if calls.exists() else ''))
        # With versions (dng-compare 992eff7 on), the refill is preserved: the earlier
        # record stays restorable by its label, and the shuttle is safe to wipe again.
        sections = [archive / 'bytes', archive]
        section = next(d for d in sections if (d / 'recovery.sqlite3').is_file())
        out = unison(*full)
        check('preserving 1 files again' in out and 'safe to wipe: 2 of 2 files' in out, 'refill preserved as a new version\n' + out)
        rdb = sqlite3.connect(section / 'recovery.sqlite3')
        labels = [v for v, in rdb.execute("SELECT version FROM versions WHERE path='2026/A/s1/meta.DNG'")]
        rdb.close()
        check(len(labels) == 1, 'one earlier version kept: %r' % labels)
        for label, want in ((None, dng(5)), (labels[0], files['meta.DNG'][0])):
            restored = t / 'restored-version.DNG'
            restored.unlink(missing_ok=True)
            r = subprocess.run([archiver, 'restore', str(archive), '2026/A/s1/meta.DNG', str(restored)]
                               + (['--version', label] if label else []), capture_output=True, text=True)
            check(r.returncode == 0 and restored.read_bytes() == want, 'restore %s:\n%s%s' % (label or 'current', r.stdout, r.stderr))
        check((right / '2026/A/s1/meta.DNG').read_bytes() == files['meta.DNG'][1], 'long-term file still untouched')
        check(not ((archive / 'recovery.sqlite3').exists() and (archive / 'bytes').exists()),
              'later runs keep one layout: %r' % sorted(os.listdir(archive)))
    else:
        print('SKIPPED: dng-compare archive, preservation and conflict-copy checks (no dng-compare rules, dng-archive or xdelta3)')
    # The tool never writes the shuttle (meta.DNG was rewritten by this test for the second cycle).
    check(all(sha(p) == h for p, h in before.items() if p.exists() and p.name != 'meta.DNG'), 'shuttle files unchanged')
    check(not python_calls.exists(), 'no Python ran in any run: ' + (python_calls.read_text() if python_calls.exists() else ''))
    print('PASS%d semdiff controls%s' % (checks, '' if have_dng_compare else ' (dng-compare checks skipped)'))
