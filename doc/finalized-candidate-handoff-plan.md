# Retain the receiver's candidate through source checking and final publication

This is a source-only implementation handoff, not a qualification receipt.
The initial audit below describes its pinned predecessor. The current
continuation implements actual descriptor adoption, held-parent resume
admission, mutable/frozen native phases, strict producer registry phases,
local fingerprint receipts and the additive Copy/Files protocol. Native 170, registry 105 and worker 32 controls pass per compiler; combined
materializer/caller qualification passes 79 cases per compiler without
exclusions. The current receipt is
`tests/qualification/retained-producer-publication-20261013.json`.
An invalid resume prefix now restarts by truncating its validated writer for
the same admitted inode, rather than discarding and re-admitting a new object.
Only initial explicit backend/family handoff permits legacy behavior; native
identity errors remain terminal. Consult SEMANTIC-UNISON-DESIGN.md and qualification receipts for
the latest tested source, rather than treating the predecessor pins as current.

The originally audited final-publication slice binds the file reopened by
`Files.preparePublication`; it does not yet bind that file to the receiver's
original producer object. A same-byte inode replacement between `Copy.file`
completion and that attachment can therefore be admitted. Rechecking the full
expected archive fingerprint on every bound commit, including when Adobe
validation is off, rejects different bytes and prevents publishing bytes that
disagree with the archive. It does not reject an identical-byte replacement.
That control must remain a recorded gap until the retained-producer path is
implemented and passes its tests.

Do not solve this with the archive stamp. `Fileinfo.getAux` masks the inode to
30 bits (`src/fileinfo.ml:144`); `Fileinfo.stamp` can return `NoStamp`
(`src/fileinfo.ml:231`). Those fields and their existing marshalers remain
compatible archive/update hints. The new proof uses an endpoint-local native
descriptor, full-width identity and the already held publication parents.

The source reviewed for this plan was:

| Source | SHA-256 |
| --- | --- |
| `src/copy.ml` | `266cd0c7c2ad4a40c3461e9f99308921108a3d806b87d3056ba558de6489d943` |
| `src/files.ml` | `8d2d52e870bb274919873a24d2e1f4aa7da518b015507c05f0ef409e2e0b3acd` |
| `src/semanticSync.ml` | `fee24b304ac5e35128b0b2deda2039b30eb27baae457622f9e7a32a75ab1202f` |
| `src/semanticRemote.ml` | `baf6813e40f5da9974dd9a92436f7e0c3a4394579a498ab60b80faf20e0e89fd` |
| `src/finalPublication_stubs.c` | `099978fd5b7eba4d402f7ce16807ce0d2ec4e68d519b76134f0cb49d8e430828` |
| `src/targetBinding.ml` | `ea1acfc66e7917491784383563151b71f4ffd63efba018ef73f9b10477ff76d0` |

Line locations below refer to that source. Concurrent follow-on Files/native
changes should be reconciled against the behavior, not just those locations.

The smallest useful sequence is: acquire a witness from the actual receiver
output descriptor; retain it while planned data, forks and properties change;
freeze its full native facts after that finalization; run the final target
fingerprint with checks before and after; retain the frozen witness while the
caller awaits source checking; use the same witness for validation and live
publication. Moving named `attach` before `paranoidCheck` closes the later
Source.check-to-rename interval, but it still captures a reopened name after
all writers were closed. It is a narrower improvement, not proof of the
original producer object.

Proposed additive native API, retaining the existing `attach` behavior for
legacy callers:

```ocaml
val adopt_mutable : t -> candidate:Unix.file_descr -> unit
val check_producer : t -> unit
val freeze_producer : t -> unit
val producer_finalized : t -> bool
```

`adopt_mutable` borrows the actual output descriptor for the duration of the
call and duplicates it close-on-exec into the rooted native owner. It does not
consume the channel's descriptor. Admit only a singly linked regular file:
check fresh root/workdir/parent bindings, then compare the held normal-candidate
parent's no-follow leaf to the actual output descriptor, using full native
identity. The normal candidate parent is already owned by `FinalPublication`.
For a promoted stage, its original creation parent may legitimately differ
from this normal parent; do not compare that creation parent to the normal
parent and reject a valid promotion. The materializer must retain its actual
creation-parent/stage witness proof through promotion, then hand over the same
output object to the final context before disarming that earlier owner.

Native phase `PRODUCING` permits Unison's planned size, mode, ownership,
timestamp, extended-property and resource-fork changes. `check_producer`
checks identity, regular kind, single-link privacy, current placement, volume
and directory bindings; it does not freeze mutable file facts before Unison
has set them. It must reject a replacement file, a final-component symlink,
missing/rebound parent, or a hardlink introduced before finalization. No
degraded identity or pathname retry follows that failure.

`freeze_producer` is allowed only from `PRODUCING`. After the last planned fork
and `setFileinfo` operation, capture and recheck the same full native baseline
used by today's attached candidate. Transition to `ATTACHED` only after every
check succeeds. `producer_finalized` distinguishes this producer-origin proof
from named legacy attachment, remains local, and is required before a strict
producer ticket can become eligible for commit. Once frozen, any further
property/fork/data write is a mutation, including a write by Unison itself.
`check_candidate` then applies unchanged around fingerprinting, validation and
publication. Do not refresh its baseline to accept a later replacement.

The owned-name cleanup state must include `PRODUCING` as well as `ATTACHED`.
Cleanup uses the retained witness's current identity and captured parent/name,
so legitimate partial writes can be discarded without deleting a foreign
replacement. Before successful adoption, the native context owns no candidate
leaf. Failure cleanup belongs to the materializer's actual creator/stage
owner; it must not blindly unlink the saved normal path. After native
publication, close only and preserve the publication receipt. The existing
quarantine operation also needs explicit producer-phase semantics if a
pre-freeze failure is to use it; otherwise producer abort remains distinct
from frozen validation rejection.

The registry needs a separate producer borrow, rather than consuming the
single commit borrow before transfer and then trying to reuse it. Proposed
additive interface:

```ocaml
type completion = Guarded_producer | Legacy_backend

val prepare : ?connection:Remote.connection -> ?require_producer:bool ->
  (* existing root/path/workdir/candidate/target/policy arguments *)
  unit -> string option

val with_producer : ?connection:Remote.connection -> token:string ->
  (* the same exact root/path/workdir/candidate/target arguments *)
  (t -> 'a Lwt.t) -> ('a * completion) Lwt.t
```

The private state sequence is `Ready -> Producing -> Finalized -> Committing
-> Closed`. A transaction nonce authorizes one producer operation and one
subsequent commit operation in that order; replay of either operation fails.
Only `with_binding` consumes the commit authorization. A producer borrow
verifies the same connection, immutable session, root, translated local path,
working directory, candidate, planned target and saved follow/case/resource
policies as the commit borrow. Both busy phases count against the same
128-slot endpoint backstop and the requester's existing 64 lifetime permits.

After the producer callback settles, return to `Finalized` only after checking
the producer-origin frozen native witness. It remains registered through the
client's source checks and next RPC. A connection close immediately revokes
idle Ready/Finalized tickets; an active Producing/Committing borrow is marked
closing and keeps its native witness until its awaited helpers settle. Every
failure path revokes the ticket and settles ownership. Retain the current
guard for Lwt waiter-installation failure after callback dispatch: it must not
close under an outstanding helper. A bounded exceptional reservation may stay
closing until its recovery observer can be installed; do not claim universal
allocation or asynchronous-exception coverage.

An explicit planned `legacy_handoff` closes proof descriptors without unlinking
and returns `Legacy_backend`; the caller clears its commit token and follows
the existing copy/rename workflow. This is appropriate when an actual sidecar
appears during resource finalization, when a supported external tool controls
the file's replacement strategy, or for a deliberately excluded backend. It
is selected before validation/live mutation, after any running producer
helpers settle. A stale binding, replaced producer, malformed identity or
operational error never selects legacy handoff. Once attached/frozen, failure
cannot be disguised as an optimization decline.

`Files.preparePublication` must distinguish strict finalized producer tickets
from legacy named attachment. For strict tickets it checks the existing
frozen witness and never calls `attach` again. Preserve target-directory,
conflict-copy and AppleDouble handoff decisions, including families detected
only after forks are written. No producer change qualifies directory
transactions or `moveLocal`.

Use a new negotiated producer capability (for example
`target-binding-producer-v0`) and an additive `boundCopyV0` command. Keep
`transferFile`, `finishExternalTransfer`, their argument/status marshalers,
and all source-check/stream commands unchanged. This avoids assuming that a
peer advertising the earlier target-binding capability implements producer
handoff. A separate `Copy.fileBound` entry point can accept the prepared
token, logical target root and translated target selection, retain all
existing positional copy arguments, and return the old file-info result plus
`completion`. Existing `Copy.file` callers remain unchanged. `Files.copy`
passes the binding only for its top-level regular-file branch; `copyBack`
uses its already known regular-file setup. Nested directory/merge/move callers
keep their existing path.

The new command adds `(logicalTargetRoot, translatedTargetPath, token)` to the
existing transfer arguments and adds a small completion tag to its existing
result. No descriptors or native identities cross the wire. Dispatch the
bound receiver command manually with `Remote.registerServerCmd`, as the new
Files setup/rename commands do. **The source connection and ticket-owning
connection are separate parameters.** With a local receiver and remote source,
source compression uses `Some sourceConnection` but the prepared ticket owner
is `None`. With a remote receiver, the server's incoming connection owns the
ticket and is also the current source transport. Reusing
`registerRootCmdWithConnection` without that distinction would incorrectly
bind a local receiver's ticket to its remote source connection.

The receiver returns only after forks, selected properties, freezing, final
paranoid fingerprint and the producer-after-check have completed. The caller
then runs the existing `checkForChangesToSource` logic and Files source checks,
and commits using the same token. Pseudo-fingerprint behavior remains
compatible: the actual target fingerprint computed by `paranoidCheck` still
goes through `TransferNeedsDoubleCheckAgainstCurrentSource`. Keep that actual
target full fingerprint endpoint-local with the frozen witness as well, so
commit can recheck it even when the archive's fingerprint is pseudo. A
pseudo archive value must not be relabeled a cryptographic source proof.
Source-check failure releases the prepared target; successful source checking
does not refresh candidate identity. Archive advancement remains last.

| Materializer / current location | Required retained-producer handoff |
| --- | --- |
| Generic remote DATA, `destinationFd` / `transferFileContents` (`src/copy.ml:1013`) | Adopt the actual `openFileOut` descriptor on first open, before writes. Its O_EXCL creator is the producer object. Retain native duplicate across EOF channel close, resource transfer and awaited property loading. Check producer before/after each planned finalization, then freeze before `paranoidCheck`. The Netware O_TRUNC fallback is not exclusive creation; preserve it only as an explicit legacy backend unless separately qualified. |
| APFS ordinary receiver clone (`src/copy.ml:1070`, EOF near `:1170`) | Existing `StagePublication.adopt` already binds the native creation parent/output. After `StagePublication.publish` places that same object at normal temp, adopt its still-open actual output descriptor into the final context **before** `StagePublication.disarm`, release or `close_all`. The stage owner and final owner overlap during handoff. On failed adoption the stage owner still cleans its own object. |
| Local generic copy, `copyContents` / `localFileContents` / `localFileAsync` (`src/copy.ml:626`, `:705`, `:741`) | Add a producer callback at the actual output opening, before its existing close. Keep the native duplicate through resource copying, `propsWithExtDataLocal` and `setFileinfo`. Freeze in the main local-file completion path before `Copy.file` invokes `paranoidCheck`. Auxiliary synchronous localFile callers keep their legacy contract unless given an explicit binding. |
| Direct source clone, `copyByPath` (`src/copy.ml:609`) | A bool from `Fs.clone_path` carries no output witness. Use a descriptor-returning native creator with actual parent proof, or explicitly choose legacy qualification for this shortcut. Opening the completed path afterward is a weaker named attachment, not original-object proof. |
| Local basis clone, `copyLocalCloned` (`src/copy.ml:650`) | It currently closes basis/output before raw stage rename. Retain output and actual parent; use qualified intermediate publication, then adopt the same output into the final owner before closing/disarming. Preserve copy bounds/cancellation and never promote via a saved path after a proof failure. |
| Local SDE (`src/semanticSync.ml:136`, promotion `:184`) | Workers already borrow held descriptors and settle before transaction close. Add a producer-aware promotion completion that retains output and creator proof through qualified stage-to-normal publication. Transfer witness/name ownership before `close_transaction`, then continue normal fork/property finalization. The current close-before-Fs.rename order cannot qualify this path. |
| Remote SDE (`src/semanticRemote.ml:157`, promotion `:203`) | Same handoff as local SDE: hold output and actual creation-parent witness through workers and promotion; adopt before `close candidate`/candidate-registry release. No source/basis worker FD is substituted for the actual output witness. Current two-descriptor native clone results need creator-parent coverage or a separately qualified creation path. |
| Moved-file reuse, `tryCopyMovedFile` (`src/copy.ml:772`) | This is a copied hint, not the separate move transaction. Its local materializer must pass the actual output witness through the awaited source property load and final full fingerprint. Do not let its broad `Util.Transient` hint-fallback handler swallow new binding failures and retry with a revoked/attached ticket. A failed hint may retry only after its owned producer is safely abandoned and a new admitted producer attempt is established, or select explicit legacy before producer admission. |
| Already fully transferred temp (`src/copy.ml:1506`) | Open and admit the current regular single-link resume object **before** `fileIsTransferred` hashes it; fence that hash with the same witness, then set properties, freeze and recheck the final fingerprint. Its earlier-process creation is unknown: describe origin as an explicitly admitted verified resume object, not newly created by this session. |
| Partial DATA_APPEND / `validFilePrefix` (`src/copy.ml:174`, `:1274`) | Retain the selected prefix object before prefix fingerprinting; fence those reads. The append writer must match that held object before any write, with no final-symlink following or replacement adoption. Preserve prefix-length/source-prefix checks and bounded offsets. If there is no admitted prefix, remove/discard under proper ownership and create/adopt a new exclusive output. |
| External copy (`src/copy.ml:1435`–`:1500`) | Existing tools receive a pathname and may replace it internally. They supply no original output FD contract. Preserve copyprog/copyprogrest through explicit legacy completion before launch; a later reopen is not producer proof. A future declared FD-output/in-place extension could qualify tools that honor a held descriptor and settle all child work, but is outside this slice. |

For the first narrow implementation, qualify ordinary remote DATA and local
generic exclusive-output copy plus the already qualified APFS receiver
promotion. Other materializers either implement the same handoff now or
explicitly retain legacy qualification and their existing workflow. Do not
silently claim all bound copies qualify because the final name can be reopened.
Do not disable useful copy/resume/SDE/external behavior globally; make the
qualification boundary explicit in the additive path and test it. Each
backend can then be admitted as its own producer and promotion tests pass.

Required controls before claiming the new slice:

- The known identical-byte replacement after Copy.file completion, while the
  caller awaits Source.check, is rejected. Preserve the live sentinel and both
  archives; never adopt or delete the replacement normal-temp object.
- Replace with identical bytes between data EOF and property/fork finalization,
  during property-loading awaits, and before/after final paranoid hashing.
  The original witness remains open; current-object binding must reject the
  replacement. Legitimate selected properties and native resource forks pass.
- Replace a clone/SDE stage before promotion, and replace the normal temp
  immediately after promotion before final adoption. Every failed handoff
  closes all owned descriptors and removes only the witnessed owned name.
  Distinct stage/temp parents, followed aliases, external followed targets,
  sibling changes and planned normalization remain supported.
- The actual producer FD differs from the named candidate but has identical
  bytes, matching low 30 inode bits, or matching size/time: adoption rejects it.
  NoStamp and ignoreinodenumbers do not weaken native identity. Add hardlink and
  final-symlink controls, descriptor reuse, actual-parent rebind and missing
  native volume identity.
- Fully completed and partial resumes bind their admitted objects before any
  fingerprint/append step; replacement at each await rejects. A valid resume
  retains its prefix and current workflow. Hint fallback, ordinary clone decline
  and SDE fallback do not reuse a failed producer witness or silently downgrade
  an operational/stale error.
- Producer-command replay, commit before producer completion, concurrent
  producer/commit on one token, wrong connection/root/path/session, and a
  disconnected finalized idle ticket all reject. Connection loss during
  producer workers preserves their borrowed FDs until all helpers settle.
  The 128-slot backstop includes both producer and commit borrows; the requester
  lifetime permit remains held through source checking and final cleanup.
- Newly created AppleDouble auxiliary files select a planned legacy family
  before validation. Auxiliary lookup errors fail. Actual sidecars, conflict
  copies, directories, moves, external copies, source-selected properties and
  archive-last ordering retain their existing behavior and honest scope.
- Guarded Adobe-off, Warn, Require, helper failure and helper mutation all bind
  the same finalized producer object. Final hash compares full data/fork
  fingerprint to the appropriate actual source-confirmed target fingerprint;
  fingerprint equality alone never grants inode ownership.
- Post-native-success exception and readback failure preserve Published and
  never delete live or advance an unproven archive. Cleanup faults, immutable
  EPERM and quarantine collisions preserve their explicit errors. Repeat the
  existing same-byte failing control as a positive regression test only after
  this complete path is exercised through actual Copy/Files, not a fixture
  that manually supplies the missing attachment.

Native descriptor-relative checks and rename remain a cooperative namespace
contract, not a kernel compare-and-swap, a hostile-writer sandbox, a remount
incarnation proof or a crash-durable transaction. Fingerprinting via a reopened
name with before/after witness checks shares that cooperative limitation;
hashing the held producer witness directly would further tighten the data
read binding, but must also account for resource forks. Linux/ZFS/ReFS and
Windows replacement semantics require their own backend qualification. No
Photo, Lightroom, SDK, production-cache or full-generator operation is needed
to implement or qualify these small synthetic copy/publication controls.
