#!/usr/bin/env python3
"""Milestone 4 controls for packed roots in unison: drive-cache barriers, the
pending list, and recovery after a crash or a damaged container. Synthetic
roots only."""
import argparse, os, pathlib, random, subprocess, sys, tempfile

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

rng = random.Random(13)
with tempfile.TemporaryDirectory(prefix='unison-packdir-recover-') as td:
    t = pathlib.Path(td).resolve()
    quasar, ten, udir = t / 'quasar', t / 'ten', t / 'unisondir'
    udir.mkdir(); ten.mkdir()
    def make_leaf(leaf, n=6):
        d = quasar / leaf; d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            f = d / ('%08x_%d' % (rng.getrandbits(32), rng.choice([320, 1024])))
            f.write_bytes(rng.randbytes(rng.randint(1000, 100000)))
            ns = 1_700_000_000_000_000_000 + rng.randint(0, 10**15); os.utime(f, ns=(ns, ns))
    for leaf in ('0/0000', '0/0001', 'a/0a00'):
        make_leaf(leaf)

    env = dict(os.environ, UNISON=str(udir))
    def unison(*extra, env_extra=None):
        flow = ['-force', str(quasar), '-nodeletion', str(ten), '-perms', '0', '-times',
                '-packdepth', '2', '-packroot', str(ten), '-packbarrier', '0', '-debug', 'packdir']
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', *flow, *extra],
                           env=dict(env, **(env_extra or {})), capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    def pending():
        files = list(udir.glob('pd*.pending'))
        return files[0].read_text().split() if files else []
    def leaves():
        return tree(quasar, only=lambda f: len(f.relative_to(quasar).parts) == 3)
    def unpacked(tag):
        out = t / ('unpacked-' + tag)
        r = subprocess.run([a.packdir, 'unpack-tree', str(ten), str(out), '--skip-retained'], capture_output=True, text=True)
        check(r.returncode == 0, 'unpack-tree: ' + r.stdout + r.stderr)
        return tree(out)

    # 1. Barriers: packbarrier = 0 flushes after every container; a good run clears the pending list.
    rc, out = unison()
    check(rc == 0, 'first run (rc %d):\n%s' % (rc, out))
    barriers = out.count('packdir: barrier after')
    check(barriers >= 3, 'a barrier after each of the 3 containers: %d\n%s' % (barriers, out))
    check(pending() == [], 'pending list cleared after the commit: %r' % pending())
    check(unpacked('1') == leaves(), 'first run complete')

    # 2. A crash inside a transaction: rolled back, pending, verified and redone by the next run.
    make_leaf('a/0a01'); make_leaf('0/0000', 2)
    rc, out = unison(env_extra={'UNISON_PACKDIR_CRASH_AFTER': '1'})
    check(rc == 3, 'the crash hook stops the run inside a transaction (rc %d):\n%s' % (rc, out))
    check(pending() != [], 'the interrupted container is pending')
    rc, out = unison()
    check(rc == 0 and 'damaged' not in out, 'the next run verifies, finds nothing damaged, and completes (rc %d):\n%s' % (rc, out))
    check(pending() == [] and unpacked('2') == leaves(), 'converged after the crash')

    # 3. A crash after the final barrier, before Unison's archives are written: the next run converges.
    make_leaf('a/0a02')
    rc, out = unison(env_extra={'UNISON_PACKDIR_CRASH_BEFORE_COMMIT': '1'})
    check(rc == 4 and (ten / 'a/0a02.sqlar').is_file(), 'stopped after the barrier, container written (rc %d):\n%s' % (rc, out))
    rc, out = unison()
    check(rc == 0 and 'Packing a/0a02' not in out, 'the next run finds the container already right:\n' + out)
    check(pending() == [] and unpacked('3') == leaves(), 'converged after the uncommitted run')

    # 4. A damaged container: found by the next run, set aside, and the leaf brought back from Quasar.
    victim = ten / '0/0001.sqlar'
    member = max((quasar / '0/0001').iterdir(), key=lambda f: f.stat().st_size)
    data = bytearray(victim.read_bytes()); i = data.find(member.read_bytes()[500:564])
    check(i > 0, 'found a member inside the container')
    data[i] ^= 1; victim.write_bytes(bytes(data))
    rc, out = unison()
    aside = list((ten / '0').glob('0001.sqlar.damaged-*'))
    check('is damaged' in out and len(aside) == 1, 'damage detected and the container set aside:\n' + out)
    check('Packing 0/0001' in out and rc == 0, 'the leaf is copied again (rc %d):\n%s' % (rc, out))
    check(subprocess.run([a.packdir, 'verify', str(victim)], capture_output=True).returncode == 0, 'the new container verifies')
    check(unpacked('4') == leaves(), 'converged after the damage')
    rc, out = unison()
    check(rc == 0 and 'Packing' not in out and 'damaged' not in out, 'then quiet:\n' + out)

print('PASS%d packdir recovery controls' % checks)
