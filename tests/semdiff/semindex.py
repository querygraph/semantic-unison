#!/usr/bin/env python3
"""Controls for unison -semdiff -semindex: phindex indexes of the two trees.

Synthetic DNGs in a private temporary directory, and two hand-made indexes
with phindex's `files` table. Runs the real binaries and checks that a pair
whose rows are current is settled without reading either file (the files are
made unreadable), that a file is found by its content under another name,
that a stale row is not trusted, and that only what is missing is copied."""
import argparse, hashlib, json, os, pathlib, sqlite3, struct, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True, help='text-UI unison binary of this build')
p.add_argument('--dngscan', required=True, help='unison-dngscan of the same build')
a = p.parse_args()

FILES = """
CREATE TABLE files (
  path TEXT PRIMARY KEY, size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, ino INTEGER NOT NULL,
  dev INTEGER NOT NULL, sha256 TEXT, hashed_unix INTEGER, seen_unix INTEGER NOT NULL, gone INTEGER NOT NULL DEFAULT 0,
  dng_blocks TEXT, dng_blocks_err TEXT, image_data TEXT, image_err TEXT);
CREATE INDEX files_sha ON files(sha256);
CREATE INDEX files_dng_blocks ON files(dng_blocks);
CREATE INDEX files_image ON files(image_data);"""


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


checks = 0
def check(ok, message):
    global checks
    if not ok:
        sys.exit('FAIL: ' + message)
    checks += 1


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


class Index:
    def __init__(self, file):
        self.file = file
        self.db = sqlite3.connect(file)
        self.db.executescript(FILES)

    def row(self, path, image=None, raw=None, mtime_ns=None):
        """Lists the file at path as it is now, or with another modification time."""
        st = os.stat(path)
        self.db.execute('INSERT OR REPLACE INTO files(path, size, mtime_ns, ino, dev, sha256, seen_unix, gone, dng_blocks, image_data) '
                        'VALUES(?, ?, ?, 0, 0, ?, 0, 0, ?, ?)',
                        (str(path), st.st_size, st.st_mtime_ns if mtime_ns is None else mtime_ns,
                         hashlib.sha256(path.read_bytes()).hexdigest(), raw, image))

    def done(self):
        self.db.commit(); self.db.close()
        return str(self.file)


with tempfile.TemporaryDirectory(prefix='unison-semindex-') as td:
    t = pathlib.Path(td).resolve()
    left, right = t / 'source/foto', t / 'longterm/foto'
    L, R = Index(t / 'left.sqlite'), Index(t / 'right.sqlite')
    both = lambda rel, l, r: (put(left / rel, l), put(right / rel, r))

    # Same path, same bytes; then neither file can be read.
    same = both('2026/A/same.DNG', dng(1), dng(1))
    # Same path, another rating: the rows share the raw blocks.
    meta = both('2026/A/meta.DNG', dng(3), dng(1))
    for f in same: (L if f == same[0] else R).row(f, raw='raw-same')
    for f in meta: (L if f == meta[0] else R).row(f, raw='raw-meta')
    # Moved and renamed on the long-term side: found by SHA-256.
    moved = put(left / '2026/B/moved.DNG', dng(4)), put(right / 'elsewhere/renamed.DNG', dng(4))
    L.row(moved[0], raw='raw-moved'); R.row(moved[1], raw='raw-moved')
    # Moved, renamed and edited there: found by its raw blocks.
    edited = put(left / '2026/B/edited.DNG', dng(2, raw_flip=9)), put(right / 'elsewhere/edited-there.DNG', dng(5, raw_flip=9))
    L.row(edited[0], raw='raw-edited'); R.row(edited[1], raw='raw-edited')
    # One name twice on the long-term side: ambiguous by name, settled by content.
    amb = put(left / '2026/C/twice.DNG', dng(1, raw_flip=20))
    put(right / 'x/twice.DNG', dng(1, raw_flip=21)); amb_right = put(right / 'y/twice.DNG', dng(1, raw_flip=20))
    L.row(amb, raw='raw-amb'); R.row(right / 'x/twice.DNG', raw='raw-other'); R.row(amb_right, raw='raw-amb')
    # A stale row: the long-term file was rewritten after it was indexed.
    stale = both('2026/A/stale.DNG', dng(1, raw_flip=30), dng(1, raw_flip=30))
    L.row(stale[0], raw='raw-stale'); R.row(stale[1], raw='raw-stale', mtime_ns=1)
    changed = both('2026/A/changed.DNG', dng(1, raw_flip=40), dng(1, raw_flip=40))
    L.row(changed[0], raw='raw-changed'); R.row(changed[1], raw='raw-changed')
    changed[1].write_bytes(dng(1, raw_flip=41)); os.utime(changed[1], ns=(1, 2 * 10 ** 18))
    # Only on the source.
    new = put(left / '2026/D/new.DNG', dng(2, raw_flip=50)); L.row(new, raw='raw-new')
    indexes = [L.done(), R.done()]
    for f in (*same, *meta):
        f.chmod(0)

    env = dict(os.environ, UNISON=str(t / 'unisondir'))
    (t / 'unisondir').mkdir()
    def unison(*args, rc=0):
        r = subprocess.run([a.unison, str(left), str(right), '-semdiff', '-batch', '-v', '-semdiffscanner', a.dngscan, *args],
                           env=env, capture_output=True, text=True)
        check(r.returncode in (rc if isinstance(rc, tuple) else (rc,)), 'unison exited %d:\n%s%s' % (r.returncode, r.stdout, r.stderr))
        return r.stdout + r.stderr

    try:
        out = unison('-semindex', indexes[0], '-semindex', indexes[1], rc=(0, 1))
        report = next((t / 'unisondir').glob('semdiff-*.jsonl'))
        records = {json.loads(l)['rel']: json.loads(l)['targets'][0] for l in report.read_text().splitlines()}
        st = lambda rel: (records[rel]['status'], records[rel]['how'])
        check(st('2026/A/same.DNG') == ('identical', 'path'), 'identical from the rows, unread: %r\n%s' % (st('2026/A/same.DNG'), out))
        check(st('2026/A/meta.DNG') == ('metadata-only', 'path') and records['2026/A/meta.DNG']['image'] == 'same',
              'same image from the rows, unread: %r' % (records['2026/A/meta.DNG'],))
        check('phindex indexes' in records['2026/A/meta.DNG']['reason'], 'the report says where the verdict came from')
        check(st('2026/B/moved.DNG') == ('identical', 'index') and records['2026/B/moved.DNG']['match'] == str(moved[1]),
              'a renamed file found by SHA-256: %r' % (records['2026/B/moved.DNG'],))
        check(st('2026/B/edited.DNG') == ('metadata-only', 'index') and records['2026/B/edited.DNG']['match'] == str(edited[1]),
              'a renamed and edited file found by its raw blocks: %r' % (records['2026/B/edited.DNG'],))
        check(st('2026/C/twice.DNG') == ('identical', 'index') and records['2026/C/twice.DNG']['match'] == str(amb_right),
              'an ambiguous name settled by content: %r' % (records['2026/C/twice.DNG'],))
        check(st('2026/A/stale.DNG') == ('identical', 'path'), 'a stale row is not used; the pair is read: %r' % (st('2026/A/stale.DNG'),))
        check(records['2026/A/changed.DNG']['status'] in ('image-differs', 'differs'),
              'a file rewritten after it was indexed is compared, not trusted: %r' % (st('2026/A/changed.DNG'),))
        check('5 identical' not in out and 'without reading the files: 3 identical, 2 with the same image; 3 found by content' in out,
              'the count of what the indexes settled\n' + out)
        # Catch-up: only the file with no copy anywhere.
        check((right / '2026/D/new.DNG').read_bytes() == new.read_bytes(), 'the new file was copied')
        for rel in ('2026/B/moved.DNG', '2026/B/edited.DNG', '2026/C/twice.DNG'):
            check(not (right / rel).exists(), rel + ' was found elsewhere and not copied again')
        check(changed[1].read_bytes() == dng(1, raw_flip=41), 'a differing long-term file is left as it is')
        for f in (t / 'left.sqlite', t / 'right.sqlite'):
            check(not [x for x in t.iterdir() if x.name.startswith(f.name) and x != f], 'nothing written beside ' + f.name)
        # Without the indexes the unreadable pairs cannot be compared, and the renamed files look missing.
        (t / 'unisondir2').mkdir(); env['UNISON'] = str(t / 'unisondir2')
        unison(rc=(0, 1))
        report = next((t / 'unisondir2').glob('semdiff-*.jsonl'))
        plain = {json.loads(l)['rel']: json.loads(l)['targets'][0] for l in report.read_text().splitlines()}
        check(plain['2026/A/same.DNG']['status'] == 'error', 'without an index the unreadable pair is an error: %r' % plain['2026/A/same.DNG']['status'])
        check(plain['2026/C/twice.DNG']['status'] == 'ambiguous', 'without an index the name stays ambiguous')
        # An index that is not one is refused.
        bad = t / 'bad.sqlite'
        db = sqlite3.connect(bad); db.execute('CREATE TABLE files(path TEXT)'); db.commit(); db.close()
        r = subprocess.run([a.dngscan, '-semdiff', str(right), '-semindex', str(bad), str(left)], capture_output=True, text=True, env=env)
        check(r.returncode != 0 and 'not a phindex index' in r.stdout + r.stderr, 'a database that is not an index is refused')
    finally:
        for f in (*same, *meta):
            f.chmod(0o644)
print(f'{checks} checks passed')
