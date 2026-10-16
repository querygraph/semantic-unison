"""Compile exact inspector JSON helpers; independent UTF-8/JSON decoding oracle."""
import argparse
import codecs
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ocamlopt', required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
source = Path(__file__).with_name('inspect.ml')
text = source.read_text()
helpers = text[:text.index('let category =')] + text[text.index('let path_fields '):text.index('let report ')]
cases = [bytes([i]) for i in range(256)] + [
    b'', b'quote"slash\\\n', 'é漢字😀'.encode(), b'\xc0\xaf', b'\xed\xa0\x80',
    b'\xf4\x90\x80\x80', b'\xf0\x9f', b'a\xffb', b'\xe2(\xa1',
    b'\xf4\x8f\xbf\xbf', b'\xe0\xa0\x80', b'\xc2\x80',
]
codecs.register_error('inspector_byte_escape', lambda e: (e.object[e.start:e.end].decode('latin1'), e.end))
def literal(value):
    return '"' + ''.join('\\%03d' % byte for byte in value) + '"'
w = Path(tempfile.mkdtemp(prefix='unison-inspector-json-'))
(w/'control.ml').write_text(helpers + '\nlet () = List.iter (fun s -> print_endline (object_ (path_fields s))) [' + ';'.join(map(literal,cases)) + ']\n')
subprocess.run([a.ocamlopt, 'control.ml', '-o', 'control'], cwd=w, check=True, timeout=30)
r = subprocess.run([str(w/'control')], capture_output=True, check=True, timeout=10)
lines = r.stdout.decode('utf-8', errors='strict').splitlines()
assert len(lines) == len(cases)
for raw, line in zip(cases, lines):
    value = json.loads(line)
    assert value['path'] == raw.decode('utf-8', errors='inspector_byte_escape'), raw
    assert bytes.fromhex(value['path_bytes_hex']) == raw, raw
(w/'stdout.jsonl').write_bytes(r.stdout)
a.report.write_text(json.dumps({'passed':True,'cases':len(cases),'source':str(source),
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'compiler':a.ocamlopt,
    'workspace':str(w),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),
    'scope':'exact JSON helper compile; no inspector input, SDK, Photo or sync'},indent=2)+'\n')
print('PASS',len(cases),'JSON/UTF-8/path-byte cases',flush=True)
