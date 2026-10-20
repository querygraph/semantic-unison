"""Compile-only worker/owner boundary checks against current OxCaml objects."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build-result', type=Path, required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
hash_file = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
build = json.loads(a.build_result.read_text())
compiler = Path(build['compiler'])
assert hash_file(compiler) == build['compiler_sha256']
source = Path(build['workspace']) / 'src'
production = {n: h for n, h in build['source_sha256'].items() if n.startswith('src/')}
assert production and all(hash_file(root / n) == h for n, h in production.items())
version = subprocess.check_output([str(compiler), '-version'], text=True, timeout=10).strip()
assert '+ox' in version
work = Path(tempfile.mkdtemp(prefix='unison-worker-ffi-boundary-', dir='/private/tmp'))
cases = [
    ('private-hash', 'ignore (SemanticHash.string "abc")', True),
    ('owner-record-publication', 'ignore (ComponentHash.record_publication_available ())', False),
    ('owner-cache-parent', 'ignore (DngComponents.open_cache_parent "never-opened-compile-only")', False),
]
rows = []
for name, expression, accepted in cases:
    probe = work / (name.replace('-', '_') + '.ml')
    probe.write_text('let _ = Domain.Safe.spawn (fun () -> ' + expression + ')\n')
    argv = [str(compiler), '-I', str(source), '-I', str(source / 'ubase'),
            '-I', str(source / 'system'), '-I', str(source / 'lwt'),
            '-c', str(probe)]
    result = subprocess.run(argv, cwd=work, text=True, capture_output=True, timeout=20)
    output = result.stdout + result.stderr
    log = work / (name + '.log')
    log.write_text(output)
    if accepted:
        assert result.returncode == 0, output
    else:
        symbol = {'owner-record-publication': 'ComponentHash.record_publication_available',
                  'owner-cache-parent': 'DngComponents.open_cache_parent'}[name]
        assert result.returncode != 0 and ('Error: The value "' + symbol +
            '" is "nonportable"') in output, output
    rows.append(dict(name=name,expected_compile_acceptance=accepted,
                     command=argv,exit_code=result.returncode,
                     source=str(probe),source_sha256=hash_file(probe),
                     log=str(log),log_sha256=hash_file(log),diagnostics=output))
interfaces = ['semanticHash.cmi', 'componentHash.cmi', 'dngComponents.cmi']
a.report.write_text(json.dumps(dict(schema='unison-worker-ffi-boundary/1',passed=True,
    compiler=str(compiler),compiler_sha256=hash_file(compiler),version=version,
    current_production_source_sha256=production,
    actual_interface_sha256={str(source/n):hash_file(source/n) for n in interfaces},
    runner_sha256=hash_file(Path(__file__)),cases=rows,workspace=str(work),
    scope='Compile only. No generated program executed, no target path opened, no SDK/Photo/transport. '
          'Two representative owner APIs reject; this is not a complete call-graph or C-safety proof.'),indent=2)+'\n')
print('PASS private hash accepted; owner publication/cache APIs rejected; compile only', flush=True)
