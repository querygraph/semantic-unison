#!/usr/bin/env python3
"""Qualify strict typed range results and the actual macOS C ABI in isolation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--negative-control', action='store_true',
                        help='remove only the private strict mutation guard and require byte-oracle failure')
    parser.add_argument('--skip-native', action='store_true', help='run only portable synthetic result tests')
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    compiler = str(Path(compiler).resolve())
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    for name in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(name, None)
    work = Path(tempfile.mkdtemp(prefix='unison-native-copy-range-', dir='/private/tmp'))
    records = []
    sources = ['src/copyRange.ml', 'src/copyRange.mli', 'src/nativeCopyRange_stubs.c',
               'src/copy_stubs.c', 'src/system/system_generic.ml',
               'src/system/system_intf.ml', 'src/fs.ml', 'src/fs.mli',
               'tests/native_copy_range/test.ml', 'tests/native_copy_range/native.ml',
               'tests/native_copy_range/run.py']
    receipt = {'schema': 1, 'scope': 'synthetic typed-loop and actual macOS unavailable/preflight ABI',
               'work': str(work), 'retained': args.keep_work, 'commands': records,
               'source_pins': {}, 'native_other_platform_qualified': False,
               'physical_sharing_qualified': False, 'production_Photo_access': False,
               'Adobe_invoked': False, 'success': False}

    def run(command, directory, name, *, allow_failure=False, timeout=60):
        log = directory / (name + '.log')
        result = subprocess.run(command, cwd=directory, env=environment,
                                text=True, capture_output=True, timeout=timeout)
        log.write_text(result.stdout + result.stderr)
        records.append({'command': command, 'cwd': str(directory), 'exit': result.returncode,
                        'log': str(log), 'log_sha256': sha(log)})
        if result.stdout:
            print(result.stdout, end='', flush=True)
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr, flush=True)
        if not allow_failure:
            result.check_returncode()
        return result

    try:
        copied = work / 'frozen-inputs'
        for source in sources:
            target = copied / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / source, target)
            receipt['source_pins'][source] = sha(target)
        receipt['compiler'] = {'path': compiler, 'sha256': sha(Path(compiler)),
                               'version': run([compiler, '-version'], work, 'compiler-version').stdout.strip(),
                               'library': run([compiler, '-where'], work, 'compiler-library').stdout.strip()}
        for mode in ('unit', 'negative') if args.negative_control else ('unit',):
            directory = work / mode
            directory.mkdir()
            for name in ('copyRange.ml', 'copyRange.mli'):
                shutil.copyfile(copied / 'src' / name, directory / name)
            shutil.copyfile(copied / 'tests/native_copy_range/test.ml', directory / 'test.ml')
            if mode == 'negative':
                source = (directory / 'copyRange.ml').read_text()
                needle = '| Native_declined (_,_,context) when context.mutation = Indeterminate ->'
                if source.count(needle) != 1:
                    raise RuntimeError('mutation-control seam no longer unique')
                source = source.replace(needle, '| Native_declined (_,_,context) when false ->')
                (directory / 'copyRange.ml').write_text(source)
                receipt['negative_control'] = {
                    'only_production_edit': 'disable strict indeterminate-decline guard in private CopyRange.ml',
                    'source': str(directory / 'copyRange.ml'),
                    'source_sha256': sha(directory / 'copyRange.ml'),
                    'expected_failure': 'unauthorized or repeated suffix write'}
            for name in ('copyRange.mli', 'copyRange.ml'):
                run([compiler, '-I', '+unix', '-c', name], directory, 'compile-' + name)
            run([compiler, '-I', '+unix', 'unix.cmxa', 'copyRange.cmx', 'test.ml', '-o', 'typed-test'],
                directory, 'link')
            result = run([str(directory / 'typed-test')], directory, 'test',
                         allow_failure=(mode == 'negative'), timeout=30)
            if mode == 'negative':
                if result.returncode == 0 or 'unauthorized or repeated suffix write' not in result.stderr:
                    raise RuntimeError('private mutation-guard negative control did not fail the independent byte oracle')
                receipt['negative_control']['detected'] = True
            else:
                receipt['typed_named_groups'] = sum(line.startswith('PASS ') for line in result.stdout.splitlines())
        if args.skip_native or sys.platform != 'darwin':
            receipt['native_abi'] = {'executed': False, 'reason': 'explicitly skipped' if args.skip_native else 'host is not macOS'}
        else:
            directory = work / 'native'
            directory.mkdir()
            for name in ('copyRange.ml', 'copyRange.mli', 'nativeCopyRange_stubs.c', 'copy_stubs.c'):
                shutil.copyfile(copied / 'src' / name, directory / name)
            shutil.copyfile(copied / 'tests/native_copy_range/native.ml', directory / 'native.ml')
            # Use the actual System external declarations, not a guessed tuple
            # ABI. All unrelated System functions stay outside this harness.
            generic = (copied / 'src/system/system_generic.ml').read_text()
            declarations = []
            for name, symbol in [('copy_file', 'unison_copy_file'), ('copy_file_status', 'unison_copy_file_status')]:
                found = re.findall(r'external ' + name + r'\s*:.*?=\s*"' + symbol + r'"', generic, re.S)
                if len(found) != 1:
                    raise RuntimeError('actual external declaration is not unique: ' + name)
                declarations.append(found[0])
            (directory / 'nativeApi.ml').write_text('\n'.join(declarations) + '\n')
            receipt['derived_native_api'] = {'source': str(directory / 'nativeApi.ml'),
                                             'sha256': sha(directory / 'nativeApi.ml'),
                                             'from': 'src/system/system_generic.ml: two unchanged actual external declarations'}
            for name in ('copyRange.mli', 'copyRange.ml', 'nativeApi.ml', 'nativeCopyRange_stubs.c', 'copy_stubs.c'):
                run([compiler, '-I', '+unix', '-ccopt', '-Wall', '-ccopt', '-Wextra', '-c', name],
                    directory, 'compile-' + name)
            run([compiler, '-I', '+unix', 'unix.cmxa', 'copyRange.cmx', 'nativeApi.cmx',
                 'nativeCopyRange_stubs.o', 'copy_stubs.o', 'native.ml', '-o', 'native-test'], directory, 'link')
            fixtures = directory / 'fixtures'
            fixtures.mkdir()
            result = run([str(directory / 'native-test'), str(fixtures)], directory, 'test', timeout=30)
            if any(fixtures.iterdir()):
                raise RuntimeError('native fixture left an unexpected owned name')
            receipt['native_abi'] = {'executed': True, 'platform': 'macOS',
                                     'named_groups': sum(line.startswith('PASS ') for line in result.stdout.splitlines()),
                                     'other_platforms': False, 'block_sharing': False}
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)): {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}
                                for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work / 'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print('Receipt ' + str(target), flush=True)
        print('Artifacts ' + str(work) + (' (retained)' if args.keep_work else ' (removed after receipt)'), flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
