"""Owner-enumerated first-party inventories; metadata only, not a runtime grant."""
from pathlib import Path
from sdk_merge_receiving.plan import require
from sdk_negative_receiving import inventory as negative
from current_validation_paths.admission import REPOSITORY,LEGACY

EXTRA=('tests/clone_interruption_transport.py','tests/supervised_external/external_records.py',LEGACY)


def production():return negative.production()


def execution():
    root=Path(REPOSITORY)
    names=negative.execution()
    names.extend(str(p.relative_to(root)) for p in (root/'tests/current_validation_paths').glob('*.py'))
    names.extend(EXTRA)
    require('tests/current_validation_paths/entry.py' in names,'named native entry missing')
    return sorted(set(names))
