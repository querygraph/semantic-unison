# Local async semantic transaction ownership

Production local async materialization now prepares a pair ledger, a single-source
ledger, original-error slot, interrupted error and owner/scope links before cloning
or opening source. Each returned handle is adopted before allocating a list,
registry record or callback wrapper. Legacy names become owned only after actual
creation. Scope metadata is prepared for both bound and legacy async paths.

Every independent close slot is attempted once, including source after a pair
failure. Uncertain close preserves original error plus separate pair/source causes
and pre-close evidence, roots transaction/name metadata, and blocks name removal
and ordinary reservation retirement. Known-close inventory excludes uncertain,
closed or native-transferred FD numbers; diagnostic handles are not retry authority.
A post-acquisition interruption retains new handles instead of continuing work.

Bound publication prepares the abstract parent handoff and owner before handle
acquisition. Cleanup reads the actual native acknowledgement: unconsumed parent
closes locally once; consumed parent is owned by native code, not declared closed.
Raw pair/source closure precedes native abort/name removal. Any raw uncertainty
blocks that abort. Native uncertainty retains its context and transaction. A null
native-exception diagnostic is not proof there is no retained prepared context.

Worker jobs and the complete synchronous producer call share the borrowed lifetime.
The producer can run an inner event loop, so connection cleanup must only mark
abandonment while it remains active. After callback returns, known cleanup may
close handles and abort the owned name. Recognized nested uncertainty preserves
all descriptors and stage bytes, leaving the transaction pending. Original
producer exceptions remain terminal and must not become ordinary copy fallback.

## Actual checkpoint — 2026-10-18

Evidence: tests/qualification/local-transaction-owner-actual-20261018.json.
Stock/Ox Make and Dune builds+selftests pass on329 production source hashes.
Both compilers pass37 directed actual async cases each (14 legacy,23 bound),
including raw/source/parent failures before and after settlement, registration,
opening, interruptions, native preentry rejection and callback connection cleanup.
A nested real typed close carrier retains the producer's pair/source/name; a
close-swallowing participant fails the designated assertion under both compilers.
Known paths restore FD census; uncertain fixture resources settle at process exit,
not by a claimed normal native teardown. All test groups/CPU scopes closed.

Eight original native publication cases pass. Callback-failure cleanup now proves
raw pair/source known closed before a separate native-abort close uncertainty;
other uncertain native stages retain their still-held raw handles. The64 actual
handoff regressions (32/compiler) exercise final-publication witness adoption,
original callback errors, namespace replacement/rebind sentinels, registration/
unregistration failures, unsupported/ineligible fallback, deferred borrowed cleanup
and FD-number reuse. Constructor hooks use the new prepared owners, not old
allocating raw descriptor lists. Remote planner delivery is in-process, not actual
transport. All inputs are original8192B synthetic DNGs; no SDK/Photo/camera or EXIO.

## Remaining scope

This checkpoint covers production local async transfer, not the synchronous test
reference, compact-base capture or scalar merge's independent raw descriptors.
The remote producer subsequently received separate event-loop/callback lifetime
qualification; see remote-producer-lifetime.md. That later directed proof is not
retroactively inferred from this checkpoint's successful remote handoffs. Current
remaining ownership inventory is the immutable v3 successor.

Merge-cache directory/quota/record/temp-name ownership needs a joint successor;
do not independently root a directory while dropping its outer quota/borrower.
Aggregate descendant FD/RSS and complete acquisition accounting, wider benchmark
matrix and final consolidated integration remain open. Native tracked component
qualification is not a blanket guarantee for every caller or unsupported platform.
