# Managed component metadata store

This successor composes the existing namespace, monotonic quota, authenticated
capture and manifest publication APIs. It remains endpoint-local, default-off
metadata; it does not supply reconciliation or peer trust.

`prepare_managed_cache_store` authenticates the checkpoint against its owner
entry and freezes an immutable compare-and-replaced index before touching the
namespace. `execute_managed_cache_store` opens the supplied identity-bound
namespace ticket, prepares the fixed quota, reserves one 2MiB slot and exclusively
creates record and entry stages. It stages and independently authenticates both,
retires the borrowed inspection readers, publishes the record then entry, and
normally closes both owned stages. It next creates, authenticates and publishes
the manifest, closes that stage, and closes the namespace. Only after all these
scopes return can `managed_cache_store_reference` or `_index` succeed.

False means reservation exhaustion. Every error consumes the store ticket and
preserves actual stage creations, reservation slots and published orphans. There
is no overwrite, unlink, refund, fallback, retry or implicit recovery. Native stage
opens immediately return ownership without post-open allocating operations.
Descriptor close uncertainty uses the loader's qualified carrier, preserves known
outer descriptors and borrowed ancestors, and never retries a numeric FD.
Published effects are observable independently of completion; a renamed object
or successful callback is not adoptable ownership evidence.

`Update.adopt_component_cache_store` compares the currently loaded archive hint
against an explicit expected reference, requires a normally settled store, and
changes only in-memory properties. The owner must serialize root access and use
the normal archive commit. A changed head refuses without replacing it; its
already-published metadata remains an orphan. No trusted namespace identity is
implicitly discovered, and no automatic report-path activation is supplied yet.

The 2MiB charge bounds admitted encoded record+entry+manifest payload per capture,
not filesystem overhead, RSS or physical disk allocation. Cooperating owners must
preserve configuration/reservations, exclusively own the supplied parent and
namespace, and coordinate IO/CPU ownership separately. Same-UID hostile mutation,
power-loss recovery and non-macOS native publication are not qualified here.

Qualification uses original tiny fixtures, copied fault objects and real native
publication objects. See the versioned actual receipts and OPUS-HANDOFF.md;
normal-path success does not establish failure-path or full integrated coverage.
