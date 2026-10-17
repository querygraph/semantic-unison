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


## Remaining report-owner integration

Current `SemanticRemote.inspect_components` still calls `SemanticWorkers.components`
without checkpoint capture or cache selection. It precedes Update in the module
dependency graph; importing Update there would create a cycle. The next route
must pass an explicit endpoint-owner context from the loaded archive owner (or
register a narrow owner-loop hook), never infer authority from a self-hashed
manifest or a directory found on disk.

Persist namespace identity as an optional archive-owned extension bound to the
same archive context and manifest reference. An old archive without that identity
must remain a cold miss. Missing/corrupt optional metadata must not reset the
ordinary archive or mutate synchronization state. Provision a namespace only
under a private owner-state parent after the owner has explicitly selected this
feature; normal reading must use an existing identity-bound namespace ticket.
Retain compatibility with old code dropping optional hints on rewrite.

Do not hold synchronous namespace callbacks over an asynchronous worker await.
Load bounded index/record bytes under scoped owned descriptors, close normally,
run the worker with immutable authenticated inputs, then independently reopen
with the exact namespace identity to stage any new capture. Check the source
snapshot and expected archive head again before adoption. A corrupt selected
record is a reported failure, not a silently fresh extraction. Unchanged captures
must reuse the existing immutable objects rather than collide on exclusive
publication; missing/stale selections may capture new metadata within quota.
Unknown descriptor ownership must propagate past report error formatting, retain
the resource owner, and never become an ordinary unavailable-report release.

The report may expose reused/invalidated component counts and refinement versions,
with exact opaque coverage preserved. It must not call logical reuse physical IO
savings: current restore still verifies the full input. Remote endpoints need the
same owner-local lifecycle; cache authority is never transferred over the existing
small component-summary wire response.


## Archive-owned namespace identity successor

The optional UAN/0 tail follows UAX/0 without changing archive format23 or
legacy serialized properties. Its fixed152 bytes are magic8, archive-context32,
owner-binding32, manifest-digest32, unsigned device8, unsigned inode8 and body
SHA25632. Values outside the host integer range, wrong head/context, malformed
framing or checksum return no namespace identity. This checksum authenticates
framing against a trusted loaded archive, not an untrusted standalone file.

Successful managed-store execution retains the namespace identity it actually
used. Archive adoption copies that identity and manifest reference together only
after normal descriptor settlement and expected-head comparison. The older raw
manifest setter clears any previous namespace identity; clearing a hint clears
both. Old optional-hint archives still load with no identity. The namespace key
is stripped from the legacy property payload, so older code need not recognize
it; old writers may drop optional tails on rewrite. Actual retained-old-code
compatibility for this new tail is still a separate validation item.

Report routing must treat absent namespace identity as cold metadata, not discover
or trust whichever directory currently occupies the expected name. The parent
path remains selected by the endpoint owner, never the peer. A valid archived
identity still requires fresh private-parent/name/descriptor checks on each open.


## Endpoint-owner orchestration source

`Update.inspect_cached_components` now implements the scoped-load / immutable
worker / guarded-capture flow. The caller supplies the already owned private
parent, current source descriptor/path, root and generation. Legacy hints without
identity take the ordinary fresh-worker path without touching that parent. A
selected manifest missing on disk is incomplete metadata, not a silently empty
index. An unchanged owner entry skips exclusive publication. Replacement uses the
prior exact key's digest even when generation selection was stale; the new worker
result still requires current-input parsing and hashing.

This is an explicit owner API, not yet the default `SemanticRemote`/UI route.
The caller must provide outer memory/IO admission and descriptor lifetimes, plus
a later normal archive commit. Generation selects a candidate; it does not prove
bytes unchanged. Current worker refresh performs full-input verification. Source
FD/path observations and loaded-head comparison are repeated before publishing.
Report observations and cache-hint mutation never change common-file authority.


Cancellation is checked before any cache parent access and again after worker
reply, before capture/adoption. Submitted-job cancellation returns no report result
and preserves the old cache head; native worker settlement still occurs through
its existing lifecycle. A concurrent owner-head change is refused even when the
returned capture would otherwise be unchanged. Controls schedule those changes
between submission and owner-loop completion. Worker read observers run after
reply delivery and are unsuitable as a before-reply race injection point.


## Explicit asynchronous parent owner source

`open_cache_parent` opens only an existing explicitly selected absolute directory
with native no-follow/nonblocking/CLOEXEC flags, records ownership before identity
validation, and checks final-path/descriptor private0700 ownership and identity.
`cache_parent_descriptor` borrows it and repeats the path check. There is no
finalizer, recursive discovery, mkdir, IO admission or implicit source access.

The caller must invoke `settle_cache_parent` once after all async work stops.
Normal settlement closes once. An ordinary original error is rethrown after a
normal close; a close error instead carries its uncertain descriptor and original
cause. Nested cache uncertainty transfers this still-known parent into the same
retained descriptor carrier without closing it. Subsequent settlement attempts
are refused in both cases. This explicitly separates lifetime ownership from
synchronous namespace reader callbacks.


## Opt-in local report entry source

The UI component-details branch now calls
`SemanticRemote.observe_components_with_worker` with
`Update.inspect_configured_components` as its local worker. The original
`observe_components` API remains intact; remote roots ignore the local callback
and retain their existing bounded protocol. Remote endpoint cache routing is not
claimed by this local integration.

Both `componentownercache = true` and a nonempty endpoint-local
`componentcacheparent` are required. The latter selects an explicitly existing
absolute private0700 parent, with optional `%ROOT%` expansion to the canonical
root identity's SHA256. Supply a distinct pre-provisioned parent per root; neither
recursive directories nor arbitrary discovered caches are adopted. Empty/off uses
the old uncached worker. The parent owner spans only this inspection and retains
its FD on nested uncertainty. The ordinary loaded-archive transaction still owns
durable hint commit; details viewing does not invent a separate commit protocol.


Configured parent path/descriptor binding is rechecked after the worker await
before interpreting a successful result, and again between completed store
publication and archive-head adoption. A caller-supplied parent checker is passed
through the explicit owner API; default borrowed-parent callers retain their
exclusive-parent obligation. Replacing the configured directory or making it
nonprivate during the await refuses the result and leaves the archive head
unchanged. Legacy no-identity hints bypass parent opening entirely. Concurrent
hostile same-UID mutation is not an OS-enforced isolation guarantee.


## Report admission on cache uncertainty

Local component observation now catches `Cache_ownership_uncertain` INSIDE the
semantic transaction callback. The retained node, linked-list wrapper and pending
promise are allocated before inspection can open cache descriptors. On uncertainty
it keeps the original carrier, links it into owner-loop diagnostics, emits a held
message and returns that unresolved promise. The outer resource lease consequently
never sees an ordinary failure to retire. Helper cancellation cannot convert
unknown native ownership into a release. No broad generic-admission policy changes
or numeric-FD retries are introduced.

`SemanticRemote.component_retained_ownership` is diagnostic, not a cleanup API.
There is no automatic recovery/release assertion. The original disposable control
invalidates an owned parent descriptor and calls its real production settle path
to produce a carrier, then invokes the real local report entry with that error.
It verifies a pending report, retained carrier, charged transaction/payload/FD
credits, unchanged credits after actual helper cancellation, and no archive-head
change. The probe intentionally retains application admission until process exit;
external child/group wait proves OS closure, not successful native close or normal
admission retirement. This narrow cache-carrier contract does not qualify every
legacy source-FD cleanup path elsewhere in Unison.
