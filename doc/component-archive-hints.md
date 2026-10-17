# Local archive ownership for component cache references

This successor reuses the normal Unison archive transaction for the trusted
reference to an already published UIX/0 manifest. It does not change archive
format23, file fingerprints, comparison/reconciliation authority or negotiated
features. `componentownercache` is endpoint-local and defaults off. It does not
automatically capture files, open a managed cache namespace or enable reuse.

A newly registered serialized `Proplist` key would make older readers fail.
Instead, the component key exists only in the loaded owner's property cache.
`storeArchiveLocal` always removes it from the legacy property payload. With an
explicit reference and the preference enabled, it writes the already supported
paths map (including an empty map when necessary), then one fixed optional hint.
With no reference or the preference off, the previous serialization path remains
unchanged. Old readers that understand the base archive consume at most the paths
map; old writers may drop the hint. That loss is a cache miss, not authority to
scan or promote surviving blobs. A separately linked probe now runs the actual retained pre-component-RPC fork's
old Update/Proplist/native production objects against current stock/Ox private
archives. That old registry lacks the new key: its reader preserves exact archive
bytes, its rewrite drops the hint, and current cold reload declines cache reuse
while the UIX payload stays unchanged. This is old-code archive qualification;
the untouched old CLI, network peers, arbitrary older versions and data-bearing
corpora remain separately unqualified.

## Adoption and loading

`DngComponents.owner_index_reference` returns captured `(binding,manifestSHA)`
only after manifest publication returned normally. An observed rename followed
by directory-sync failure is insufficient. Actual rename state is still available
for recovery, and the ticket remains one-shot. The caller independently settles
all borrowed descriptors and referenced captures before calling
`Update.set_component_owner_reference` on a loaded local root.

The setter requires the explicit preference and the opaque publication context;
it changes memory only. `Update.commitUpdates` persists the reference through the
ordinary scratch/new/main archive protocol. No new mutable head file, archive
version, root command, property on synchronized files or physical-IO pool exists.
`clear_component_owner_reference` drops only the memory hint, later persisted by
normal commit; it does not unlink objects or refund native quota.

Loading obtains the reference only from that trusted local archive context.
Absent, truncated, unknown-version, wrong-context or checksum-damaged hint frames
are ignored. Operational channel errors propagate. The hint is read only after
the valid legacy paths tail; corruption of the primary archive/paths data keeps
upstream error behavior. No checksum of an arbitrary cache file supplies this
trust. A selected reference still requires authenticated UIX/UDI/UCR metadata,
exact owner/path/generation selection and full-current-input/parser verification.

## UAX/0 optional hint

The fixed136B frame is:

| Offset | Contents |
| --- | --- |
| 0 | `UAX` plus five NUL bytes |
| 8 | Raw32 archive-context SHA256 |
| 40 | Raw32 UIX manifest owner-state binding |
| 72 | Raw32 captured UIX manifest digest |
| 104 | SHA256 of the preceding104bytes |

The archive-context digest uses the domain
`unison-component-archive-context/0`, canonical owning root, canonical root set,
archive format and the archive's stored commit magic. Each field is prefixed by
its decimal byte length and a colon. Rewriting the normal archive rebinds the
already trusted reference to the new commit context. Roots in the same process
can have different private hints without affecting the shared archive checksum.
The checksum detects corruption within this local-state trust boundary; it is
not authentication against the owning UID or a remote-state signature.

## Qualification boundary

Original stock private controls use empty generated roots and a private `UNISON`
directory. The manifest is actually written/synced/published; both borrowed FDs
are closed before adoption. Separate processes test archive restart loading,
rewrite preservation, default-off removal, absence without blob discovery and
optional-checksum corruption without archive reset. No source file data, SDK,
Adobe, remote process or transfer runs. Test-only setup import/compiler/preference
failures are preserved as closed attempts; they did not modify production code.
Current stock/Ox Make/fullselftests/Dune and110workerchecks/compiler passed;
1272current production-source checks match. Both production-linked probes passed
14direct calls/six phases per compiler, all child groups/tokens closed. Pure DNG
controls1391/compiler include fixed framing vectors;29test-only native publication
fault checks/compiler prove rename+directoryEIO cannot grant a normal-completion
reference. Exact evidence: `tests/qualification/component-archive-hints-actual-20261017.json`. This is not a whole-cache/old-peer/corpus/production certificate,
nor a new hardware power-loss or legacy close-uncertainty guarantee.

The retained old-code compatibility run passed13direct calls under actual owner
12014/2441f7/0, allgroups/tokensclosed. Old source/object/original-CLI bytes were
rehashed unchanged; the original CLI was not executed. Current production source
is unchanged and was rebound against its four existing builds, not rebuilt.
Exact evidence: `tests/qualification/component-archive-legacy-actual-20261017.json`.
