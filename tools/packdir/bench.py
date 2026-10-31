#!/usr/bin/env python3
"""Benchmark harness for packed directories (docs/packdir-design.md).

Copies one leaf set (<H>/<HHHH>/<files>) to a target disk by each method and
records wall time and the target disk's bytes written and I/O operations
(iostat), as JSON lines:

  plain      Unison, file per file (clone off), one way and additive like the mirror profile
  sqlar      unison-packdir pack-tree, DELETE journal
  sqlar-wal  unison-packdir pack-tree --wal
  cp         cp -R, then sync (first run only)
  tar        tar | tar, then sync (first run only)
  bundle     Unison into an HFS+ sparse bundle on the target

  bench.py first SRC OUT --unison U --packdir P [--methods ...]
  bench.py incremental SRC OUT --unison U --packdir P [--methods ...]
  bench.py sample DIR [--gib G]      small synthetic set for a dry run

OUT must be new for 'first', must contain 'packdir-bench' in its path, and is
the only place written (Unison's archives go in OUT's sibling .unison-home on
the same run's work directory). Nothing is ever deleted."""
import argparse, json, os, pathlib, random, re, subprocess, sys, time

FIRST = ['plain', 'sqlar', 'sqlar-wal', 'cp', 'tar', 'bundle']
INCREMENTAL = ['plain', 'sqlar', 'sqlar-wal', 'bundle']


def disk_of(path):
    dev = subprocess.run(['df', path], capture_output=True, text=True, check=True).stdout.splitlines()[1].split()[0]
    info = subprocess.run(['diskutil', 'info', dev], capture_output=True, text=True).stdout
    m = re.search(r'Part of Whole:\s+(\S+)', info)
    whole = m.group(1) if m else os.path.basename(dev)
    # An APFS volume's whole disk is a synthesized container: iostat counts its physical store.
    store = re.search(r'APFS Physical Store:\s+(disk\d+)', subprocess.run(['diskutil', 'info', whole], capture_output=True, text=True).stdout)
    return store.group(1) if store else whole


def io_totals(disk):
    """(transfers, MiB) since boot for one disk, from iostat -I."""
    lines = subprocess.run(['iostat', '-Id', disk], capture_output=True, text=True, check=True).stdout.splitlines()
    kbt, xfrs, mb = lines[-1].split()[:3]
    return float(xfrs), float(mb)


def leaf_stats(src):
    files = [f for f in pathlib.Path(src).glob('*/*/*') if f.is_file()]
    return len(files), sum(f.stat().st_size for f in files)


def unison(args, src, dst, home):
    os.makedirs(dst, exist_ok=True)
    env = dict(os.environ, UNISON=str(home))
    # The mirror profile's flow: one way and additive, nothing deleted on the target.
    flow = ['-force', str(src), '-noupdate', str(src), '-nocreation', str(src), '-nodeletion', str(src),
            '-nodeletion', str(dst)]
    with (home / 'unison.out').open('a') as log:
        r = subprocess.run([args.unison, str(src), str(dst), '-batch', '-times', '-perms', '0', '-clone', 'off',
                        '-confirmbigdel=false', *flow, '-logfile', str(home / 'unison.log')], env=env,
                       stdout=log, stderr=log)
    # Exit 1 means items were skipped: the deletions that nodeletion keeps.
    if r.returncode not in (0, 1):
        sys.exit('unison exited %d; see %s' % (r.returncode, home / 'unison.out'))


def method(args, name, phase, src, out, home):
    dst = out / name
    if name == 'plain':
        unison(args, src, dst, home)
    elif name in ('sqlar', 'sqlar-wal'):
        extra = ['--wal'] if name == 'sqlar-wal' else []
        r = subprocess.run([args.packdir, 'pack-tree', str(src), str(dst), *extra], capture_output=True, text=True, check=True)
        return json.loads(r.stdout.splitlines()[-1])
    elif name == 'cp':
        subprocess.run(['cp', '-Rp', str(src), str(dst)], check=True)
        subprocess.run(['sync'], check=True)
    elif name == 'tar':
        dst.mkdir()
        subprocess.run('tar -cf - -C %s . | tar -xpf - -C %s' % (sh(src), sh(dst)), shell=True, check=True)
        subprocess.run(['sync'], check=True)
    elif name == 'bundle':
        image, mount = out / 'bundle.sparsebundle', out / 'bundle-mount'
        if phase == 'first':
            subprocess.run(['hdiutil', 'create', '-quiet', '-type', 'SPARSEBUNDLE', '-fs', 'HFS+J', '-volname', 'packdir-bench',
                            '-size', '%dg' % args.bundle_gib, str(image)], check=True)
        mount.mkdir(exist_ok=True)
        subprocess.run(['hdiutil', 'attach', '-quiet', '-nobrowse', '-mountpoint', str(mount), str(image)], check=True)
        try:
            unison(args, src, mount / 'cache', home)
        finally:
            subprocess.run(['hdiutil', 'detach', '-quiet', str(mount)], check=True)
    return None


def sh(p):
    return "'" + str(p).replace("'", "'\\''") + "'"


def run(args, phase):
    src, out = pathlib.Path(args.src).resolve(), pathlib.Path(args.out).absolute()
    if 'packdir-bench' not in str(out):
        sys.exit('OUT must be inside a folder named packdir-bench')
    if phase == 'first':
        if out.exists():
            sys.exit('OUT must not exist for a first run: ' + str(out))
        out.mkdir(parents=True)
    elif not out.is_dir():
        sys.exit('no first run in ' + str(out))
    work = pathlib.Path(args.work).resolve() if args.work else out.parent / (out.name + '.work')
    work.mkdir(exist_ok=True)
    disk = disk_of(str(out))
    files, nbytes = leaf_stats(src)
    results = out / 'RESULTS.jsonl'
    # Read the source once, untimed, so every method reads it from memory alike
    # (the set fits in RAM) and the comparison is the target disk's cost.
    for f in pathlib.Path(src).rglob('*'):
        if f.is_file():
            with f.open('rb') as h:
                while h.read(1 << 20):
                    pass
    for name in args.methods or (FIRST if phase == 'first' else INCREMENTAL):
        home = work / ('unison-home-' + name)
        home.mkdir(exist_ok=True)
        x0, m0 = io_totals(disk)
        t0 = time.monotonic()
        detail = method(args, name, phase, src, out, home)
        subprocess.run(['sync'], check=True)  # what is still in memory counts too
        dt = time.monotonic() - t0
        x1, m1 = io_totals(disk)
        row = dict(phase=phase, method=name, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), disk=disk,
                   source_files=files, source_bytes=nbytes, seconds=round(dt, 3),
                   disk_mib=round(m1 - m0, 1), disk_ios=int(x1 - x0), iops=round((x1 - x0) / dt, 1) if dt else None,
                   source_mib_per_s=round(nbytes / 1048576 / dt, 1) if dt else None, detail=detail)
        print(json.dumps(row), flush=True)
        with results.open('a') as f:
            f.write(json.dumps(row) + '\n')


def sample(args):
    """A small leaf set in the cache's layout, random (incompressible) bytes."""
    root = pathlib.Path(args.dir)
    if root.exists():
        sys.exit(str(root) + ' exists')
    rng, total, target = random.Random(1), 0, args.gib * 1024 ** 3
    n = 0
    while total < target:
        h = '%x' % (n % 16); leaf = root / h / ('%s%03x' % (h, n // 16)); leaf.mkdir(parents=True)
        for _ in range(rng.randint(31, 89)):
            size = min(int(rng.lognormvariate(13.4, 1.0)), 8 << 20)
            (leaf / ('%032x-%016x_%d' % (rng.getrandbits(128), rng.getrandbits(64), rng.choice([320, 1024, 2048, 2880])))).write_bytes(os.urandom(size))
            total += size
        n += 1
    print(json.dumps(dict(leaves=n, bytes=total)))


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest='cmd', required=True)
for c in ('first', 'incremental'):
    q = sub.add_parser(c); q.add_argument('src'); q.add_argument('out')
    q.add_argument('--unison', required=True); q.add_argument('--packdir', required=True)
    q.add_argument('--methods', nargs='*'); q.add_argument('--work'); q.add_argument('--bundle-gib', type=int, default=200)
q = sub.add_parser('sample'); q.add_argument('dir'); q.add_argument('--gib', type=float, default=1)
a = p.parse_args()
if a.cmd == 'sample':
    sample(a)
else:
    run(a, a.cmd)
