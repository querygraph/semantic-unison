# Physical IO coordination: source proposal

CPU sharing is implemented: Unison uses canonical00..07; Photo uses08..15.
Bulk IO is a separate resource. The [v1 proposal](shared-physical-io-proposal-v1.json)
is source-only: no canonical IO pool has been created, no kernel IO locking is
wired into either dispatcher, and no OS topology provider is qualified.

The proposed namespace is `~/Library/Application Support/FirstPair Lightroom
Shuttle/io-lanes-v1`. Photo Root and Unison must agree one namespace and publish
its stable directory/barrier/lane inode manifest before live use. Neither
consumer creates missing files or falls back to another pool. Photo's existing
UI/catalog/IO ownership lease remains separate and is not repurposed here.

| Job topology | Locks from the same canonical namespace |
| --- | --- |
| Complete stable qualified physical member set | Shared `all-devices.lock`, then exclusive lanes for the sorted member union |
| Unknown, incomplete, changed or unqualified topology | Exclusive `all-devices.lock` |

Every known-device job holds the shared barrier. Thus an unknown-device job's
exclusive barrier conflicts with **all** known jobs. An independent `unknown`
lane would be incorrect. Distinct known devices can overlap; APFS siblings and
composite arrays with a shared physical member cannot. Volume names, `st_dev`,
filesystem type and an apparent virtual-disk parent do not prove independence.
A future local ZFS/ReFS provider must supply the same complete-member contract;
no native discovery or platform support is claimed by this abstraction.

## Acquisition and lifetime

1. Resolve the complete local resource set before payload dispatch, using fresh
   volume/topology bindings from a separately qualified trusted provider.
2. Acquire the barrier and sorted member lanes nonblocking, then the explicitly
   granted sorted CPU tokens. Use existing private single-link inode-bound files
   and fresh open descriptions; never explicitly `LOCK_UN` inherited locks.
3. On contention, close the entire partial bundle before returning busy/waiting.
   Never hold IO while waiting for CPU, upgrade a held shared barrier, or nest
   leases whose combined resources were not declared.
4. Pass/retain descriptors through actual child, nested process-group and worker
   settlement. Unknown close/ownership retains the owner; uncertain numeric FDs
   are not retried. Deadline, output frame and PID absence are not release proof.
5. Topology/manifest updates require the exclusive stable barrier and a pinned
   successor adopted by both consumers. A stale/unbound namespace is a refusal,
   not permission to use another barrier.

This first protocol is for complete local bulk jobs or endpoint-local phases.
Do not hold a per-phase IO lease across peer-dependent RPC waits: distributed
source/consumer admission needs its own deadlock qualification. A same-host
loopback wrapper must account for both endpoints together. Existing production
`IoAdmission` remains a separate endpoint-local `st_dev` gate; it has not become
a physical-device scheduler through this proposal.

## Evidence and next gate

The [pure planner](../tests/shared_io_plan.py) defaults to global fallback until
its trusted adapter is explicitly qualified. It validates bounded canonical
claims, merges resource sets and rejects fake domain splits. Its observations
are inputs, not discovery or kernel identity attestations.

[Ten pure controls](../tests/qualification/shared-io-source-ready-20261016.json)
passed under Unison's00..07 CPU ownership, actual terminalfb8786/exit0, containing
group reaped and source pins unchanged, tokens closed. They cover synthetic
sibling/disjoint/composite claims, unknown-global conflicts, changed bindings,
unqualified adapters and invalid/bounded inputs. No devices, IO pool, photographic
payloads, SDK or Adobe executable were accessed by these cases.

Next: joint canonical manifest, disposable two-owner barrier/member/CPU rollback,
inheritance and close-unknown controls; then actual local topology qualification
and a bounded simultaneous synthetic workload. Until both dispatchers join the
same qualified protocol, physical IO coordination is by explicit owner messages.
This proposal grants no payload access, native window, quiet timing, hard RSS/CPU
limit or production publication authority.

## Joint namespace successor

The immutable [v2 source proposal](shared-physical-io-proposal-v2.json) supersedes
the v1 namespace suggestion with `FirstPair Lightroom Shuttle/physical-io-lanes-v1`
and a Root-published `SHARED-PHYSICAL-IO-POOL-v1.json` manifest. Neither exists by
this work. Photo/UI and migration locks remain separate and are never repurposed.
The full bundle order is IO, CPU, then existing native/UI ownership, all
nonblocking with complete rollback before waiting. Stable physical identity,
oldest-observation freshness, mount/boot binding, hotplug/refusal and immutable
manifest succession are explicit source requirements, not implemented detection.

[Six actual read-only metadata commands](../tests/qualification/topology-metadata-actual-20261016.json)
completed under Unison00..07, 398869 raw bytes, all child waits0 and owned group
reaped with other members absent; tokens closed. Raw bounded diskutil/ioreg
receipts are private and pinned. Quasar UUID matches the handoff and Ten reports
HFS+, but no complete physical-leaf provider or runtime IO pool is qualified.
No device media/DNG payload, native Photo/SDK, live provisioning or private-DNG
admission occurred. Current V7/other dispatchers do not gain this protocol by
source publication.

## Actual provisioned namespace and EX_GLOBAL backend

Root has provisioned the original `io-lanes-v1` namespace, with sole existing
`all-devices.lock` barrier and no physical-device lanes. Adopt exact manifest
`/Users/alexy/src/photo/preview-generator/SHARED-PHYSICAL-IO-POOL-v1.json`, SHA
`f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636`.
The later v2 `physical-io-lanes-v1` path suggestion remains historical and must
not be created as another pool. No manifest was modified by Unison.

The [joint consumer contract](shared-physical-io-consumer-contract-v1.json) pins
the actual directory/barrier and the existing-only `tests/shared_io_pool.py`
backend. Only nonblocking EX_GLOBAL is supported; IO precedes CPU, and all
partial descriptions close before busy/wait. Existing native/UI ownership must
be acquired nonblocking last by a future qualified consumer, with full rollback.
The backend does not implement that native/UI stage or bind either production
dispatcher. Close functions consume caller settlement proofs; unknown retains
ownership and prohibits numeric descriptor retries.

[Ten disposable controls](../tests/qualification/shared-io-disposable-controls-actual-20261016.json)
passed with independent Python contention, inherited descriptions and late-CPU
rollback, plus refusal/uncertainty cases. No canonical IO file was opened.
The [finite canonical qualification plan](shared-physical-io-canonical-qualification-plan-v1.json)
is source preparation only; exact driver/command freeze and a separate finite
canonical test admission remain before the first live barrier test. Neither
provisioning nor these disposable tests grant payload/SDK execution or live bulk
dispatcher integration.
