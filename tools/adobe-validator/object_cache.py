"""Content-checked native object cache; no SDK imports or runtime invocation."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dependencies(path):
    text = Path(path).read_text().replace('\\\n', '')
    # Clang emits one escaped Make target followed by colon/whitespace. Colon
    # inside an ordinary pathname is not itself the rule separator.
    separator = next((i for i, char in enumerate(text)
                      if char == ':' and i + 1 < len(text) and text[i + 1].isspace()
                      and (i == 0 or text[i - 1] != '\\')), None)
    if separator is None:
        raise ValueError('invalid compiler dependency rule')
    names = shlex.split(text[separator + 1:], comments=False, posix=True)
    if not names:
        raise ValueError('empty compiler dependencies')
    return sorted(set(str(Path(name.replace('$$', '$')).resolve()) for name in names))

def compile_object(compiler, options, source, output, run):
    compiler = shutil.which(str(compiler))
    if compiler is None:
        raise FileNotFoundError('native compiler unavailable')
    compiler = str(Path(compiler).resolve())
    output, source = Path(output), Path(source).resolve()
    depfile, record = output.with_suffix('.d'), output.with_suffix('.inputs.json')
    command = [compiler, *map(str, options), '-MD', '-MF', str(depfile),
               '-c', str(source), '-o', str(output)]
    identity = {'command': command, 'compiler_sha256': digest(compiler),
                'environment': {key: os.environ.get(key) for key in
                    ('CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'OBJC_INCLUDE_PATH',
                     'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'CCC_OVERRIDE_OPTIONS')}}
    try:
        saved = json.loads(record.read_text())
        if (saved['identity'] == identity and saved['object_sha256'] == digest(output)
            and saved['dependencies'] == {name: digest(name) for name in dependencies(depfile)}):
            return output, True
    except (OSError, ValueError, KeyError, TypeError):
        pass
    run([compiler, *map(str, options), '-M', '-MF', str(depfile),
         '-MT', str(output), str(source)])
    before = {name: digest(name) for name in dependencies(depfile)}
    run(command)
    names = dependencies(depfile)
    if str(source) not in names:
        raise ValueError('compiler dependencies omit the source')
    after = {name: digest(name) for name in names}
    if before != after or digest(compiler) != identity['compiler_sha256']:
        output.unlink(missing_ok=True)
        raise RuntimeError('native build inputs changed during compilation')
    saved = {'identity': identity, 'dependencies': after,
             'object_sha256': digest(output)}
    # An interrupted object/receipt write cannot become a valid cache hit.
    with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(saved, stream, indent=2)
            stream.write('\n')
            stream.close()
            os.replace(temporary, record)
        finally:
            temporary.unlink(missing_ok=True)
    return output, False
