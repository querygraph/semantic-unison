"""Two serial one-job compiler controls, original fixed synthetic frames only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT / 'src/dngPrivateData.mli', ROOT / 'src/dngPrivateData.ml',
           ROOT / 'tests/dng_private_data/test.ml']


def main():
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
    workspace = Path(tempfile.mkdtemp(prefix='unison-dng-private-framing-'))
    workspace.chmod(0o700)
    runs = []
    for label, compiler in [('stock', '/Users/alexy/.opam/default/bin/ocamlopt'),
                            ('ox', '/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt')]:
        path = workspace / label
        path.mkdir(mode=0o700)
        for source in SOURCES:
            shutil.copyfile(source, path / source.name)
        command = [compiler, '-w', '+a-70', '-warn-error', '+a-70',
                   'dngPrivateData.mli', 'dngPrivateData.ml', 'test.ml', '-o', 'test']
        for phase, argv in [('compile', command), ('fixed-controls', [str(path / 'test')])]:
            result = subprocess.run(argv, cwd=path, capture_output=True, text=True, timeout=15)
            row = {'label': label, 'phase': phase, 'command': argv,
                   'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
            runs.append(row)
            if result.returncode:
                print(json.dumps({'workspace': str(workspace), 'runs': runs}), flush=True)
                raise SystemExit(result.returncode)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == value for p, value in pins.items())
    print(json.dumps({'state': 'TWO_COMPILER_FIXED_FRAMING_CONTROLS_PASS',
          'workspace': str(workspace), 'source_pins': pins, 'runs': runs,
          'semantic_eligibility_qualified': False}), flush=True)


if __name__ == '__main__':
    main()
