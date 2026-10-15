#!/usr/bin/env python3
"""Pure refusal controls; deliberately no owned child/CLI/native invocation."""
from pathlib import Path
import tempfile
import time
import live_merge_owner as owner

work = Path(tempfile.mkdtemp(prefix='unison-live-owner-pure-'))
r = owner.Runner(work, time.monotonic() + 300)
assert r.marker.exists()
for count in (0, 8, 10):
    r.calls = count
    try:
        r.accept_complete_proofs([])
    except ValueError:
        pass
    else:
        raise AssertionError('incomplete proof cleared marker')
    assert r.marker.exists()
r.calls = 9
results = [{'codec': codec, 'receipts': []} for codec in owner.prep.CODECS]
try:
    r.accept_complete_proofs(results)
except FileNotFoundError:
    pass
else:
    raise AssertionError('missing real CLI receipts cleared marker')
assert r.marker.exists() and not (work / 'HELPER-PROOFS-COMPLETE.json').exists()
# Both pre-dispatch limits must refuse without calling OwnedGroup at all.
for count, deadline in ((9, time.monotonic() + 300), (0, time.monotonic())):
    r.calls, r.deadline = count, deadline
    try:
        r.run_sync(['/NEVER-EXECUTE'], {}, work / 'never.log')
    except RuntimeError:
        pass
    else:
        raise AssertionError('pre-dispatch limit failed')
assert not list(work.glob('CLI-*-START.json'))
print('PASS incomplete/missing closure and pre-dispatch limit refusals; no child created; retained marker', r.marker)
