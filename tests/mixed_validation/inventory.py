"""Exact current mixed execution/source inventory; no helper or media access."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def paths():
    files=set((ROOT/'tests/mixed_validation').glob('*.py'))
    files.add(ROOT/'tests/mixed_validation/probe.ml')
    files.update(ROOT/'tests'/name for name in ('shared_cpu_pool.py','shared_io_pool.py',
                  'shared_process_owner.py','shared_dispatch.py','manual.py'))
    files.update(ROOT/'tests/sdk_host_matrix'/name for name in ('shared_binding.py','shared_child.py'))
    files.update(ROOT/'bench/sync'/name for name in ('ownership.py','measure.py'))
    files.update(ROOT/'tests'/name for name in ('private_camera_receiving/close.py',
                  'sdk_multifile/clone.py','camera_sdk_concurrency/persistence.py',
                  'supervised_external/external_records.py'))
    # Bind production sources used by the compiled probe, including interfaces
    # and build descriptions. This does not itself authenticate a build receipt.
    files.update(p for p in (ROOT/'src').rglob('*') if p.is_file() and
                 (p.suffix in ('.ml','.mli','.c','.h','.S','.in') or p.name.startswith('Makefile')))
    return tuple(sorted(files))


def verify(plan,*,checker=None):
    from mixed_validation.artifacts import verified_hash
    checker=checker or verified_hash
    rows=plan['source_pins']
    if len(rows)!=len(paths()) or {item['path'] for item in rows}!={str(p) for p in paths()}:
        raise ValueError('exact current mixed source inventory required')
    for item in rows:checker(item)
