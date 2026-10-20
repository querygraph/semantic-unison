# Optional all-scanned validation

The default remains `adobevalidate = off` and `adobevalidatescope = received`.
With an already configured qualified driver, executable SHA and build identity,
request unchanged-file checking explicitly:

```text
adobevalidate = require
adobevalidatescope = all-scanned
```

Both replicas must negotiate `dng-validation-all-scanned-v1`. An active request
fails explicitly with an incapable peer, including after late preference
installation. Off does not require this capability. Scope values are strict;
only `received` and `all-scanned` are accepted. No wire/archive format is changed.
Driver/limiter configuration remains endpoint-local, as for receiving validation.

The scan collects selected regular files, including unchanged and immutable
files, while retaining ignore, name-conflict and follow rules. Watcher hints and
directory shortcuts cannot remove requested validation coverage. Immutable update
results retain their previous semantics. A scan error or limit overflow rejects
the phase rather than reporting partial coverage. Both endpoint promises drain
before a failed scan returns.

Policies/tool callbacks are captured once per endpoint phase before enumeration.
Recognizers independently select active companions; the default registry has only
the DNG companion. Other explicitly enabled compiled companions can participate
in the common phase; this setting enables no additional companion automatically.
Nonmatching files receive bounded recognition and avoid snapshot materialization/full hashing.
Suffix claims and indeterminate recognition still require validation independently
of semantic-transfer eligibility.

Matching originals are opened read-only and copied/cloned into fresh0700 staging
under the local Unison state directory, outside the supplied local replica roots.
No pathname helper receives a live unchanged original. Staging ancestry checks
use canonical paths and ancestor inode identity; namespace fences are cooperative,
not a hostile-same-UID or arbitrary mount-topology sandbox. Followed paths are
resolved without changing process CWD and checked before/after each file. Stage
hash/name checks reject helper mutation. Private stages/directories retire only
after actual callback/worker/helper settlement; unrelated entries/replacements are
never recursively deleted. Cleanup failure preserves the original cause.

Candidate inspection borrows the stage owner's descriptor. Separate read-only
artifact owners allow driver/limiter hashes, while original-inode aliases are
refused. An uncertain temporary close keeps its identity, original failure and
resource loan pending without numeric retry. Other legacy worker/IO-wrapper
close-fault limitations are not claimed as universally fixed.

The positive structural limits are:

| Preference | Default | Meaning |
| --- | ---: | --- |
| `adobevalidatescanfiles` | 65536 | All selected regular files retained before recognition, including non-DNG files |
| `adobevalidatescanpathbytes` | 16777216 | Cumulative retained endpoint-local pathname bytes |
| `adobevalidatescanmaxmib` | 4096 | Per-matching-file private snapshot size, checked before materialization |

These are structural/per-file limits, not whole-process RSS or total physical IO
caps. Existing shared backend/worker admission still applies. Warn explicitly
permits validator findings with a warning; source instability, mutation,
incomplete coverage, cancellation and unresolved ownership remain failures or
retained work. No-op syncs revalidate only when all-scanned is explicitly active.

Current qualification uses generated private roots, local scan RPCs and original
fake protocol helpers. Their independent candidate SHA checks and process/group
bindings exercise the real driver invocation path, including driver inspection;
they are not Adobe decode/raw-digest or pixel evidence. Real SDK all-scanned,
actual remote-process peer combinations, live watcher and broader platform/corpus
qualification remain open. The full SEMANTIC-UNISON-DESIGN.md goal is incomplete.

For explicit qualification, `-debug validation-input` records the owner context's
candidate pathname as bounded raw-byte hex, candidate hash/size, helper PID and
whether it borrowed an unchanged-file stage output. The record is emitted only
after supervised execution returns. Paths longer than4096bytes are explicitly
unavailable; they are not silently truncated into apparently complete evidence.
Normal debug-off operation emits none of these paths. This is an owner observation,
not an OS argv trace or hostile same-user sandbox guarantee.

Current007 stock/Ox Make+Dune builds and actual generated scan/fake-helper
records pass [current qualification](../tests/qualification/all-scanned-input-current-actual-20261017.json).
The prospective SDK auditor joins helper identity to the endpoint-owned stage
path and refuses paths inside replicas, mismatched owner PIDs and unborrowed
inputs. No actual SDK or remote-process all-scanned run is inferred.
