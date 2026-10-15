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
  host-interface          pure plan/receipt controls, no tool invocation
  host-executor           original fake validators and owned-group closure controls
JOBS defaults to 4 (1..18), for build targets only.
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


def command(target, output, environment):
    if target in ('helper-stock', 'helper-ox'):
        key = 'STOCK_PREFIX' if target == 'helper-stock' else 'OX_PREFIX'
        require(bool(environment.get(key)), key + ' is required')
        compiler = Path(environment[key]).resolve() / 'ocamlopt'
        require(compiler.is_file(), 'compiler prefix must contain ocamlopt')
        return [sys.executable, str(ROOT / 'tests/helpers/run_tests.py'),
                '--ocamlopt', str(compiler)]
    if target == 'group-parser':
        return [sys.executable, str(ROOT / 'tests/validation_process/group_parser_test.py')]
    if target in ('stock-make', 'ox-make', 'stock-dune', 'ox-dune'):
        kind, system = target.split('-')
        key = 'STOCK_PREFIX' if kind == 'stock' else 'OX_PREFIX'
        require(bool(environment.get(key)), key + ' is required')
        prefix = Path(environment[key]).resolve()
        require((prefix / 'ocamlopt').is_file(), 'compiler prefix must contain ocamlopt')
        jobs = int(environment.get('JOBS', '4'))
        require(1 <= jobs <= 18, 'JOBS must be 1..18')
        return [sys.executable, str(ROOT / 'tests/build_snapshot.py'),
                '--compiler-prefix', str(prefix), '--jobs', str(jobs),
                '--build-system', system, '--selftest', '--report', str(output / 'RESULT.json')]
    if target == 'sync-functional':
        argv = [sys.executable, str(ROOT / 'bench/sync/run.py')]
        for label, key in (('stock', 'STOCK_RECEIPT'), ('ox', 'OX_RECEIPT')):
            require(bool(environment.get(key)), key + ' is required')
            receipt = checked_build(environment[key])
            argv.extend(['--binary', label + '=' + receipt['binary'],
                         '--compiler', label + '=' + receipt['compiler']])
        return argv + ['--qualification', '--measure-primary-reads',
                       '--loopback-cpu-credits', '4', '--timeout', '30',
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
                      'helper-stock', 'helper-ox')
    require(not(host and requested), 'host checks own their output; do not set OUTPUT_DIR')
    output = Path(requested).resolve() if requested else Path(tempfile.gettempdir()) / 'UNCREATED-unison-check'
    if requested:
        require(not output.exists(), 'output directory already exists')
    argv = command(target, output, os.environ)
    if dry:
        print(json.dumps({'target': target, 'argv': argv, 'executes': False}))
        return
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
