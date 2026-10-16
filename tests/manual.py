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
  stock-check / ox-check  Make plus selftests capped at3 semantic workers, shared lane
  stock-dune-check / ox-dune-check  Dune plus the same shared bounded selftests
  stock-build / ox-build  Make build only; no resulting Unison executable invocation
  inspect-stock / inspect-ox build/retain the read-only inspector only; compiler prefix required
  inspect-file            reuse a pinned inspector; INSPECTOR_RECEIPT and absolute INSPECT_INPUT required
  inspector-reuse-controls fixed inert artifact/refusal checks; no compiler or image reads
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
  shared-io-controls      pure physical-IO claim controls; no device or IO lock access
  sde-conformance         serial stock/Ox fixed independent wire controls; no SDK/camera
  dng-private-framing     serial stock/Ox fixed synthetic framing checks; no SDK/image reads
  dng-private-diagnostic  serial stock/Ox stdin diagnostic controls; generated inputs only
  private-dng-framing-input  admitted bounded receiving-clone diagnostic; explicit FRAMING_PLAN and SHA required
  private-dng-local-clone  tiny synthetic local source-clone exact/no-op controls; no SDK/Photo
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
    build = target in ('stock-build', 'ox-build', 'stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check')
    framing = target in ('sde-conformance', 'dng-private-framing', 'dng-private-diagnostic')
    inspector = target in ('inspect-stock', 'inspect-ox')
    inspect_file = target in ('inspect-file', 'private-dng-framing-input')
    endpoints = [3, 3] if target == 'sync-functional' else [3] if target == 'private-dng-local-clone' else []
    jobs = int(environment.get('JOBS', str(min(2, credits - 2)))) if build else 1 if inspector or framing else 0
    selftest_endpoints = [3, 3] if target in ('stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check') else []
    overhead = 2 if build or inspector or framing or inspect_file or endpoints else 1
    inspector_workers = 1 if inspect_file else 0
    declared_peak = max(jobs + sum(endpoints) + inspector_workers, sum(selftest_endpoints)) + overhead
    require((not build or 1 <= jobs <= 2) and declared_peak <= credits,
            'declared shared work exceeds project grant')
    implemented = target in ('stock-build', 'ox-build', 'stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check', 'read-parser', 'group-parser',
                             'aggregate-preflight', 'host-interface', 'shared-entrypoints',
                             'shared-sync-controls', 'sync-functional', 'inspect-stock', 'inspect-ox',
                             'inspect-file', 'inspector-reuse-controls', 'shared-io-controls', 'sde-conformance', 'dng-private-framing', 'dng-private-diagnostic', 'private-dng-framing-input', 'private-dng-local-clone')
    return {'project': 'unison', 'cpu_credits': credits,
            'declared_peak_credits': declared_peak,
            'selftest_endpoint_workers': selftest_endpoints,
            'build_and_selftest_are_serial': bool(selftest_endpoints),
            'retained_property_reader_limit': 36 if target == 'sync-functional' and environment.get('SYNC_PROPERTY_REMOVAL_CONTROLS') == '1' else 0,
            'inspector_workers': inspector_workers,
            'compiler_jobs': jobs, 'endpoint_workers': endpoints,
            'orchestration_credits': overhead, 'cpu_token_indexes': list(range(credits)),
            'canonical_pool_manifest': str(ROOT.parent / 'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),
            'memory_reservation_gib': 32,
            'runtime_grant': False, 'token_acquisition_implemented': implemented,
            'memory_enforced': False, 'physical_io_lane_resolved': False,
            'scope': 'standing Unison tokens; finite sync server proofs; IO/memory qualification pending'}


def command(target, output, environment):
    io_path = environment.get('SHARED_IO_ADMISSION')
    io_sha = environment.get('SHARED_IO_ADMISSION_SHA256')
    if io_path is not None or io_sha is not None:
        require(bool(io_path) and Path(io_path).is_absolute() and bool(io_sha)
                and len(io_sha) == 64 and all(c in '0123456789abcdef' for c in io_sha)
                and environment.get('SHARED_CPU_CREDITS') is not None
                and target in ('inspect-file', 'private-dng-local-clone', 'private-dng-framing-input', 'sync-functional'),
                'IO mode requires pinned admission, shared CPU and complete job with qualified closure audit')
    property_controls = environment.get('SYNC_PROPERTY_REMOVAL_CONTROLS')
    require(property_controls is None or (property_controls == '1' and target == 'sync-functional'
            and environment.get('SHARED_CPU_CREDITS') == '8' and bool(io_path) and bool(io_sha)),
            'property-removal controls require explicit shared8 functional IO admission')
    shared = environment.get('SHARED_CPU_CREDITS')
    if shared is not None:
        shared = int(shared)
        require(1 <= shared <= 8, 'shared Unison lane must be 1..8 credits')
        require(target in ('stock-build', 'ox-build', 'stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check', 'sync-functional',
                           'read-parser', 'group-parser', 'aggregate-preflight', 'host-interface',
                           'shared-entrypoints', 'shared-sync-controls', 'inspect-stock', 'inspect-ox',
                           'inspect-file', 'inspector-reuse-controls', 'shared-io-controls', 'sde-conformance', 'dng-private-framing', 'dng-private-diagnostic', 'private-dng-framing-input', 'private-dng-local-clone'),
                'target has no shared resource scope; use build-only or separately coordinate it')
        if target == 'private-dng-local-clone':
            require(shared >= 5, 'local clone controls require three worker plus two owner credits')
        if target in ('sde-conformance', 'dng-private-framing', 'dng-private-diagnostic'):
            require(shared >= 3, 'framing controls require one compiler plus two owner credits')
        if target == 'sync-functional':
            require(shared == 8, 'shared functional loopback requires six endpoint plus two owner credits')
        if target in ('inspect-stock', 'inspect-ox'):
            require(shared >= 3, 'inspector build needs one compiler plus two owner credits')
        if target in ('inspect-file', 'private-dng-framing-input'):
            require(shared >= 3, 'inspector execution needs one worker plus two owner credits')
    if target == 'private-dng-framing-input':
        require(shared is not None and environment.get('SHARED_IO_ADMISSION'),
                'camera-derived framing input requires explicit shared IO admission')
        path = environment.get('FRAMING_PLAN', '')
        digest = environment.get('FRAMING_PLAN_SHA256', '')
        require(Path(path).is_absolute() and len(digest) == 64 and
                all(c in '0123456789abcdef' for c in digest), 'exact absolute framing plan and SHA required')
        return [sys.executable, str(ROOT / 'tools/private-dng-framing/admitted.py'),
                '--plan', path, '--plan-sha256', digest]
    if target == 'private-dng-local-clone':
        return [sys.executable, str(ROOT / 'tests/private_dng_local_clone/run.py')]
    if target == 'sde-conformance':
        return [sys.executable, str(ROOT / 'tests/semantic/conformance/shared.py')]
    if target == 'dng-private-diagnostic':
        return [sys.executable, str(ROOT / 'tools/private-dng-framing/controls.py')]
    if target == 'dng-private-framing':
        return [sys.executable, str(ROOT / 'tests/dng_private_data/run.py')]
    if target == 'inspector-reuse-controls':
        return [sys.executable, str(ROOT / 'tools/semantic-inspect/reuse_test.py')]
    if target == 'shared-io-controls':
        return [sys.executable, str(ROOT / 'tests/shared_io_controls.py')]
    if target == 'inspect-file':
        for key in ('INSPECTOR_RECEIPT', 'INSPECT_INPUT'):
            require(bool(environment.get(key)) and Path(environment[key]).is_absolute(),
                    key + ' must be an explicit absolute path')
        profile = environment.get('INSPECT_PROFILE', 'org.firstpair.dng-xmp/1')
        require(profile in ('org.firstpair.dng-xmp/0', 'org.firstpair.dng-xmp/1'), 'unknown inspector profile')
        argv = [sys.executable, str(ROOT / 'tools/semantic-inspect/run.py'),
                '--use-build', environment['INSPECTOR_RECEIPT'], '--', '--profile', profile]
        if environment.get('INSPECT_BASE'):
            require(Path(environment['INSPECT_BASE']).is_absolute(), 'INSPECT_BASE must be absolute')
            argv += ['--base', environment['INSPECT_BASE']]
        return argv + [environment['INSPECT_INPUT']]
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
    if target in ('stock-make', 'ox-make', 'stock-dune', 'ox-dune', 'stock-build', 'ox-build', 'stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check'):
        kind, system = target.split('-', 1)
        build_only = system == 'build'
        shared_check = system in ('check', 'dune-check')
        if build_only or system == 'check':
            system = 'make'
        elif system == 'dune-check':
            system = 'dune'
        if shared_check:
            require(shared is not None and shared >= 8, 'shared selftest requires full Unison8 lane')
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
                '--build-system', system] + ([] if build_only else ['--selftest']) + (['--selftest-workers', '3'] if shared_check else []) + [
                '--report', str(output / 'RESULT.json')]
    if target == 'sync-functional':
        argv = [sys.executable, str(ROOT / 'bench/sync/run.py')]
        for label, key in (('stock', 'STOCK_RECEIPT'), ('ox', 'OX_RECEIPT')):
            require(bool(environment.get(key)), key + ' is required')
            receipt = checked_build(environment[key])
            argv.extend(['--binary', label + '=' + receipt['binary'],
                         '--compiler', label + '=' + receipt['compiler'],
                         '--expected-binary-sha256', label + '=' + receipt['binary_sha256'],
                         '--expected-compiler-sha256', label + '=' + receipt['compiler_sha256']])
        if property_controls == '1':
            argv += ['--property-removal-controls']
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
                      'aggregate-preflight', 'shared-entrypoints', 'shared-sync-controls',
                      'inspector-reuse-controls', 'shared-io-controls')
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
        io_request = ({'path': os.environ['SHARED_IO_ADMISSION'],
                       'sha256': os.environ['SHARED_IO_ADMISSION_SHA256']}
                      if os.environ.get('SHARED_IO_ADMISSION') else None)
        raise SystemExit(run(target, argv, output, int(shared), io_admission=io_request))
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
