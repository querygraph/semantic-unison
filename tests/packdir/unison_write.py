#!/usr/bin/env python3
"""Milestone 3 controls for packed roots in unison: propagation through the
writer. Synthetic roots only: Quasar is a plain tree <H>/<HHHH>/<files> with a
plain file above the packed depth; Ten starts with only a directory of kept
originals beside one leaf, as after Photo's clearing."""
import argparse, hashlib, os, pathlib, random, shutil, subprocess, sys, tempfile

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

def tree(root, only=None):
    return {str(f.relative_to(root)): (f.read_bytes(), f.stat().st_mtime_ns)
            for f in sorted(root.rglob('*')) if f.is_file() and (only is None or only(f))}

rng = random.Random(11)
with tempfile.TemporaryDirectory(prefix='unison-packdir-write-') as td:
    t = pathlib.Path(td).resolve()
    quasar, ten, udir = t / 'quasar', t / 'ten', t / 'unisondir'
    udir.mkdir()
    for leaf in ('0/0000', '0/0001', 'a/0a00', 'a/0a01'):
        d = quasar / leaf; d.mkdir(parents=True)
        for i in range(6):
            f = d / ('%08x_%d' % (rng.getrandbits(32), rng.choice([320, 1024, 2048])))
            f.write_bytes(rng.randbytes(rng.randint(0, 200000)))
            ns = 1_700_000_000_000_000_000 + rng.randint(0, 10**15); os.utime(f, ns=(ns, ns))
    (quasar / 'LEAFSET.json').write_text('{"a plain file above the packed depth": true}\n')
    os.utime(quasar / 'LEAFSET.json', ns=(1_750_000_000_123_456_789,) * 2)
    keep = ten / '0/0001'; keep.mkdir(parents=True)
    same = sorted((quasar / '0/0001').iterdir())[0]
    shutil.copy2(same, keep / same.name)
    (keep / 'old.lrfprev').write_bytes(b'a kept original that Quasar never had')
    kept = tree(keep)

    env = dict(os.environ, UNISON=str(udir))
    def unison(*extra, nodeletion=True):
        flow = ['-force', str(quasar), '-perms', '0', '-times', '-packdepth', '2', '-packroot', str(ten)]
        if nodeletion:
            flow += ['-nodeletion', str(ten)]
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', *flow, *extra], env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    def packdir(*args):
        return subprocess.run([a.packdir, *map(str, args)], capture_output=True, text=True)
    def containers():
        return sorted(ten.glob('*/*.sqlar'))
    def unpacked(tag):
        out = t / ('unpacked-' + tag)
        r = packdir('unpack-tree', ten, out, '--skip-retained')
        check(r.returncode == 0, 'unpack-tree: ' + r.stdout + r.stderr)
        return tree(out)
    def leaves():
        return tree(quasar, only=lambda f: len(f.relative_to(quasar).parts) == 3)

    # 1. First run: every leaf streamed into a container.
    rc, out = unison()
    check(rc in (0, 1) and 'failed' not in out.lower().replace('0 failed', ''), 'first run (rc %d):\n%s' % (rc, out))
    check([c.relative_to(ten).as_posix() for c in containers()] == ['0/0000.sqlar', '0/0001.sqlar', 'a/0a00.sqlar', 'a/0a01.sqlar'],
          'one container per leaf: %r' % containers())
    r = packdir('verify', *containers())
    check(r.returncode == 0, 'containers verify: ' + r.stdout)
    want = {k: v for k, v in leaves().items() if k != '0/0001/' + same.name}  # present-plain: not packed
    check(unpacked('1') == want, 'unpacked containers equal the Quasar leaves, bytes and ns mtimes')
    check(tree(keep) == kept, 'kept originals untouched')
    check((ten / 'LEAFSET.json').read_bytes() == (quasar / 'LEAFSET.json').read_bytes()
          and (ten / 'LEAFSET.json').stat().st_mtime_ns == (quasar / 'LEAFSET.json').stat().st_mtime_ns,
          'the plain file above the packed depth arrives plain, with its mtime')
    check(not [p for p in ten.rglob('*') if p.name.endswith(('-journal', '-wal', '-shm'))], 'no journal left beside containers')
    check(not [p for p in ten.rglob('*') if p.is_dir() and p.relative_to(ten).as_posix() in ('0/0000', 'a/0a00', 'a/0a01')],
          'no plain leaf directories created')

    # 2. Nothing changed: nothing written.
    before = tree(ten)
    rc, out = unison()
    check('Packing' not in out and tree(ten) == before, 'a quiet rerun writes nothing:\n' + out)

    # 3. A change and an addition are packed; a deletion is skipped under nodeletion.
    changed = sorted((quasar / 'a/0a00').iterdir())[0]
    changed.write_bytes(b'new bytes'); os.utime(changed, ns=(1_800_000_000_000_000_001,) * 2)
    (quasar / '0/0000/added_2048').write_bytes(b'a new level')
    gone = sorted((quasar / 'a/0a01').iterdir())[0]; gone_name = gone.name; gone.unlink()
    rc, out = unison()
    check('Packing a/0a00/' + changed.name in out and 'Packing 0/0000/added_2048' in out, 'change and addition packed:\n' + out)
    check('a/0a01/' + gone_name in out and 'Retaining' not in out, 'deletion skipped under nodeletion:\n' + out)
    u = unpacked('3')
    check(u['a/0a00/' + changed.name] == (b'new bytes', 1_800_000_000_000_000_001) and u['0/0000/added_2048'][0] == b'a new level',
          'new bytes and mtime in the containers')
    check('a/0a01/' + gone_name in u, 'the skipped deletion leaves the member in place')
    check(packdir('verify', *containers()).returncode == 0, 'containers verify after the update')

    # 4. Without nodeletion on Ten: the deletion is kept as retained and drops out of view.
    rc, out = unison(nodeletion=False)
    check('Retaining a/0a01/' + gone_name in out and 'not identical' not in out, 'deletion becomes retained, archives agree:\n' + out)
    check('Failed [0/0001/old.lrfprev]' in out and 'a kept original' in out and (keep / 'old.lrfprev').is_file(),
          'a kept original beside a container is never deleted, and says so:\n' + out)
    listing = packdir('list', ten / 'a/0a01.sqlar').stdout
    check(any(l.startswith(gone_name + '\t') and l.endswith('retained') for l in listing.splitlines()), 'member marked retained, bytes kept')
    rc, out = unison(nodeletion=False)
    check('a/0a01/' + gone_name not in out and 'Packing' not in out, 'a retained member is not resurrected or retained again:\n' + out)
    check(tree(keep) == kept, 'kept originals still untouched')

    # 5. A kept original whose Quasar version changes: the new bytes are packed beside it.
    p = quasar / '0/0001' / same.name
    p.write_bytes(b'Quasar re-rendered this level'); os.utime(p, ns=(1_800_000_000_000_000_002,) * 2)
    rc, out = unison()
    check('Packing 0/0001/' + same.name in out, 'changed kept original is packed:\n' + out)
    check(tree(keep) == kept, 'the plain original stays as it was')
    check(unpacked('5')['0/0001/' + same.name][0] == b'Quasar re-rendered this level', 'the container holds the new bytes')
    rc, out = unison()
    check('Packing' not in out, 'then quiet: the member wins over the plain original:\n' + out)

print('PASS%d packdir write controls' % checks)
