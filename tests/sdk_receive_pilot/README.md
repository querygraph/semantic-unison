This finite pilot links unchanged, compiler-matched production ML objects and
recompiles **only** the helper C stub with the existing test-only inherited-group
backend. It does not modify installed Unison, SDK binaries, photos or Lightroom.
It qualifies functional receiving/lifecycle, not production-C-backend timing.

Default `--mode prepare` builds two private CLIs and copies seven original/generated
inputs into a new owned workspace. It performs no SDK calls. Required arguments:

```sh
python3 tests/sdk_receive_pilot/run.py \
  --stock-build /absolute/stock-Make-receipt.json \
  --ox-build /absolute/Ox-Make-receipt.json \
  --sdk-result /absolute/accepted-sdk-v2-result.json \
  --fixtures /absolute/accepted-pilot/fixtures \
  --driver-manifest /absolute/qualified-driver/build-manifest.json \
  --workspace /private/tmp/unique-owned-receive-preparation
```

Only the pinned, previously accepted v2 fixture result is supported. Original
fixture hashes and driver pin are checked. SDK linking/loading is not part of
preparation. Link inputs are pinned before/after private relinking. A different
SDK/corpus requires a separately reviewed successor, not bypassing these checks.

`--mode mock` uses another fresh workspace and an original fake tool, never the
SDK. Six actual stock→Ox/Ox→stock receives use SDE on uncompressed/JPEG/JXL DNGs.
One bad raw-digest-tag update must be rejected with live destination preserved.
Three original-input calls complete ten mock entries. Returned original receipts,
entry multiplicities/group bindings, byte equality and aggregate closure must pass.
Independent controls run with:

```sh
python3 tests/sdk_receive_pilot/guard_test.py
python3 tests/sdk_receive_pilot/admission_test.py
```

The guard refuses wrong group, wrong tool hash, unlisted bytes and an eleventh
call before tool entry, even under Python optimization. Admission tests are pure:
no subprocesses, SDK or native execution. An entry marker alone proves neither
exec nor success. A successful pipeline also needs bound tool receipts, Unison's
precommit validation result, exact output and genuine terminal group closure.

Native execution is **not released by a preparation or mock receipt**. It requires
`--mode native --request /absolute/pinned-request.json --admission
/absolute/fresh-Root-admission.json`, reusing an untouched build-only workspace.
The admission must bind the exact absolute-interpreter command, immutable request
and READY pins, fresh deadline and exact limits. Old SDK/preview admissions and
consumed/unresolved workspaces refuse. START is exclusive and created only inside
the established owned phase, before the first SDK entry. No automatic retry.

The proposed native bounds are ten SDK calls (3 original positives +6 mixed
receives +1 rejected bad-digest update), seven input states, sixteen logical states
(3 direct originals +6 baselines +6 edited receives +1 negative update), and one
300-second aggregate covering copies/hashes/receives/SDK calls and cleanup. Each
endpoint has one semantic permit; reserve **8 host CPU credits** conservatively
for both admitted pipelines plus legacy owner hashing and orchestration headroom.
This is planning headroom, not a proved whole-process CPU/RSS ceiling. Helpers
remain single-threaded. No benchmark, Lightroom, Photo, cache or Main operation.

`AGGREGATE-CLOSED.json` must prove reaped/other-members-absent/within-wall and exit0
for a pass. Cleanup ambiguity retains the unresolved marker. The trusted tools
must not escape groups; kernel stalls/killing the outer owner are outside the
existing supervisor guarantee. The caller must retain its actual parent tool
handle and obtain its terminal exit separately. `SUPERVISOR-RETURN.json` explicitly
is **not** a parent terminal-exit receipt. Root holds any reservation until actual
parent closure and pinned results are returned.

Underlying SDK and prepared inputs must stay stable throughout the slot. File
pins are rechecked, but this is not atomic execution against an adversarial
same-UID namespace writer. Native receive validation does not qualify standalone
rendering, camera corpus, cache reuse, single-large-file parallelism or full M4-V/M6.
