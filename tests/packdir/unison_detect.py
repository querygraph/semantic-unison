#!/usr/bin/env python3
"""Milestone 2 controls for packed roots in unison: update detection from the
containers. Synthetic roots only: Quasar is a plain tree <H>/<HHHH>/<files>,
Ten is the same tree packed by unison-packdir pack-tree (one .sqlar per leaf),
with a plain directory of kept originals beside one container."""
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

def digest_tree(root):
    return {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() + str(f.stat().st_mtime_ns)
            for f in sorted(root.rglob('*')) if f.is_file()}

rng = random.Random(7)
with tempfile.TemporaryDirectory(prefix='unison-packdir-detect-') as td:
    t = pathlib.Path(td).resolve()
    quasar, ten, udir = t / 'quasar', t / 'ten', t / 'unisondir'
    udir.mkdir()
    for leaf in ('0/0000', '0/0001', 'a/0a00'):
        d = quasar / leaf; d.mkdir(parents=True)
        for i in range(5):
            f = d / ('%08x_%d' % (rng.getrandbits(32), rng.choice([320, 1024])))
            f.write_bytes(rng.randbytes(rng.randint(100, 50000)))
            ns = 1_700_000_000_000_000_000 + rng.randint(0, 10**15); os.utime(f, ns=(ns, ns))
    (quasar / 'README').write_text('a plain file above the packed depth\n')
    # Ten: kept originals beside one leaf (an identical copy and a Ten-only file), then the packed tree.
    keep = ten / '0/0001'; keep.mkdir(parents=True)
    same = sorted((quasar / '0/0001').iterdir())[0]
    shutil.copy2(same, keep / same.name)
    (keep / 'old.lrfprev').write_bytes(b'a kept original that Quasar never had')
    subprocess.run([a.packdir, 'pack-tree', str(quasar), str(ten)], check=True, capture_output=True)
    shutil.copy2(quasar / 'README', ten / 'README')
    for f in ('.packdir-state', '.packdir-pending', '.packdir-writer.lock'):
        (ten / f).unlink(missing_ok=True)   # the prototype's own files, not Unison's
    ten_before = digest_tree(ten)

    env = dict(os.environ, UNISON=str(udir))
    flow = ['-force', str(quasar), '-nodeletion', str(ten), '-perms', '0', '-times']
    def unison(*args, packed=True):
        extra = ['-packdepth', '2', '-packroot', str(ten)] if packed else []
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', *flow, *extra, *args],
                           env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    # Identical trees: Unison sees each container as the leaf it holds.
    rc, out = unison()
    skipped = [l for l in out.splitlines() if l.strip().startswith(('skipped:', 'failed:'))]
    check(skipped == ['  skipped: 0/0001/old.lrfprev (would delete a file with nodeletion or nodeletionpartial set)'],
          'identical trees: only the kept original is skipped, nothing fails (rc %d):\n%s' % (rc, out))
    check('Error' not in out and 'propagation is not built yet' not in out, 'no errors on an identical run:\n' + out)
    check('old.lrfprev' in out and 'Deleting' not in out, 'the Ten-only kept original is not deleted:\n' + out)
    check(digest_tree(ten) == ten_before, 'Ten untouched by an identical run')

    # A changed and an added file on Quasar: detected, and held back from Ten by noupdate/nocreation.
    changed = sorted((quasar / 'a/0a00').iterdir())[0]
    changed.write_bytes(b'new bytes'); os.utime(changed, ns=(1_800_000_000_000_000_000,) * 2)
    (quasar / '0/0000/new_2048').write_bytes(b'a new level')
    hold = ['-noupdate', str(ten), '-nocreation', str(ten)]
    rc, out = unison(*hold)
    check('a/0a00/' + changed.name in out and '0/0000/new_2048' in out, 'both changes detected:\n' + out)
    held = sorted(l.strip().split(' (')[0] for l in out.splitlines() if l.strip().startswith('skipped:') and 'old.lrfprev' not in l)
    check(held == ['skipped: 0/0000/new_2048', 'skipped: a/0a00/' + changed.name] and 'Error' not in out,
          'exactly the two changes detected and held back, no digest errors:\n' + out)
    check(digest_tree(ten) == ten_before, 'Ten untouched while writes are held back')

    # An unchanged container is not opened: unreadable, the run still sees it as before.
    locked = ten / '0/0001.sqlar'; locked.chmod(0)
    rc, out = unison(*hold)
    held = sorted(l.strip().split(' (')[0] for l in out.splitlines() if l.strip().startswith('skipped:') and 'old.lrfprev' not in l)
    check('Permission denied' not in out and 'Error' not in out and
          held == ['skipped: 0/0000/new_2048', 'skipped: a/0a00/' + changed.name],
          'unchanged container left unopened, the same two pending changes:\n' + out)
    locked.chmod(0o644)

    # Archive identity: a run without packdepth uses other archives for both roots.
    before = {f.name for f in udir.iterdir() if f.name.startswith('ar')}
    rc, out = unison('-noupdate', str(ten), '-nocreation', str(ten), packed=False)
    after = {f.name for f in udir.iterdir() if f.name.startswith('ar')}
    check(len(before) == 2 and len(after - before) == 2, 'separate archives without packdepth: %r -> %r' % (before, after))
    check(digest_tree(ten) == ten_before, 'Ten untouched by the plain run')

print('PASS%d packdir detection controls' % checks)
