#!/usr/bin/env python3
"""Compile original tiny C inputs; never load SDK code or execute objects."""
import hashlib
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('object_cache', root/'tools/adobe-validator/object_cache.py')
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)
work = Path(tempfile.mkdtemp(prefix='unison-native-cache-', dir='/private/tmp'))
print('Workspace:', work, flush=True)
source, outer, inner = [work/name for name in ('original.c', 'outer header.h', 'inner $ header.h')]
source.write_text('#include "outer header.h"\nint original(void) { return VALUE; }\n')
outer.write_text('#include "inner $ header.h"\n')
inner.write_text('#define VALUE 17\n')
output = work/'original object.o'
calls, cases = [], []
def run(command):
    calls.append(list(map(str, command)))
    subprocess.run(command, check=True, capture_output=True, text=True)
def compile_case(name, hit, flags=()):
    _, actual = cache.compile_object('clang', ['-O2', *flags], source, output, run)
    assert actual == hit, (name, actual)
    cases.append({'name': name, 'cache_hit': actual, 'object_sha256': cache.digest(output)})
    print('PASS', name, flush=True)
compile_case('initial', False)
compile_case('unchanged', True)
previous = cache.digest(output)
stamp = inner.stat()
inner.write_text('#define VALUE 18\n')
os.utime(inner, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
compile_case('transitive-header-restored-mtime', False)
assert cache.digest(output) != previous
compile_case('header-successor-hit', True)
stamp = source.stat()
source.write_text(source.read_text().replace('return VALUE', 'return VALUE + 1'))
os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
compile_case('source-restored-mtime', False)
compile_case('flags-changed', False, ['-DOTHER=1'])
output.write_bytes(b'private corrupt object')
compile_case('object-corrupted', False, ['-DOTHER=1'])
output.with_suffix('.inputs.json').write_text('{}')
compile_case('receipt-corrupted', False, ['-DOTHER=1'])
output.with_suffix('.d').unlink()
compile_case('dependencies-missing', False, ['-DOTHER=1'])
compile_case('restored-hit', True, ['-DOTHER=1'])
def changing_run(command):
    run(command)
    if '-c' in command:
        inner.write_text('#define VALUE 19\n')
try:
    cache.compile_object('clang', ['-O2', '-DNEW=1'], source, output, changing_run)
    raise AssertionError('changed build input accepted')
except RuntimeError as error:
    assert 'inputs changed' in str(error)
    assert not output.exists()
cases.append({'name': 'during-compile-change', 'rejected': True})
compile_case('retry-after-input-change', False)
def builder_function(text, directory):
    directory.mkdir()
    tree = ast.parse(text)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'compile_one')
    namespace = {'build': directory, 'here': work, 'common': ['-O2'],
                 'hashlib': hashlib, 'run': run, 'compile_object': cache.compile_object}
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<actual SDK builder function>', 'exec'), namespace)
    return namespace['compile_one']
current = builder_function((root/'tools/adobe-validator/build.py').read_text(), work/'current-builder')
previous_source = subprocess.check_output(['git', 'show', 'd9fa10c:tools/adobe-validator/build.py'], cwd=root, text=True)
previous = builder_function(previous_source, work/'previous-builder')
current_object, old_object = current((source, [])), previous((source, []))
current_hash, old_hash = cache.digest(current_object), cache.digest(old_object)
stamp = inner.stat()
inner.write_text('#define VALUE 20\n')
os.utime(inner, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
assert cache.digest(current((source, []))) != current_hash
assert cache.digest(previous((source, []))) == old_hash
cases.append({'name': 'actual-builder-transitive-header', 'current_rebuilt': True,
              'previous_retained_stale_object': True,
              'previous_function_sha256': hashlib.sha256(previous_source.encode()).hexdigest()})
print('PASS actual builder and previous stale-cache negative', flush=True)
receipt = {'scope': 'Real clang compilation and object/depfile readback of owned original C; no SDK link/load/runtime',
           'workspace': str(work), 'cases': cases, 'commands': calls,
           'sources': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [root/'tools/adobe-validator/object_cache.py', root/'tools/adobe-validator/build.py', Path(__file__)]}}
(work/'RESULT.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('Receipt:', work/'RESULT.json')
