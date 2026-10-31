#!/usr/bin/env python3
"""Milestone 1 controls for packed roots in unison: the preferences and their
refusals, synthetic roots in a private temporary directory."""
import argparse, os, pathlib, subprocess, sys, tempfile

p = argparse.ArgumentParser()
p.add_argument('--unison', required=True)
a = p.parse_args()
checks = 0

def check(ok, message):
    global checks
    if not ok:
        sys.exit('FAIL: ' + message)
    checks += 1

with tempfile.TemporaryDirectory(prefix='unison-packdir-config-') as td:
    t = pathlib.Path(td).resolve()
    quasar, ten = t / 'quasar', t / 'ten'
    (quasar / '0/0000').mkdir(parents=True); ten.mkdir()
    (quasar / '0/0000/level_320').write_bytes(b'x' * 1000)
    env = dict(os.environ, UNISON=str(t / 'unisondir'))
    (t / 'unisondir').mkdir()

    def unison(*args):
        r = subprocess.run([a.unison, str(quasar), str(ten), '-batch', *args], env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def refused(args, text, what):
        rc, out = unison(*args)
        check(rc != 0 and text in out, '%s: exit %d\n%s' % (what, rc, out))
        check(not (ten / '0').exists(), what + ': nothing written to the packed root')

    refused(['-packdepth', '-1'], 'packdepth must be 0 or more', 'negative depth')
    refused(['-packdepth', '2'], 'packdepth needs packroot', 'no packroot')
    refused(['-packdepth', '2', '-packroot', str(t / 'elsewhere')], 'not uniquely identifying one of the current roots', 'packroot not a root')
    refused(['-packdepth', '2', '-packroot', str(ten)], 'packroot only receives', 'no force')
    refused(['-packdepth', '2', '-packroot', str(ten), '-force', str(ten)], 'packroot only receives', 'force toward the plain root')
    refused(['-packdepth', '2', '-packroot', str(ten), '-force', str(quasar)], 'not complete yet', 'integration not complete')
    # Without packdepth nothing changes: a plain one-way copy.
    rc, out = unison('-force', str(quasar))
    check(rc == 0 and (ten / '0/0000/level_320').read_bytes() == b'x' * 1000, 'plain run unchanged:\n' + out)

print('PASS%d packdir config controls' % checks)
