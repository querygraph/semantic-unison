#!/usr/bin/env python3
"""Test the native observation/borrowed-descriptor lease bridge in isolation."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

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
sources = ['src/fileObservation_stubs.c', 'src/fileObservation.mli', 'src/fileObservation.ml',
           'src/cloneRange.mli', 'src/cloneRange.ml', 'src/cloneLease.mli', 'src/cloneLease.ml',
           'tests/clone_lease/fixture.c']
with tempfile.TemporaryDirectory(prefix='unison-clone-lease-', dir='/private/tmp') as tmp:
    work = Path(tmp)
    for name in sources + ['tests/clone_lease/test.ml']:
        data = (root / name).read_bytes()
        (work / Path(name).name).write_bytes(data)
        print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
    for name in sources:
        subprocess.run([compiler, '-I', '+unix', '-c', Path(name).name], cwd=work, env=environment, check=True)
    subprocess.run([compiler, '-I', '+unix', 'unix.cmxa', 'fileObservation_stubs.o', 'fixture.o',
                    'fileObservation.cmx', 'cloneRange.cmx', 'cloneLease.cmx', 'test.ml', '-o', 'lease-test'],
                   cwd=work, env=environment, check=True)
    print('Compiler', subprocess.check_output([compiler, '-version'], text=True, env=environment).strip(), flush=True)
    result = subprocess.run([str(work / 'lease-test'), str(work)], cwd=work, env=environment, timeout=30)
    if result.returncode == 77:
        print('SKIP: native lease cases require macOS observation')
    else:
        result.check_returncode()
