#!/usr/bin/env python3
"""Qualify held-FD observations and private attribute faults in isolated files."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
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
with tempfile.TemporaryDirectory(prefix='unison-file-observation-', dir='/private/tmp') as tmp:
    work = Path(tmp)
    for name in ['src/fileObservation.mli', 'src/fileObservation.ml', 'src/fileObservation_stubs.c',
                 'tests/file_observation/fixture.c', 'tests/file_observation/test.ml']:
        data = (root / name).read_bytes()
        (work / Path(name).name).write_bytes(data)
        print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
    for name in ['fileObservation.mli', 'fileObservation.ml', 'fixture.c']:
        subprocess.run([compiler, '-I', '+unix', '-c', name], cwd=work, env=environment, check=True)
    subprocess.run([compiler, '-I', '+unix', 'unix.cmxa', 'fixture.o', 'fileObservation.cmx',
                    'test.ml', '-o', 'observation-test'], cwd=work, env=environment, check=True)
    baseline = work / 'baseline'
    baseline.write_bytes(bytes(range(256)) * 32)
    if hasattr(os, 'chflags'):
        os.chflags(baseline, stat.UF_NODUMP)
    os.utime(baseline, ns=(1700000100987654321, 1700000000123456789))
    s = baseline.stat()
    expected = [f'{s.st_dev & 0xffffffff:08x}', f'{s.st_ino & 0xffffffffffffffff:016x}',
                str(s.st_size), str(s.st_nlink), str(getattr(s, 'st_flags', 0)),
                str(s.st_mtime_ns // 10**9), str(s.st_mtime_ns % 10**9),
                str(s.st_ctime_ns // 10**9), str(s.st_ctime_ns % 10**9)]
    print('Compiler', subprocess.check_output([compiler, '-version'], text=True, env=environment).strip(), flush=True)
    result = subprocess.run([str(work / 'observation-test'), str(work), *expected],
                            cwd=work, env=environment, timeout=30)
    if result.returncode == 77:
        print('SKIP: native observation requires macOS')
    else:
        result.check_returncode()
