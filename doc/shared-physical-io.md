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
