#!/usr/bin/env python3
"""Exercise production StagePublication with small isolated native fixtures."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    sources = ['src/stagePublication.mli', 'src/stagePublication.ml',
               'src/stagePublication_stubs.c', 'tests/stage_publication/fixture.c']
    library = Path(subprocess.check_output([compiler, '-where'], text=True,
                                           env=environment).strip())
    with tempfile.TemporaryDirectory(prefix='unison-stage-publication-', dir='/private/tmp') as tmp:
        work = Path(tmp)
        for name in sources + ['tests/stage_publication/test.ml']:
            data = (root / name).read_bytes()
            (work / Path(name).name).write_bytes(data)
            print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
        harness = (work / 'test.ml').read_text()
        if 'val with_async_exns' in (library / 'sys.mli').read_text():
            harness = harness.replace('let with_async_exns f = f ()',
                                      'let with_async_exns = Sys.with_async_exns')
        (work / 'test.ml').write_text(harness)
        print('compiled test.ml', hashlib.sha256(harness.encode()).hexdigest(), flush=True)
        # fixture.c includes the byte-identical production C translation unit
        # under private syscall wrappers; never link duplicate native symbols.
        for name in ['src/stagePublication.mli', 'src/stagePublication.ml',
                     'tests/stage_publication/fixture.c']:
            subprocess.run([compiler, '-I', '+unix', '-c', Path(name).name],
                           cwd=work, env=environment, check=True)
        subprocess.run([compiler, '-I', '+unix', 'unix.cmxa',
                        'fixture.o',
                        'stagePublication.cmx', 'test.ml', '-o', 'publication-test'],
                       cwd=work, env=environment, check=True)
        print('Compiler', subprocess.check_output([compiler, '-version'], text=True,
                                                  env=environment).strip(), flush=True)
        result = subprocess.run([str(work / 'publication-test'), str(work)],
                                cwd=work, env=environment, timeout=60)
        if result.returncode == 77:
            print('SKIP: native exclusive publication requires macOS 10.12+')
        else:
            result.check_returncode()


if __name__ == '__main__':
    main()
