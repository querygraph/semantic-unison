#!/usr/bin/env python3
"""Dispatch existing user-run checks without changing their process ownership."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HELP = '''Run from the repository root: make -f tests/Makefile TARGET
Targets:
  stock-make / stock-dune  build stock CLI and run selftests; STOCK_PREFIX required
  ox-make / ox-dune        build checked OxCaml CLI and run selftests; OX_PREFIX required
  stock-build / ox-build  Make build only; no resulting Unison executable invocation
  inspect-stock / inspect-ox build/retain the read-only inspector only; compiler prefix required
  cache-storage           private cache/quota controls; BUILD_RECEIPT required
  cache-ownership         private cleanup exception controls; BUILD_RECEIPT required
  cache-cli               loopback merge/recovery, fake validators; BUILD_RECEIPT required
  read-workers            reader/worker controls; Make BUILD_RECEIPT required
  read-cli                synthetic telemetry sync; BUILD_RECEIPT required
  read-parser             pure telemetry parser controls
  sync-functional         finite stock/Ox matrix; STOCK_RECEIPT and OX_RECEIPT required
  helper-stock / helper-ox finite synthetic helper suite; STOCK_PREFIX/OX_PREFIX required
  validation-cli          synthetic receiving diagnostics; BUILD_RECEIPT required
  group-parser            pure retained-group diagnostic parser controls
  shared-entrypoints      pure shared command/budget controls
  shared-sync-controls    pure sync budget/receipt controls, no binaries
  interrupted-receipts    four fake-child interruption/receipt controls
  aggregate-lifecycle     four fake-worker aggregate ownership controls
  aggregate-preflight     pure interpreter-capability refusals; no test children
  host-interface          pure plan/receipt controls, no tool invocation
  host-executor           original fake validators and owned-group closure controls
JOBS defaults to 4 (1..18), for build targets only.
SHARED_CPU_CREDITS=8 selects capped shared entry points: build-only defaults
to JOBS=2 and rejects JOBS above two or the ceiling minus two owner credits.
sync-functional uses workers1/2/3 per endpoint plus two owner credits and audits
every separate server closure before releasing tokens. Other targets need a separately
qualified resource scope; this option does not claim a kernel CPU limit or
enforce kernel CPU limits. Shared build/parser execution acquires only authorized
Unison tokens in the existing canonical pool and retains them through settlement.
DRY_RUN=1 prints JSON argv without executing a check or creating a report directory.
OUTPUT_DIR for build/cache/reader/sync targets must be fresh; otherwise a private temporary
directory retains the receipt. Host checks print their own workspace/receipt.
Build snapshots/workspaces are retained separately.
No target executes Adobe, opens Photo/Lightroom, or starts a fuzz/sanitizer campaign.
SDK runtime still requires separate coordination. These checks do not complete the goal.
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_build(path):
    receipt = json.loads(Path(path).read_text())
    require(receipt['complete'] and receipt['build_exit'] == receipt['selftest_exit'] == 0,
            'completed successful build/selftest receipt required')
    require(sha(receipt['binary']) == receipt['binary_sha256']
            and sha(receipt['compiler']) == receipt['compiler_sha256'], 'build artifact changed')
    # A cache-only pin could silently accept stale transfer/worker code.
    pins = receipt['source_sha256']
    require('src/semanticMergeCache.ml' in pins and 'src/semanticWorkers.ml' in pins,
            'production source pins missing')
    for name, digest in pins.items():
        if name.startswith('src/'):
            require(sha(ROOT / name) == digest, 'production source changed: ' + name)
    return receipt


def shared_resource_plan(target, environment):
    """Describe the local source budget; never acquire a token or grant a slot."""
    value = environment.get('SHARED_CPU_CREDITS')
    if value is None:
        return None
    credits = int(value)
    require(1 <= credits <= 8, 'shared Unison lane must be 1..8 credits')
    build = target in ('stock-build', 'ox-build')
    inspector = target in ('inspect-stock', 'inspect-ox')
    endpoints = [3, 3] if target == 'sync-functional' else []
    jobs = int(environment.get('JOBS', str(min(2, credits - 2)))) if build else 1 if inspector else 0
    overhead = 2 if build or inspector or endpoints else 1
    require((not build or 1 <= jobs <= 2) and jobs + sum(endpoints) + overhead <= credits,
            'declared shared work exceeds project grant')
    implemented = target in ('stock-build', 'ox-build', 'read-parser', 'group-parser',
                             'aggregate-preflight', 'host-interface', 'shared-entrypoints',
                             'shared-sync-controls', 'sync-functional', 'inspect-stock', 'inspect-ox')
    return {'project': 'unison', 'cpu_credits': credits,
            'declared_peak_credits': jobs + sum(endpoints) + overhead,
            'compiler_jobs': jobs, 'endpoint_workers': endpoints,
            'orchestration_credits': overhead, 'cpu_token_indexes': list(range(credits)),
            'canonical_pool_manifest': str(ROOT.parent / 'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),
            'memory_reservation_gib': 32,
            'runtime_grant': False, 'token_acquisition_implemented': implemented,
            'memory_enforced': False, 'physical_io_lane_resolved': False,
            'scope': 'standing Unison tokens; finite sync server proofs; IO/memory qualification pending'}


def command(target, output, environment):
    shared = environment.get('SHARED_CPU_CREDITS')
    if shared is not None:
        shared = int(shared)
        require(1 <= shared <= 8, 'shared Unison lane must be 1..8 credits')
        require(target in ('stock-build', 'ox-build', 'sync-functional',
                           'read-parser', 'group-parser', 'aggregate-preflight', 'host-interface',
                           'shared-entrypoints', 'shared-sync-controls', 'inspect-stock', 'inspect-ox'),
                'target has no shared resource scope; use build-only or separately coordinate it')
        if target == 'sync-functional':
            require(shared == 8, 'shared functional loopback requires six endpoint plus two owner credits')
        if target in ('inspect-stock', 'inspect-ox'):
            require(shared >= 3, 'inspector build needs one compiler plus two owner credits')
    if target in ('inspect-stock', 'inspect-ox'):
        key = 'STOCK_PREFIX' if target == 'inspect-stock' else 'OX_PREFIX'
        require(bool(environment.get(key)), key + ' is required')
        compiler = Path(environment[key]).resolve() / 'ocamlopt'
        require(compiler.is_file(), 'compiler prefix must contain ocamlopt')
        return [sys.executable, str(ROOT / 'tools/semantic-inspect/run.py'),
                '--ocamlopt', str(compiler), '--build-only', '--report', str(output / 'RESULT.json')]
    if target in ('helper-stock', 'helper-ox'):
        key = 'STOCK_PREFIX' if target == 'helper-stock' else 'OX_PREFIX'
        require(bool(environment.get(key)), key + ' is required')
        compiler = Path(environment[key]).resolve() / 'ocamlopt'
        require(compiler.is_file(), 'compiler prefix must contain ocamlopt')
        return [sys.executable, str(ROOT / 'tests/helpers/run_tests.py'),
                '--ocamlopt', str(compiler)]
    if target == 'group-parser':
        return [sys.executable, str(ROOT / 'tests/validation_process/group_parser_test.py')]
    if target == 'shared-entrypoints':
        return [sys.executable, str(ROOT / 'tests/manual_shared_test.py')]
    if target == 'shared-sync-controls':
        return [sys.executable, str(ROOT / 'tests/shared_sync_controls.py')]
    if target == 'aggregate-preflight':
        return [sys.executable, str(ROOT / 'tests/sdk_container_receive/aggregate_preflight_test.py')]
    if target in ('interrupted-receipts', 'aggregate-lifecycle'):
        script = ('interrupted_receipt_lifecycle_test.py' if target == 'interrupted-receipts'
                  else 'aggregate_successor_lifecycle_test.py')
        return [sys.executable, str(ROOT / 'bench/sync' / script)]
    if target in ('stock-make', 'ox-make', 'stock-dune', 'ox-dune', 'stock-build', 'ox-build'):
        kind, system = target.split('-')
        build_only = system == 'build'
        if build_only:
            system = 'make'
        key = 'STOCK_PREFIX' if kind == 'stock' else 'OX_PREFIX'
        require(bool(environment.get(key)), key + ' is required')
        prefix = Path(environment[key]).resolve()
        require((prefix / 'ocamlopt').is_file(), 'compiler prefix must contain ocamlopt')
        if shared is not None:
            require(shared >= 3, 'shared build needs one compiler plus two owner credits')
        jobs = int(environment.get('JOBS', str(min(2, shared - 2)) if shared is not None else '4'))
        require(1 <= jobs <= 18, 'JOBS must be 1..18')
        require(shared is None or (jobs <= 2 and jobs + 2 <= shared),
                'JOBS plus two owner credits exceeds shared policy (maximum two compiler jobs)')
        return [sys.executable, str(ROOT / 'tests/build_snapshot.py'),
                '--compiler-prefix', str(prefix), '--jobs', str(jobs),
                '--build-system', system] + ([] if build_only else ['--selftest']) + [
                '--report', str(output / 'RESULT.json')]
    if target == 'sync-functional':
        argv = [sys.executable, str(ROOT / 'bench/sync/run.py')]
        for label, key in (('stock', 'STOCK_RECEIPT'), ('ox', 'OX_RECEIPT')):
            require(bool(environment.get(key)), key + ' is required')
            receipt = checked_build(environment[key])
            argv.extend(['--binary', label + '=' + receipt['binary'],
                         '--compiler', label + '=' + receipt['compiler']])
        return argv + ['--shared-qualification' if shared is not None else '--qualification', '--measure-primary-reads',
                       '--loopback-cpu-credits', str(shared if shared is not None else 4)] + (
                       ['--orchestration-cpu-credits', '2'] if shared is not None else []) + [
                       '--timeout', '30',
                       '--background-note', 'user-run finite functional checks; not a throughput comparison',
                       '--output', str(output / 'RESULT.json')]
    if target in ('cache-storage', 'cache-ownership', 'cache-cli', 'read-workers', 'read-cli', 'validation-cli'):
        require(bool(environment.get('BUILD_RECEIPT')), 'BUILD_RECEIPT is required')
        receipt = checked_build(environment['BUILD_RECEIPT'])
        if target in ('read-cli', 'validation-cli'):
            script = 'tests/read_stats/cli.py' if target == 'read-cli' else 'tests/validation_process/cli.py'
            return [sys.executable, str(ROOT / script),
                    '--build-receipt', str(Path(environment['BUILD_RECEIPT']).resolve()),
                    '--report', str(output / 'RESULT.json')]
        if target == 'read-workers':
            require(receipt['build_system'] == 'make', 'native object probes require a Make snapshot')
            return [sys.executable, str(ROOT / 'tests/workers/run.py'),
                    '--ocamlopt', receipt['compiler'],
                    '--build', str(Path(receipt['workspace']) / 'src'),
                    '--read-stats-only', '--keep-work', '--receipt', str(output / 'RESULT.json')]
        if target == 'cache-cli':
            return [sys.executable, str(ROOT / 'tests/semantic_base_cache/run.py'),
                    '--unison', receipt['binary'], '--receipt', str(output / 'RESULT.json')]
        require(receipt['build_system'] == 'make', 'native object probes require a Make snapshot')
        script = 'storage.py' if target == 'cache-storage' else 'ownership.py'
        return [sys.executable, str(ROOT / 'tests/semantic_base_cache' / script),
                '--compiler', receipt['compiler'], '--build', receipt['workspace'],
                '--report', str(output / 'RESULT.json')]
    if target == 'read-parser':
        return [sys.executable, str(ROOT / 'tests/read_stats/parser.py')]
    script = {'host-interface': 'test.py', 'host-executor': 'executor_test.py'}.get(target)
    require(script is not None, 'unknown check target')
    return [sys.executable, str(ROOT / 'tests/sdk_host_matrix' / script)]


def main():
    require(Path.cwd() == ROOT, 'run from the repository root')
    require(len(sys.argv) == 2, 'one target required; use help')
    target = sys.argv[1]
    if target == 'help':
        print(HELP)
        return
    dry = os.environ.get('DRY_RUN') == '1'
    requested = os.environ.get('OUTPUT_DIR')
    host = target in ('host-interface', 'host-executor', 'read-parser', 'group-parser',
                      'helper-stock', 'helper-ox', 'interrupted-receipts', 'aggregate-lifecycle',
                      'aggregate-preflight', 'shared-entrypoints', 'shared-sync-controls')
    require(not(host and requested), 'host checks own their output; do not set OUTPUT_DIR')
    output = Path(requested).resolve() if requested else Path(tempfile.gettempdir()) / 'UNCREATED-unison-check'
    if requested:
        require(not output.exists(), 'output directory already exists')
    argv = command(target, output, os.environ)
    if dry:
        print(json.dumps({'target': target, 'argv': argv, 'executes': False,
                          'shared_resource_plan': shared_resource_plan(target, os.environ)}))
        return
    shared = os.environ.get('SHARED_CPU_CREDITS')
    if shared is not None:
        from shared_dispatch import run, TARGETS
        require(target in TARGETS, 'target has no retained shared owner scope; not dispatched')
        if requested:
            output.mkdir(mode=0o700)
        else:
            output = Path(tempfile.mkdtemp(prefix='unison-shared-' + target + '-'))
            argv = command(target, output, os.environ)
        print('Shared owner report directory: ' + str(output), flush=True)
        raise SystemExit(run(target, argv, output, int(shared)))
    if host:
        print('Runner owns its output and process lifecycle.', flush=True)
        os.execv(sys.executable, argv)
    if requested:
        output.mkdir(mode=0o700)
    else:
        output = Path(tempfile.mkdtemp(prefix='unison-manual-' + target + '-'))
        argv = command(target, output, os.environ)
    print('Report directory: ' + str(output), flush=True)
    print('Command: ' + shlex.join(argv), flush=True)
    # Replace the dispatcher, retaining the selected runner's existing child/
    # signal/closure ownership. There is no extra supervisor or hidden SDK mode.
    os.execv(sys.executable, argv)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print('Check refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
