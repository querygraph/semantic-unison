"""One fixed cached-SHA experiment; metadata checks confer no IO admission."""
import ast
import hashlib
import json
import math
import os
import re
from pathlib import Path
import stat
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import require, unique_object

TARGET = 'cached-sha-benchmark'
PYTHON = '/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA = '56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'
COMPILERS = {'stock':'/Users/alexy/.opam/default/bin/ocamlopt.opt',
             'ox':'/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt'}
LIMITS = dict(cpu_credits=8, token_indexes=list(range(8)), io_mode='EX_GLOBAL',
              workers=[1, 2, 4, 6], owner_credits=2, file_mib=32, jobs=6,
              warmups=1, repetitions=5, observation_seconds=300, sample_seconds=30,
              declared_io_bytes=16 * 1024**3, physical_io_budget_enforced=False)


def stamp(s):
    return tuple(getattr(s, k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_size',
                                        'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_uid'))


def read_bytes(path, limit):
    """Regular owned metadata/artifact only; one close, uncertainty retained."""
    path = Path(path)
    require(path.is_absolute(), 'absolute artifact path required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and 0 < before.st_size <= limit,
                'bounded owned regular artifact required')
        raw = bytearray()
        while len(raw) < before.st_size:
            block = os.read(fd, min(65536, before.st_size-len(raw)))
            require(bool(block), 'short artifact read')
            raw.extend(block)
        require(not os.read(fd, 1) and stamp(before) == stamp(os.fstat(fd))
                == stamp(os.lstat(path)), 'artifact epoch changed')
        return bytes(raw)
    finally:
        close_descriptors([fd])


def document(path, digest=None):
    raw = read_bytes(path, 1048576)
    require(digest is None or hashlib.sha256(raw).hexdigest() == digest,
            'metadata SHA differs')
    return json.loads(raw, object_pairs_hook=unique_object)


def benchmark_sources():
    tree = ast.parse(read_bytes(ROOT/'bench/semantic/run.py',16*1048576).decode('utf-8'))
    values = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
                  and t.id == 'SOURCES' for t in node.targets)]
    require(len(values) == 1 and all(type(p) is str for p in values[0]),
            'literal benchmark source inventory required')
    return values[0]


def sources():
    names = benchmark_sources() + ['bench/semantic/run.py', 'tests/manual.py',
        'tests/shared_dispatch.py', 'tests/shared_cpu_pool.py', 'tests/shared_io_pool.py',
        'tests/shared_process_owner.py', 'bench/sync/ownership.py',
        'tests/private_camera_receiving/close.py', 'tests/sdk_host_matrix/shared_binding.py']
    names += [str(p.relative_to(ROOT)) for p in (ROOT/'tests/cached_benchmark').glob('*.py')]
    return sorted(set(names))


def artifact_paths(plan):
    paths = {Path(PYTHON)}
    for build in plan['builds']:
        paths.update((Path(build['compiler']), Path(build['receipt'])))
        for name in benchmark_sources():
            if not name.startswith('src/') or name.endswith('.h'):
                continue
            actual = Path(build['src']) / name.removeprefix('src/')
            extensions = ('.cmi', '.cmx', '.o') if name.endswith('.ml') else (
                ('.cmi',) if name.endswith('.mli') else ('.o',))
            paths.update(actual.with_suffix(ext) for ext in extensions)
    return sorted(str(p) for p in paths)


def validate(plan):
    require(plan['schema'] == 'unison-cached-benchmark-plan/1'
            and json.dumps(plan['limits'], sort_keys=True) == json.dumps(LIMITS, sort_keys=True),
            'exact finite benchmark contract required')
    workspace = Path(plan['workspace'])
    require(str(workspace).startswith('/private/tmp/unison-cached-sha-')
            and workspace.parent == Path('/private/tmp') and workspace.resolve() == workspace,
            'private exact workspace required')
    require([b['label'] for b in plan['builds']] == ['stock', 'ox'], 'exact compiler pair required')
    for build in plan['builds']:
        src=Path(build['src']);receipt=Path(build['receipt'])
        require(build['compiler']==COMPILERS[build['label']]
                and src.name=='src' and src.parent.name.startswith('unison-build-')
                and (src.is_relative_to('/private/tmp') or src.is_relative_to('/private/var/folders'))
                and receipt.name=='RESULT.json' and receipt.is_relative_to('/private/tmp')
                and receipt.parent.name.startswith('unison-'), 'qualified tool/build namespace required')
        for key in ('src', 'compiler', 'receipt'):
            p = Path(build[key])
            require(p.is_absolute() and '..' not in p.parts and p.resolve()==p,
                    'canonical absolute build paths required')
    require(set(plan['source_sha256']) == set(sources()), 'exact execution source set required')
    require(sorted(plan['artifact_sha256']) == artifact_paths(plan), 'exact artifact set required')
    require(plan['artifact_sha256'][PYTHON] == PYTHON_SHA, 'qualified interpreter required')
    require(all(type(h) is str and re.fullmatch('[0-9a-f]{64}',h)
                for h in [*plan['source_sha256'].values(),*plan['artifact_sha256'].values()]),
                'typed exact SHA256 pins required')
    return plan


def checked_plan(path, digest):
    plan = validate(document(path, digest))
    for name, expected in plan['source_sha256'].items():
        require(hashlib.sha256(read_bytes(ROOT/name, 16*1048576)).hexdigest() == expected,
                'execution source changed: '+name)
    for name, expected in plan['artifact_sha256'].items():
        require(hashlib.sha256(read_bytes(name, 256*1048576)).hexdigest() == expected,
                'build artifact changed: '+name)
    for build in plan['builds']:
        receipt = document(build['receipt'])
        require(receipt['build_exit'] == receipt['selftest_exit'] == 0
                and (Path(receipt['workspace'])/'src').resolve() == Path(build['src'])
                and Path(receipt['compiler']).resolve() == Path(build['compiler']),
                'actual complete build binding differs')
        require(all(receipt['source_sha256'].get(name) == plan['source_sha256'][name]
                    for name in benchmark_sources() if name.startswith('src/')),
                'benchmark sources differ from complete build inventory')
    return plan


def worker_argv(plan, plan_path, digest):
    validate(plan)
    return [PYTHON, str(ROOT/'tests/cached_benchmark/entry.py'), '--worker', '--plan',
            str(plan_path), '--plan-sha256', digest, '--workspace', plan['workspace']]


def benchmark_argv(plan, fds):
    validate(plan)
    require(len(fds) == len(set(fds)) == 9 and all(type(fd) is int and fd >= 3 for fd in fds),
            'exact inherited resource set required')
    argv = [str(ROOT/'bench/semantic/run.py'), '--workers', '1,2,4,6', '--jobs', '6',
            '--file-mib', '32', '--repetitions', '5', '--warmups', '1', '--sample-timeout', '30',
            '--keep-work', '--work-parent', plan['workspace'], '--output',
            str(Path(plan['workspace'])/'RESULT.json'), '--inherited-resource-fds',
            ','.join(map(str, fds))]
    for build in plan['builds']:
        argv += ['--compiler', build['label']+'='+build['compiler'],
                 '--build', build['label']+'='+build['src']]
    return argv


def schedule():
    configs = [(label, n) for n in LIMITS['workers'] for label in ('stock', 'ox')]
    return [(phase, r+1, label, n)
            for phase, rounds in [('warmup', 1), ('measured', 5)]
            for r in range(rounds) for label, n in (configs if r % 2 == 0 else configs[::-1])]


def audit(result, plan, inherited):
    """Raw saved numeric observations only; no hard limits or speedup verdict."""
    validate(plan)
    require(type(result['complete']) is bool, 'typed completion required')
    require(result['source_sha256'] == {k: plan['source_sha256'][k] for k in benchmark_sources()}
            and result['runner_sha256'] == plan['source_sha256']['bench/semantic/run.py'],
            'measurement source binding differs')
    require(result['inherited_resource_fds'] == inherited, 'resource observation differs')
    require(result['parameters'] == dict(file_mib=32, jobs=6, workers=[1, 2, 4, 6],
            warmups_per_configuration=1, measured_repetitions=5), 'sample parameters differ')
    rows = result['samples']
    require(len(rows) <= 48 and (not result['complete'] or len(rows) == 48), 'sample count differs')
    for row, identity in zip(rows, schedule()):
        require((row['phase'], row['repetition'], row['compiler'], row['workers']) == identity,
                'sample order differs')
        raw = json.loads(row['raw_stdout'], object_pairs_hook=unique_object)
        require(all(row[k] == value for k, value in raw.items()), 'raw sample changed')
        for key in ('wall_seconds', 'process_cpu_seconds', 'process_lifetime_peak_rss_bytes',
                    'observed_fd_count_peak', 'baseline_fd_count', 'final_fd_count'):
            require(type(raw[key]) in (int, float) and math.isfinite(raw[key]) and raw[key] >= 0,
                    'finite nonnegative numeric observation required')
        require(raw['wall_seconds'] > 0 and raw['correct_digests'] == 6
                and raw['final_cpu_permits'] == 0 and 1 <= raw['peak_active_workers'] <= identity[3]
                and raw['baseline_fd_count'] == raw['final_fd_count']
                and raw['observed_fd_count_peak'] >= raw['baseline_fd_count'],
                'worker/resource correctness invariant failed')
        require(all(type(raw[k]) is int for k in ('correct_digests', 'final_cpu_permits',
                    'peak_active_workers', 'baseline_fd_count', 'final_fd_count',
                    'observed_fd_count_peak')), 'typed resource counters required')
        require(type(raw['primary_logical_read_bytes']) is int
                and raw['primary_logical_read_bytes']==192*1048576
                and type(raw['primary_read_observations']) is int and raw['primary_read_observations']==6
                and type(raw['primary_read_chunks']) is int and raw['primary_read_chunks']>=6,
                'primary logical read accounting differs')
        require(row['throughput_mib_per_second'] == 192/raw['wall_seconds']
                and row['effective_cpu_cores'] == raw['process_cpu_seconds']/raw['wall_seconds'],
                'derived numeric observation differs')
    summary = []
    for label, workers in [(label, n) for n in LIMITS['workers'] for label in ('stock', 'ox')]:
        selected = [r for r in rows if r['phase'] == 'measured'
                    and r['compiler'] == label and r['workers'] == workers]
        if selected:
            summary.append(dict(compiler=label, workers=workers, samples=len(selected),
                median_mib_per_second=statistics.median(r['throughput_mib_per_second'] for r in selected)))
    return dict(functional_status='PASSED' if result['complete'] else 'FAILED_PREFIX',
                completed_native_batches=len(rows), parent_recomputed_summary=summary,
                quiet_timing=False, whole_process_hard_caps=False, resource_release_authorized=False)
