#!/usr/bin/env python3
"""Qualify additive APFS creation-parent handles using isolated synthetic files."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--ocamlopt', default='ocamlopt')
args = parser.parse_args()
if sys.platform != 'darwin':
    print('SKIP: this native APFS fixture requires macOS')
    raise SystemExit(0)
compiler = shutil.which(args.ocamlopt)
if compiler is None:
    parser.error('native compiler unavailable')
root = Path(__file__).resolve().parents[2]
environment = os.environ.copy()
for name in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
    environment.pop(name, None)
with tempfile.TemporaryDirectory(prefix='unison-clone-handles-', dir='/private/tmp') as tmp:
    work = Path(tmp)
    for name in ('src/copy_stubs.c', 'src/fs.ml', 'src/fs.mli',
                 'tests/clone_handles/fixture.c', 'tests/clone_handles/test.ml'):
        data = (root / name).read_bytes()
        (work / Path(name).name).write_bytes(data)
        print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
    # Compile the actual Fs clone types/wrappers with only the unrelated path
    # translation shim replaced. No reimplementation of their ABI declarations.
    ml = (work / 'fs.ml').read_text().split('type clone_stage_decline =', 1)[1].split('(****)', 1)[0]
    mli = (work / 'fs.mli').read_text().split('type clone_stage_decline =', 1)[1]
    (work / 'fspath.ml').write_text('type t = string\n')
    (work / 'fs.ml').write_text('let path (p : Fspath.t) = p\ntype clone_stage_decline =' + ml)
    (work / 'fs.mli').write_text('type clone_stage_decline =' + mli)
    native = (work / 'copy_stubs.c').read_text().split('static value unsn_clone_stage_impl', 1)[1]
    before_resources = native.split('char *src = strdup', 1)[0]
    assert 'caml_alloc_tuple(keep_parent ? 3 : 2)' in before_resources
    assert 'if (keep_parent) Store_field(pair, 2, Val_int(-1));' in before_resources
    assert 'declined = caml_alloc(1, 1)' in before_resources
    print('Preallocation ordering source guard passed (not OOM fault qualification)', flush=True)
    print('Compiler', subprocess.check_output([compiler, '-version'], env=environment, text=True).strip(), flush=True)
    for name in ('fspath.ml', 'fs.mli', 'fs.ml', 'fixture.c'):
        subprocess.run([compiler, '-I', '+unix', '-ccopt', '-Wall', '-ccopt', '-Wextra', '-c', name],
                       cwd=work, env=environment, check=True)
    subprocess.run([compiler, '-I', '+unix', 'unix.cmxa', 'fspath.cmx', 'fs.cmx',
                    'fixture.o', 'test.ml', '-o', 'handles-test'], cwd=work, env=environment, check=True)
    source = work / 'source'
    source.write_bytes(bytes(range(256)) * 32)
    subprocess.run(['/usr/bin/xattr', '-w', 'org.unison.fixture', 'source xattr', str(source)], check=True)
    subprocess.run(['/usr/bin/xattr', '-w', 'com.apple.ResourceFork', 'source fork', str(source)], check=True)
    subprocess.run(['/bin/chmod', '+a', 'everyone allow read', str(source)], check=True)
    source.chmod(0o400)
    flagged = work / 'flagged'
    flagged.write_bytes(b'flagged source')
    os.chflags(flagged, stat.UF_NODUMP)
    try:
        result = subprocess.run([str(work / 'handles-test'), str(work)], cwd=work,
                                env=environment, timeout=60)
    finally:
        os.chflags(flagged, 0)
    if result.returncode == 77:
        print('SKIP: fixture filesystem does not provide APFS clone staging')
    else:
        result.check_returncode()
        acl = subprocess.check_output(['/bin/ls', '-le', str(source)], text=True)
        assert 'everyone allow read' in acl
        assert source.stat().st_mode & 0o777 == 0o400
        for attribute, expected in [('org.unison.fixture', b'source xattr'),
                                    ('com.apple.ResourceFork', b'source fork')]:
            value = subprocess.check_output(['/usr/bin/xattr', '-px', attribute, str(source)], text=True)
            assert bytes.fromhex(value) == expected
        print('Original source ACL, xattrs, resource fork and mode preserved', flush=True)
