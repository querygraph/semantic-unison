#!/usr/bin/env python3
"""Small real native cleanup controls; no Adobe, Photo or production data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ('src/finalPublication.ml', 'src/finalPublication.mli',
           'src/finalPublication_stubs.c', 'tests/obsolete_cleanup/fixture.c',
           'tests/obsolete_cleanup/test.ml', 'tests/obsolete_cleanup/run.py')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    work = Path(tempfile.mkdtemp(prefix='unison-obsolete-cleanup-', dir='/private/tmp'))
    env = os.environ.copy()
    for key in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):
        env.pop(key, None)
    receipt = {'schema': 1, 'success': False, 'work': str(work), 'retained': True,
               'source_pins': {name: sha(ROOT / name) for name in SOURCES},
               'compiler': str(compiler), 'compiler_sha256': sha(compiler),
               'commands': [], 'scope': 'Production native obsolete regular-leaf cleanup with private syscall fault controls; direct FinalPublication only',
               'Adobe_or_Photo_or_UI_access': False, 'performance_claim': False}
    def command(argv, directory, label, negative=False):
        result = subprocess.run([str(value) for value in argv], cwd=directory, env=env,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        log = directory / (label + '.log'); log.write_text(result.stdout)
        receipt['commands'].append({'argv': [str(v) for v in argv], 'cwd': str(directory),
            'exit': result.returncode, 'log': str(log), 'log_sha256': sha(log)})
        if negative:
            assert result.returncode == 2 and 'DESIGNATED pathname cleanup damaged replacement inventory' in result.stdout, result.stdout
        else:
            if result.returncode: print(result.stdout, flush=True)
            result.check_returncode()
        print(label, result.returncode, result.stdout[-1300:], flush=True)
        return result
    try:
        receipt['compiler_version'] = command([compiler, '-version'], work, 'compiler').stdout.strip()
        frozen = work / 'frozen'; frozen.mkdir()
        for name in SOURCES:
            target = frozen / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        for mode in ('fixed', 'pathname-negative'):
            directory = work / mode; directory.mkdir()
            for name in SOURCES:
                shutil.copy2(frozen / name, directory / Path(name).name)
            if mode == 'pathname-negative':
                path = directory / 'finalPublication.ml'; text = path.read_text()
                anchor = '  clear_obsolete_raw t working_dir path'
                assert text.count(anchor) == 1
                path.write_text(text.replace(anchor, '  ignore t; Unix.unlink (Filename.concat working_dir path)'))
            for name in ('finalPublication.mli','finalPublication.ml','fixture.c'):
                command([compiler, '-I', '+unix', '-c', name], directory, 'compile-' + name)
            command([compiler,'-I','+unix','unix.cmxa','finalPublication.cmx','fixture.o','test.ml','-o','test'],directory,'link')
            command([directory / 'test', *(['negative'] if mode != 'fixed' else [])], directory, 'run', negative=mode != 'fixed')
        assert all(sha(ROOT / name) == value for name,value in receipt['source_pins'].items())
        receipt['artifacts'] = {str(path.relative_to(work)): {'bytes': path.stat().st_size, 'sha256': sha(path)}
            for path in sorted(work.rglob('*')) if path.is_file()}
        receipt['success'] = True
    finally:
        args.receipt.write_text(json.dumps(receipt,indent=2) + '\n')
        print('receipt', args.receipt, 'work', work, flush=True)

if __name__ == '__main__':
    main()
