"""Owner-enumerated first-party inventories; metadata only, not a runtime grant."""
from pathlib import Path
from sdk_merge_receiving.admission import REPOSITORY
from sdk_merge_receiving.plan import require

SUPPORT=(
 'tests/shared_cpu_pool.py','tests/shared_io_pool.py','tests/shared_process_owner.py',
 'tests/shared_dispatch.py','tests/sdk_host_matrix/shared_child.py',
 'tests/sdk_host_matrix/shared_binding.py','tests/cached_benchmark/contract.py',
 'tests/private_camera_receiving/close.py','tests/sdk_multifile/clone.py',
 'tests/camera_sdk_receiving/sdk_audit.py','tests/validation_process/records.py')


def execution():
    root=Path(REPOSITORY)
    names=[str(p.relative_to(root)) for p in (root/'tests/sdk_merge_receiving').glob('*.py')]
    names += [str(p.relative_to(root)) for p in (root/'bench/sync').glob('*.py')]
    names += list(SUPPORT)
    require('tests/sdk_merge_receiving/entry.py' in names,'native owner entry missing')
    return sorted(set(names))


def production():
    root=Path(REPOSITORY)
    names=sorted(str(p.relative_to(root)) for p in (root/'src').rglob('*')
        if p.is_file() and (p.suffix in ('.ml','.mli','.c','.h')
            or p.name in ('Makefile','Makefile.OCaml','dune','dune-project')
            or p.name.endswith('.ox.mli.in')))
    require({'src/semanticRuntime.ml','src/semanticWorkers.ml','src/semanticMergeCache.ml'}<=set(names),
            'complete production runtime/worker/cache inventory required')
    return names
