# Live SDK-gated scalar merge receiving: next finite test

Preparation and lifecycle design; no SDK admission or native dispatch is supplied
by this document. A source-matched preparation tool now freezes the twelve states;
the runtime executor and its finite failure controls remain to be implemented. The previous three-call admission is consumed and cannot be
reused. Photo Root retains native-slot coordination and preview ownership.

The current production stock/Ox merge controls produce the same frozen target
bytes that the SDK accepted independently. What remains untested is the exact
production per-file SDK gate during a two-receiver scalar merge. The next test
must use current, source-matched production binaries and their ordinary helper
spawn behavior, not a private C backend compiled to keep helpers in one group.

Use three retained generated inputs (uncompressed, JPEG, JPEG XL), never source
photos. Derive the already-qualified fixed-size base/left/right/target XMP
variants, verifying all bytes outside the XMP extent against the original.
Each codec has four logical states: base, left edit, right edit, merged target.
The proposed finite maximum is 3 inputs, 12 logical states, 6 SDK calls, four
configured endpoint CPU credits and a 300-second aggregate. Seed with validation
off; then require validation for the disjoint merge and its no-op. Each codec
must invoke the SDK exactly once on each receiving endpoint; seed and no-op
invoke it zero times. No negative native cases, generation, retry or benchmark
is included. This budget is a proposal, not a reservation.

Run stock client/Ox server so both receiving implementations participate. Reuse
one-thread qualified SDK v1 with endpoint-local executable/hash/build settings;
no experimental allocator/task-host activation. Keep merge-cache capture, exact
verification, properties, final publication and archive paths unmodified. Compare
both final replicas to the independently SDK-accepted target hashes; retain old
input witnesses and verify no-op bytes/inodes and staging cleanup. This does not
claim pixel equality, camera-corpus coverage or renderer correctness.

## Ownership prerequisite

`bench/adobe/phase.py` explicitly assumes contained helpers. Production
`HelperSupervisor` uses `POSIX_SPAWN_SETPGROUP`, normally creating a separate
group per helper. Therefore absence of other members in the aggregate group
cannot establish closure of this proposed production-path test.

Before any native admission, implement and exercise an owner ledger for those
helper groups. A test-only pinned validator proxy may record its owned PID/group
before dispatch, invoke the pinned SDK in that same helper group, retain bounded
raw stdout/stderr, and pass the exact protocol back to Unison. It must reap its
SDK child and retain each child terminal/capture receipt. Such a proxy adds
measurement overhead and does not qualify production timing. Do not change
production group creation merely to simplify this test.

The outer owner must keep cleanup responsibility for every registered helper
group through Unison timeout/cancellation/exit and the independent SDK capture
owner's terminal. A PID whose child has already been reaped must never be
signaled later solely because its integer appears in a stale file. Specify
registration-to-dispatch and process-exit-to-retirement handshakes, including
what remains held on partial ledger publication. If ownership cannot be proved,
retain an unresolved marker and the coordination hold; elapsed time or a single
`ps` absence is not a release. No automatic retry after ambiguous dispatch.

Qualify the ledger/proxy with original fake SDK children before requesting a
native slot: normal return, rejection, stdout/stderr bounds, hanging child,
term-ignoring child, proxy failure before/after child launch, and outer-owner
cancellation. Each case must account for its actual parent terminal, SDK child
reap, registered group closure and preserved input/output sentinels. This is a
finite deterministic lifecycle suite, not a fuzz/sanitizer campaign.

Only after that prerequisite passes should a pinned request bind exact source,
binaries, input variants, trusted proxy/SDK, unique workspace, call/state limits
and an explicit fresh Root deadline. Return START promptly, then actual parent
terminal, every raw SDK protocol/entry/capture receipt, exact output hashes,
all helper/aggregate closure evidence and unresolved-marker audit. Root's
independent acceptance is separate from the owner result.

The first implemented diagnostic foundation is `HelperSupervisor.result.child_pid`:
it retains the spawned direct child's historical PID beside the supervisor's
actual wait status. [Stock/Ox qualification](../tests/helpers/child-pid-qualification.json)
covers actual identity/status binding, direct-child reap, timeout identity,
pre-spawn cancellation and spawn failure without fabricated identity, plus the
existing helper suite. This result is not a retained PID reservation, group
absence certificate or registration-before-dispatch journal. The ledger and
its failure/capture ownership controls above remain required before this native
receiving test is ready.

A tested alternative foundation to the external proxy ledger now exists:
[spawn-bound native group observations](../tests/helper_group_observation/README.md)
can use the supervisor's existing retained direct-child owner instead of
changing process groups. The opaque binding is prepared before spawn, authenticates
group assignment at successful native spawn, and permits a kernel membership
observation before the real owner reaps. This addresses the discovered Darwin
zombie `getpgid` limitation. It is now integrated into HelperSupervisor and opt-in validation-group diagnostics.
[Current stock/Ox qualification](../tests/validation_process/group-integration-qualification.json)
covers both full builds/selftests,41 helper groups per compiler and five actual
receiving diagnostic cases per compiler. Bindings retire before every reap/lost-
child path; unknown and unobserved remain distinct. This replaces the proposed
proxy ledger for observing normal retained helper groups, without introducing a
proxy or changing production groups. It does not supply an outer executor's
failure/cleanup contract: that executor must refuse successful closure when a
required helper observation is missing, unknown or nonzero, preserve unresolved
ownership after ambiguous interruption, and never signal reaped historical PIDs. Completed diagnostic PID integers remain insufficient.

## Frozen live-merge preparation

`tests/sdk_container_receive/prepare_live_merge.py` verifies the prior closed
three-codec SDK return and artifact pins, current stock/Ox build/selftest/source
pins, original inputs and SDK-accepted merged target bytes. It reconstructs only
the fixed-width Rating/Label values within the exact XMP extent and freezes four
read-only states per codec in a fresh private directory. All bytes outside XMP
are checked against the original. Each base and target hash matches both prior
merge implementations. This does not assert SDK qualification of base/left/right.

[Preparation evidence](../tests/sdk_container_receive/live-merge-preparation-qualification.json)
records the actual pure run and eight malformed/protected-byte controls. No SDK
call occurred; the proposed six-call runtime is still unadmitted and its executor
is not implemented. Production-path group ownership during failure remains a
requirement of that executor, not proof supplied by a prepared packet.
