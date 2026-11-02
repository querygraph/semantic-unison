#!/usr/bin/env python3
"""Clone preservation into a packed root (docs/clone-preservation.md, phase 3).
Synthetic roots only, on macOS APFS (the system temporary directory): a plain
source with APFS clone groups inside one leaf and across leaves, and an
identical file that is not a clone, is synchronized with -clones into a packed
root. Each group's bytes are stored once, the other members as packdir clone
references; unpack-tree recreates the groups. A second run adds a clone of a
file packed in the first. Without -clones nothing is a reference."""
import argparse, ctypes, ctypes.util, os, pathlib, random, shutil, sqlite3, struct, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True)
p.add_argument('--packdir', required=True)
a = p.parse_args()
if sys.platform != 'darwin':
    sys.exit('needs macOS (APFS clone ids)')
checks = 0

def check(ok, message):
    global checks
    if not ok:
        sys.exit('FAIL: ' + message)
    checks += 1

libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
class attrlist(ctypes.Structure):
    _fields_ = [('bitmapcount', ctypes.c_ushort), ('reserved', ctypes.c_ushort), ('commonattr', ctypes.c_uint),
                ('volattr', ctypes.c_uint), ('dirattr', ctypes.c_uint), ('fileattr', ctypes.c_uint),
                ('forkattr', ctypes.c_uint)]
def clone_id(path):
    al = attrlist(5, 0, 0x80000000, 0, 0, 0, 0x100 | 0x1000)
    buf = ctypes.create_string_buffer(64)
    if libc.getattrlist(str(path).encode(), ctypes.byref(al), buf, 64, 0x20 | 0x1) != 0:
        raise OSError(ctypes.get_errno(), str(path))
    return struct.unpack_from('<QI', buf.raw, 24)

def tree(root):
    return {str(f.relative_to(root)): (f.read_bytes(), f.stat().st_mtime_ns)
            for f in sorted(root.rglob('*')) if f.is_file()}

def db(path, sql):
    c = sqlite3.connect(path)
    try:
        return sorted(c.execute(sql).fetchall())
    finally:
        c.close()

rng = random.Random(5)
with tempfile.TemporaryDirectory(prefix='unison-packdir-clones-') as td:
    t = pathlib.Path(td).resolve()
    src, udir = t / 'quasar', t / 'unisondir'
    udir.mkdir()
    for leaf in ('lr/0000', 'lr/0001', 'pm/0000'):
        (src / leaf).mkdir(parents=True)
    x = src / 'lr/0000/x'; x.write_bytes(rng.randbytes(250000))
    subprocess.run(['cp', '-c', x, src / 'lr/0000/y'], check=True)        # same leaf
    subprocess.run(['cp', '-c', x, src / 'pm/0000/x-pm'], check=True)     # other leaf
    shutil.copy2(x, src / 'lr/0001/z')                                    # identical, not a clone
    (src / 'pm/0000/plain').write_bytes(b'plain\n')

    def unison(target, *extra):
        target.mkdir(exist_ok=True)
        env = dict(os.environ, UNISON=str(udir))
        flow = ['-force', str(src), '-perms', '0', '-times', '-packdepth', '2', '-packroot', str(target)]
        r = subprocess.run([a.unison, str(src), str(target), '-batch', *flow, *extra], env=env, capture_output=True, text=True)
        check(r.returncode in (0, 1) and 'failed' not in (r.stdout + r.stderr).lower().replace('0 failed', ''),
              'unison (rc %d):\n%s%s' % (r.returncode, r.stdout, r.stderr))
    def packdir(*args):
        r = subprocess.run([a.packdir, *map(str, args)], capture_output=True, text=True)
        check(r.returncode == 0, 'packdir %s: %s%s' % (args[0], r.stdout, r.stderr))
        return r.stdout

    ten = t / 'ten'
    unison(ten, '-clones')
    lr0, lr1, pm0 = ten / 'lr/0000.sqlar', ten / 'lr/0001.sqlar', ten / 'pm/0000.sqlar'
    packdir('verify', lr0, lr1, pm0)
    check(db(lr0, 'SELECT name FROM sqlar') == [('x',)], 'x holds the bytes: %s' % db(lr0, 'SELECT name FROM sqlar'))
    check(db(lr0, 'SELECT name, original FROM packdir_clone') == [('y', 'x')], 'y references x')
    check(db(pm0, 'SELECT name, original FROM packdir_clone') == [('x-pm', '../../lr/0000/x')], 'x-pm references x')
    check(db(lr1, 'SELECT name FROM sqlar') == [('z',)], 'z, not a clone, holds its own bytes')
    back = t / 'back'
    packdir('unpack-tree', ten, back)
    check(tree(back) == tree(src), 'unpack-tree gives back the source, bytes and mtimes')
    g = clone_id(back / 'lr/0000/x')
    check(g[1] == 3 and clone_id(back / 'lr/0000/y')[0] == g[0] and clone_id(back / 'pm/0000/x-pm')[0] == g[0],
          'x, y and x-pm are one clone group again')
    check(clone_id(back / 'lr/0001/z')[1] == 1, 'z stays independent')

    # A second run: a new clone of x, packed in the first, references it.
    subprocess.run(['cp', '-c', x, src / 'pm/0000/x-pm2'], check=True)
    unison(ten, '-clones')
    check(('x-pm2', '../../lr/0000/x') in db(pm0, 'SELECT name, original FROM packdir_clone'),
          'a later clone references the packed original: %s' % db(pm0, 'SELECT name, original FROM packdir_clone'))
    packdir('verify', lr0, lr1, pm0)
    back2 = t / 'back2'
    packdir('unpack-tree', ten, back2)
    check(tree(back2) == tree(src), 'second unpack gives back the source')

    # Without -clones: every file holds its bytes.
    plain = t / 'ten-plain'
    shutil.rmtree(udir); udir.mkdir()
    unison(plain)
    check(all(db(c, 'SELECT count(*) FROM packdir_clone') in ([(0,)], []) for c in plain.rglob('*.sqlar')),
          'no references without -clones')

print('ok %d packed-root clone checks' % checks)
