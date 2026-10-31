#!/usr/bin/env python3
"""Milestone 6 controls for packed roots in unison: the packed marker, and
the way back to plain files. A packed root carries .unison-packed with its
depth; any run with another packdir setting, or none, refuses it instead of
copying everything again beside the containers; unison-packdir unpack-tree
turns it back into plain files. Synthetic roots only."""
import argparse, os, pathlib, random, shutil, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True)
p.add_argument('--packdir', required=True)
a = p.parse_args()
checks = 0

def check(ok, message):
    global checks
    if not ok:
        sys.exit('FAIL: ' + message)
    checks += 1

def tree(root):
    return {str(f.relative_to(root)): (f.read_bytes(), f.stat().st_mtime_ns) for f in sorted(root.rglob('*')) if f.is_file()}

rng = random.Random(19)
with tempfile.TemporaryDirectory(prefix='unison-packdir-marker-') as td:
    t = pathlib.Path(td).resolve()
    quasar, ten, udir = t / 'quasar', t / 'ten', t / 'unisondir'
    ten.mkdir(); udir.mkdir()
    for leaf in ('0/0000', 'a/0a00'):
        d = quasar / leaf; d.mkdir(parents=True)
        for i in range(4):
            f = d / ('%08x_320' % rng.getrandbits(32)); f.write_bytes(rng.randbytes(5000))
    env = dict(os.environ, UNISON=str(udir))
    def unison(*args):
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', '-force', str(quasar), '-nodeletion', str(ten),
                            '-perms', '0', '-times', *args], env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    packed = ['-packdepth', '2', '-packroot', str(ten)]

    rc, out = unison(*packed)
    check(rc == 0 and (ten / '.unison-packed').read_text() == 'unison-packdir/1 depth=2\n', 'the packed run writes the marker:\n' + out)
    rc, out = unison(*packed)
    check(rc == 0 and '.unison-packed' not in out and 'Packing' not in out, 'the marker is not in Unison\'s view:\n' + out)

    before = tree(ten)
    for args, what in (([], 'no packdepth'), (['-packdepth', '1', '-packroot', str(ten)], 'another depth')):
        rc, out = unison(*args)
        check(rc != 0 and 'is packed (packdepth = 2' in out and 'unpack-tree' in out, what + ': refused (rc %d):\n%s' % (rc, out))
        check(tree(ten) == before, what + ': nothing written')

    # Back to plain files: unpack, remove the containers and the marker, and a plain run is quiet.
    plain = t / 'plain'
    r = subprocess.run([a.packdir, 'unpack-tree', str(ten), str(plain)], capture_output=True, text=True)
    check(r.returncode == 0 and tree(plain) == tree(quasar), 'unpack-tree gives back the Quasar tree:\n' + r.stdout + r.stderr)
    shutil.rmtree(ten); shutil.copytree(plain, ten); shutil.rmtree(udir); udir.mkdir()
    rc, out = unison()
    check(rc == 0 and 'Copying' not in out and 'Updating' not in out, 'after unpacking, a plain run has nothing to do:\n' + out)

print('PASS%d packdir marker controls' % checks)
