"""Metadata-only historical evidence binding; never opens media or runs tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re

SHA = re.compile('[0-9a-f]{64}')
SOURCE_SUFFIXES = ('.ml', '.mli', '.c', '.h', '.ox.mli.in')


def source_relative(name):
    if not isinstance(name, str):
        return None
    if name.startswith('src/'):
        relative = name
    elif '/src/' in name:
        relative = 'src/' + name.rsplit('/src/', 1)[1]
        # A checkout under ~/src does not turn its tests/tools into production.
        if any(part in ('tests', 'tools', 'bench', 'doc') for part in Path(relative).parts[1:-1]):
            return None
    else:
        return None
    if relative == 'src/ubase/projectInfo.ml':
        return None  # Build-generated version metadata, absent from source inventory.
    path = Path(relative)
    if '..' in path.parts or not (name.endswith(SOURCE_SUFFIXES) or path.name in ('Makefile', 'Makefile.OCaml', 'dune')):
        return None
    return relative


def bindings(value):
    """Only explicit path/SHA pairs, including artifact records; no prose inference."""
    found = set()
    if isinstance(value, dict):
        for name, digest in value.items():
            path = source_relative(name)
            if path and isinstance(digest, str) and SHA.fullmatch(digest):
                found.add((path, digest))
        path = source_relative(value.get('path'))
        digest = value.get('sha256')
        if path and isinstance(digest, str) and SHA.fullmatch(digest):
            found.add((path, digest))
        for child in value.values():
            found.update(bindings(child))
    elif isinstance(value, list):
        for child in value:
            found.update(bindings(child))
    return found


def compare(root, value):
    rows = []
    for name, recorded in sorted(bindings(value)):
        path = root / name
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        rows.append(dict(path=name, recorded=recorded, current=current,
                         status='MATCH' if current == recorded else 'CHANGED' if current else 'MISSING'))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('receipts', nargs='+', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = dict(schema='unison-acceptance-source-bindings/2',
                  scope='Explicit keyed production-source bindings only; no test rerun, implicit artifact traversal, automatic adoption or completion claim. Zero bindings means unbound, never current. Multiple historical versions remain distinct.',
                  entries=[], goal_complete=False)
    for path in args.receipts:
        raw = path.read_bytes()
        value = json.loads(raw)
        rows = compare(root, value)
        result['entries'].append(dict(receipt=str(path), sha256=hashlib.sha256(raw).hexdigest(),
            bindings=rows, counts={status:sum(r['status']==status for r in rows)
                                  for status in ('MATCH', 'CHANGED', 'MISSING')},
            status='NO_DIRECT_BINDINGS' if not rows else 'ALL_DIRECT_BINDINGS_MATCH'
                   if all(r['status']=='MATCH' for r in rows) else 'HISTORICAL_OR_MIXED_SOURCE_BINDINGS'))
    if args.output.exists():
        parser.error('audit output must be a fresh immutable path')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    for entry in result['entries']:
        print(entry['receipt'], entry['status'], entry['counts'])


if __name__ == '__main__':
    main()
