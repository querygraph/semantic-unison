#!/usr/bin/env python3
"""Milestone 5 controls for packed roots in unison: parallel workers. The
same synthetic tree, packed by one worker and by four, gives the same
members; a worker that crashes fails only its item, and the next run
converges. Synthetic roots only."""
import argparse, os, pathlib, random, shutil, subprocess, sys, tempfile, time

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

rng = random.Random(17)
with tempfile.TemporaryDirectory(prefix='unison-packdir-parallel-') as td:
    t = pathlib.Path(td).resolve()
    quasar = t / 'quasar'
    for h in '0a':
        for i in range(20):
            d = quasar / h / ('%s%03x' % (h, i)); d.mkdir(parents=True)
            for j in range(rng.randint(3, 9)):
                f = d / ('%08x_%d' % (rng.getrandbits(32), rng.choice([320, 1024])))
                f.write_bytes(rng.randbytes(rng.randint(1000, 120000)))
                ns = 1_700_000_000_000_000_000 + rng.randint(0, 10**15); os.utime(f, ns=(ns, ns))
    leaves = {k: v for k, v in tree(quasar).items()}

    def run(ten, udir, workers, env_extra=None):
        ten.mkdir(exist_ok=True); udir.mkdir(exist_ok=True)
        flow = ['-force', str(quasar), '-nodeletion', str(ten), '-perms', '0', '-times',
                '-packdepth', '2', '-packroot', str(ten), '-packworkers', str(workers)]
        t0 = time.monotonic()
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', *flow],
                           env=dict(os.environ, UNISON=str(udir), **(env_extra or {})), capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr, time.monotonic() - t0
    def unpacked(ten, tag):
        out = t / ('unpacked-' + tag)
        r = subprocess.run([a.packdir, 'unpack-tree', str(ten), str(out)], capture_output=True, text=True)
        check(r.returncode == 0, 'unpack-tree: ' + r.stdout + r.stderr)
        return tree(out)

    rc1, out1, s1 = run(t / 'ten1', t / 'u1', 1)
    rc4, out4, s4 = run(t / 'ten4', t / 'u4', 4)
    check(rc1 == 0 and rc4 == 0, 'both runs succeed (%d, %d):\n%s\n%s' % (rc1, rc4, out1[-800:], out4[-800:]))
    check(len(list((t / 'ten4').glob('*/*.sqlar'))) == 40, 'forty containers with four workers')
    check(unpacked(t / 'ten1', '1') == leaves and unpacked(t / 'ten4', '4') == leaves, 'one and four workers both give the Quasar tree')
    check(subprocess.run([a.packdir, 'verify', *map(str, sorted((t / 'ten4').glob('*/*.sqlar')))], capture_output=True).returncode == 0,
          'four-worker containers verify')
    rc, out, _ = run(t / 'ten4', t / 'u4', 4)
    check(rc == 0 and 'Packing' not in out, 'a quiet rerun after the parallel run:\n' + out)
    print('timing: 1 worker %.2f s, 4 workers %.2f s (synthetic, internal disk)' % (s1, s4))

    # A worker crash: its item fails, the other workers' containers stay, the next run converges.
    rc, out, _ = run(t / 'tenc', t / 'uc', 4, {'UNISON_PACKDIR_CRASH_AFTER': '3'})
    check(rc == 2 and 'its worker stopped' in out, 'a crashed worker fails its item (rc %d):\n%s' % (rc, out[-1500:]))
    rc, out, _ = run(t / 'tenc', t / 'uc', 4)
    check(rc == 0, 'the next run completes (rc %d):\n%s' % (rc, out[-1500:]))
    check(unpacked(t / 'tenc', 'c') == leaves, 'converged after the worker crash')

print('PASS%d packdir parallel controls' % checks)
