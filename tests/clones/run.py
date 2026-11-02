#!/usr/bin/env python3
"""Clone preservation (clones preference, clone-pairs-v0) on an owned APFS image.

Builds synthetic source trees in a scratch directory on the system APFS volume,
syncs them with the given linktext binaries onto a private APFS disk image and
checks APFS clone identities on the target with a small getattrlist probe.
"""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import tempfile

PROBE = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/attr.h>
#include <unistd.h>
int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    struct attrlist req; memset(&req, 0, sizeof req);
    struct { uint32_t length; attribute_set_t returned; uint64_t id; uint32_t refcnt; }
      __attribute__((packed, aligned(4))) buf;
    memset(&buf, 0, sizeof buf);
    req.bitmapcount = ATTR_BIT_MAP_COUNT;
    req.commonattr = ATTR_CMN_RETURNED_ATTRS;
    req.forkattr = ATTR_CMNEXT_CLONEID | ATTR_CMNEXT_CLONE_REFCNT;
    if (getattrlist(argv[i], &req, &buf, sizeof buf, FSOPT_NOFOLLOW | FSOPT_ATTR_CMN_EXTENDED) != 0
        || (buf.returned.forkattr & (ATTR_CMNEXT_CLONEID | ATTR_CMNEXT_CLONE_REFCNT))
           != (ATTR_CMNEXT_CLONEID | ATTR_CMNEXT_CLONE_REFCNT)) {
      printf("- -\n"); continue; }
    printf("%llu %u\n", (unsigned long long)buf.id, buf.refcnt);
  }
  return 0;
}
'''

DEFAULT_WORK = None  # a fresh temporary directory
ROOT = Path(__file__).resolve().parents[2]

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', action='append', metavar='LABEL=PATH',
               help='linktext binary; default: both build-semdiff switches')
p.add_argument('--work', type=Path, default=DEFAULT_WORK, help='scratch directory (default: a new temporary one)')
p.add_argument('--baseline', type=Path,
               help='linktext built without clone-pairs-v0, used as an older server peer')
a = p.parse_args()
if platform.system() != 'Darwin':
    sys.exit('clone preservation tests need macOS and APFS')
binaries = {}
for item in a.binary or ['default=build-semdiff/.dune-default/default/src/linktext.exe',
                         'ox=build-semdiff/.dune-5.2.0+ox/default/src/linktext.exe']:
    label, _, path = item.partition('=')
    binaries[label] = (ROOT/path).resolve() if not os.path.isabs(path) else Path(path)

if a.work is None:
    work = Path(tempfile.mkdtemp(prefix='unison-clones-')).resolve()
else:
    work = a.work
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
probe = work/'cloneprobe'
(work/'cloneprobe.c').write_text(PROBE)
subprocess.run(['cc', '-O', '-o', probe, work/'cloneprobe.c'], check=True)
image, mount = work/'clones.dmg', work/'mnt'
mount.mkdir()
failures = []


def identity(*paths):
    out = subprocess.run([probe, *map(str, paths)], check=True, capture_output=True, text=True).stdout
    result = []
    for line in out.splitlines():
        cid, ref = line.split()
        result.append(None if cid == '-' else (int(cid), int(ref)))
    return result


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else ': ' + str(detail)), flush=True)
    if not cond:
        failures.append(name)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cp_clone(src, dst):
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['cp', '-c', str(src), str(dst)], check=True)


def write(path, seed, size=300000):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(random.Random(seed).randbytes(size))


def sync(binary, src, dst, state, name, extra, server=None):
    env = dict(os.environ, HOME=str(state), UNISON=str(state/'unison'))
    (state/'unison').mkdir(parents=True, exist_ok=True)
    if server is not None:
        # A pipe to a local server process through a stand-in for ssh; no network.
        fake = work/'fakessh'
        fake.write_text('#!/bin/sh\nwhile [ $# -gt 0 ] && [ "$1" != "-e" ]; do shift; done\n'
                        'shift 2\nexec "$@"\n')
        fake.chmod(0o755)
        dst = 'ssh://localhost/%s' % dst
        extra = extra + ['-sshcmd', str(fake), '-servercmd', str(server)]
    argv = [str(binary), str(src), str(dst), '-batch', '-times', '-fastcheck', 'false',
            '-debug', 'copy'] + extra
    child = subprocess.run(argv, env=env, capture_output=True, timeout=300)
    log = work/(name+'.log')
    log.write_bytes(child.stdout + b'\n' + child.stderr)
    if child.returncode != 0:
        check(name + ' exit status', False, '%d, see %s' % (child.returncode, log))
    return log.read_text(errors='replace')


def same_tree(name, src, dst):
    for path in sorted(src.rglob('*')):
        if not path.is_file():
            continue
        other = dst/path.relative_to(src)
        ok = other.is_file() and sha(path) == sha(other) and \
            int(path.stat().st_mtime) == int(other.stat().st_mtime)
        check('%s content+mtime %s' % (name, path.relative_to(src)), ok)


def grouped(name, paths, expect_clone):
    ids = identity(*paths)
    if expect_clone:
        ok = all(i is not None for i in ids) and len({i[0] for i in ids}) == 1 \
            and all(i[1] >= len(paths) for i in ids)
    else:
        ok = all(i is not None for i in ids) and len({i[0] for i in ids}) == len(ids) \
            and all(i[1] == 1 for i in ids)
    check(name, ok, ids)


def run_matrix(label, binary):
    base = mount/label
    src, state = work/(label+'-src'), work/(label+'-state')
    src.mkdir()
    base.mkdir(parents=True)
    # Run 1: groups of two and three across directories, an independent copy,
    # and a clone changed after cloning.
    write(src/'g2/a.bin', 1); cp_clone(src/'g2/a.bin', src/'d2/b.bin')
    write(src/'g3/x.bin', 2); cp_clone(src/'g3/x.bin', src/'g3sub/deep/y.bin')
    cp_clone(src/'g3sub/deep/y.bin', src/'other/z.bin')
    write(src/'indep/p.bin', 3); Path(src/'indep2').mkdir()
    shutil.copyfile(src/'indep/p.bin', src/'indep2/q.bin')
    write(src/'mod/m.bin', 4); cp_clone(src/'mod/m.bin', src/'mod/n.bin')
    with open(src/'mod/n.bin', 'r+b') as stream:
        stream.seek(1000); stream.write(b'changed after cloning')
    write(src/'single/s.bin', 5)
    grouped(label+' source sanity: g3 is a 3-group', [src/'g3/x.bin', src/'g3sub/deep/y.bin', src/'other/z.bin'], True)
    grouped(label+' source sanity: p/q independent', [src/'indep/p.bin', src/'indep2/q.bin'], False)
    grouped(label+' source sanity: m/n split', [src/'mod/m.bin', src/'mod/n.bin'], False)
    dst = base/'on'
    log = sync(binary, src, dst, state/'on', label+'-run1', ['-clones'])
    grouped(label+' run1 two-member group in one run', [dst/'g2/a.bin', dst/'d2/b.bin'], True)
    grouped(label+' run1 three-member group in one run',
            [dst/'g3/x.bin', dst/'g3sub/deep/y.bin', dst/'other/z.bin'], True)
    grouped(label+' run1 independent identical copy stays independent',
            [dst/'indep/p.bin', dst/'indep2/q.bin'], False)
    grouped(label+' run1 changed clone transfers normally', [dst/'mod/m.bin', dst/'mod/n.bin'], False)
    check(label+' run1 log shows clone shortcuts', log.count('Shortcut: cloned') == 3, log.count('Shortcut: cloned'))
    same_tree(label+' run1', src, dst)
    # Run 2: a new clone of a file synced in run 1, a new independent copy,
    # and a clone of an earlier clone changed after cloning.
    cp_clone(src/'g2/a.bin', src/'later/a2.bin')
    shutil.copyfile(src/'indep/p.bin', src/'later/p2.bin')
    cp_clone(src/'single/s.bin', src/'later/s2.bin')
    with open(src/'later/s2.bin', 'r+b') as stream:
        stream.write(b'diverged')
    # A new group created in run 2 across two new top-level directories and an
    # existing one, so members are separate top-level copies.
    write(src/'r2a/k.bin', 6); cp_clone(src/'r2a/k.bin', src/'r2b/k2.bin')
    cp_clone(src/'r2a/k.bin', src/'g2/k3.bin')
    log = sync(binary, src, dst, state/'on', label+'-run2', ['-clones'])
    grouped(label+' run2 new group across top-level items',
            [dst/'r2a/k.bin', dst/'r2b/k2.bin', dst/'g2/k3.bin'], True)
    ids = identity(dst/'g2/a.bin', dst/'d2/b.bin', dst/'later/a2.bin')
    check(label+' run2 new clone of an already synced file',
          None not in ids and len({i[0] for i in ids}) == 1 and all(i[1] == 3 for i in ids), ids)
    grouped(label+' run2 independent copy of synced file stays independent',
            [dst/'indep/p.bin', dst/'later/p2.bin'], False)
    grouped(label+' run2 diverged clone transfers normally', [dst/'single/s.bin', dst/'later/s2.bin'], False)
    same_tree(label+' run2', src, dst)
    # clones off (the default): nothing is cloned, today's behaviour.
    dst = base/'off'
    log = sync(binary, src, dst, state/'off', label+'-off', [])
    ids = identity(*[p for p in sorted(dst.rglob('*')) if p.is_file()])
    check(label+' clones off: no clone on target', all(i is not None and i[1] == 1 for i in ids), ids)
    check(label+' clones off: no clone shortcut', 'Shortcut: cloned' not in log)
    same_tree(label+' off', src, dst)
    # Remote receiver (server process over a pipe), same binary on both ends.
    dst = base/'remote'
    dst.mkdir()
    log = sync(binary, src, dst, state/'remote', label+'-remote', ['-clones'], server=binary)
    grouped(label+' remote three-member group',
            [dst/'g3/x.bin', dst/'g3sub/deep/y.bin', dst/'other/z.bin'], True)
    ids = identity(dst/'g2/a.bin', dst/'d2/b.bin', dst/'later/a2.bin')
    check(label+' remote g2 group', None not in ids and len({i[0] for i in ids}) == 1, ids)
    grouped(label+' remote independent copies stay independent',
            [dst/'indep/p.bin', dst/'indep2/q.bin', dst/'later/p2.bin'], False)
    grouped(label+' remote changed clone transfers normally', [dst/'mod/m.bin', dst/'mod/n.bin'], False)
    check(label+' remote used clonePairs', '[server: copy] clonePairs:' in log)
    same_tree(label+' remote', src, dst)
    if a.baseline:
        # An older peer: -clones must change nothing; compare with a plain run.
        results = {}
        for mode, extra in (('clones', ['-clones']), ('plain', [])):
            dst = base/('baseline-'+mode)
            dst.mkdir()
            log = sync(binary, src, dst, state/('baseline-'+mode), label+'-baseline-'+mode,
                       extra, server=a.baseline)
            check(label+' baseline peer %s: no clonePairs request' % mode, 'clonePairs' not in log)
            same_tree(label+' baseline '+mode, src, dst)
            files = [p.relative_to(dst) for p in sorted(dst.rglob('*')) if p.is_file()]
            ids = identity(*[dst/f for f in files])
            # Clone structure as a partition of names, independent of id values.
            groups = {}
            for f, i in zip(files, ids):
                groups.setdefault(i and i[0], []).append(str(f))
            results[mode] = sorted(groups.values())
        check(label+' baseline peer: -clones identical to plain sync',
              results['clones'] == results['plain'], results)
    # Explicit -clones=false behaves like the default.
    dst = base/'false'
    log = sync(binary, src, dst, state/'false', label+'-false', ['-clones=false'])
    ids = identity(*[p for p in sorted(dst.rglob('*')) if p.is_file()])
    check(label+' clones=false: no clone on target', all(i is not None and i[1] == 1 for i in ids), ids)


attached = False
try:
    subprocess.run(['timeout', '60', 'hdiutil', 'create', '-size', '200m', '-fs', 'APFS',
                    '-volname', 'UnisonClones', str(image)], check=True, capture_output=True)
    attached = True
    subprocess.run(['timeout', '60', 'hdiutil', 'attach', '-nobrowse', '-noautoopen',
                    '-mountpoint', str(mount), str(image)], check=True, capture_output=True)
    assert mount.stat().st_dev != work.stat().st_dev, 'image is not a separate volume'
    for label, binary in binaries.items():
        print('== %s: %s' % (label, binary), flush=True)
        run_matrix(label, binary)
finally:
    if attached:
        r = subprocess.run(['timeout', '60', 'hdiutil', 'detach', str(mount)], capture_output=True)
        if r.returncode != 0:
            subprocess.run(['timeout', '60', 'hdiutil', 'detach', '-force', str(mount)], capture_output=True)
print('FAILED: %d checks' % len(failures) if failures else 'ALL PASSED')
sys.exit(1 if failures else 0)
