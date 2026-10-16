# Descriptor ownership and admission lifetime inventory

Subsequent implementation adds retained publication envelopes and explicit
borrowing; see [resource-admission.md](resource-admission.md). The inspected
counts and source pins below intentionally remain evidence for the original
`e9be473` checkpoint, rather than claims about later rewritten line numbers.


Source audit, 2026-10-13. These are counts of explicit project-owned descriptor
table entries in the inspected code, not a runtime census or a claim that the
current admission credits bound the process. No build, fixture, photographic
input, Adobe helper, catalog or cache was accessed for this audit.

Each successful `open`, `openat`, `dup` or duplicating `fcntl` adds one entry.
Two entries referring to the same directory or open-file description count
twice. Converting an existing descriptor to an OCaml channel, wrapping it in
Lwt, or borrowing it in a proof adds zero entries. `CloneLease` borrows its two
caller descriptors. Child-process descriptors are a separate process census;
the helper parent's pipes and temporary spawn duplicates count here.

## Native ownership, including transient entries

| Owner or operation | Explicit entries and phase | Release / relevant source |
| --- | --- | --- |
| Target nonce | One `/dev/urandom` entry, before native target preparation; not concurrent with the completed final context in the normal sequence | [TargetBinding nonce](../src/targetBinding.ml#L167) closes before returning |
| `FinalPublication.prepare` | Four retained entries: logical root, working directory, candidate parent, target parent. All four are opened even when paths resolve to the same inode | [Native preparation](../src/finalPublication_stubs.c#L439), [slots](../src/finalPublication_stubs.c#L55) |
| Final binding checks | One temporary relative-directory probe at a time, in addition to retained entries | [probe](../src/finalPublication_stubs.c#L231), [binding checks](../src/finalPublication_stubs.c#L238) |
| Final resolution check | A fresh working-directory entry remains open while a relative target-parent probe is opened: two transient entries. Four-entry prepared context peaks at six; a witnessed five-entry context peaks at seven | [resolution](../src/finalPublication_stubs.c#L498) |
| Final producer adoption | Adds one owned duplicate of the borrowed output, or one opened resume witness. Four becomes five; post-adoption binding probes can temporarily make six | [adoption](../src/finalPublication_stubs.c#L518) |
| Final named attachment | Opens one candidate witness; four becomes five | [attachment](../src/finalPublication_stubs.c#L736) |
| Final context release | Closes witness and four directory entries. Mutable/frozen witness remains owned across producer return and later source checking | [native close](../src/finalPublication_stubs.c#L79), [Finalized transition](../src/targetBinding.ml#L386) |
| `StagePublication.prepare` | Three retained entries: working root, expected stage parent, normal temporary parent | [preparation](../src/stagePublication_stubs.c#L311) |
| Native clone stage | Opens input and actual creation parent, then either reservation or basis. Peak is five simultaneously: input, creation parent, admitted basis, stage-read handle, output-write handle. Reservation is already closed before basis creation. Successful handles ABI returns three; two-entry ABIs close the parent | [native engine](../src/copy_stubs.c#L616), [reservation close](../src/copy_stubs.c#L644), [write reopen](../src/copy_stubs.c#L705) |
| Stage adoption | Consumes the returned parent, duplicates borrowed output, then closes expected stage parent. Context transiently holds five and settles to four: root, actual parent, temporary parent, witness. The two original data descriptors remain separate and caller-owned | [adoption](../src/stagePublication_stubs.c#L355) |
| Stage checks | One transient directory probe in addition to retained context entries; probes are sequential | [probe](../src/stagePublication_stubs.c#L236), [checks](../src/stagePublication_stubs.c#L244) |
| Stage disarm / abort | Closes all context entries. Publishing the normal temporary name alone does not close them; `disarm` does | [disarm](../src/stagePublication_stubs.c#L417), [close](../src/stagePublication_stubs.c#L77) |

The native context structs currently have no `t.count` or descriptor-count
field. A future native count must sum nonnegative owned slots, not unique
inodes. Stage slots have capacity five, prepared occupancy three, adopted
occupancy four; final slots have capacity five, prepared occupancy four,
witnessed occupancy five. Such a slot count excludes incoming-but-not-consumed
descriptors and native local probe/open variables, so it cannot by itself
authorize the operation's peak. Close clears slots before attempting the OS
close, protecting against number reuse; a slot count is not independent proof
of OS settlement after an ambiguous close error.

## Worker, semantic transaction and helper entries

| Operation | Owned additions and overlap | Lifetime / source |
| --- | --- | --- |
| Persistent worker pool | Two notification-pipe entries | [pool creation](../src/semanticWorkers.ml#L154) through [shutdown](../src/semanticWorkers.ml#L289) |
| Queued Inspect / Digest / Observe | One submitted descriptor duplicate, including while waiting for I/O, a domain slot and CPU credits | [submit](../src/semanticWorkers.ml#L183); duplicate occurs before either execution gate |
| Active Inspect / Digest / Observe | One further `SemanticFile` reader duplicate: two additions per active unary job | [worker execution](../src/semanticWorkers.ml#L69), [reader duplication](../src/semanticFile.ml#L50) |
| Queued Apply | Two submitted duplicates: basis and output | [output duplication](../src/semanticWorkers.ml#L38), [submit](../src/semanticWorkers.ml#L186) |
| Active Apply | Adds basis reader duplicate and nested output reader duplicate. Total four worker additions; pre-write and final output readers are sequential, not two concurrent output readers | [execution](../src/semanticWorkers.ml#L85), [apply verification](../src/semanticDelta.ml#L203) |
| Worker settlement | Reader closes inside `with_fd`; job and operation duplicates close before completion is queued and owner promise wakes | [worker completion](../src/semanticWorkers.ml#L112) |
| Native prepared writer / positional write | Zero descriptor additions; borrows admitted output | [writer API](../src/semanticFile.ml#L1), native `semanticFile_stubs.c` |
| Local async semantic transaction | Original basis + output + retained source = three. Bound StagePublication adds four. Two submitted inspectors can add four simultaneously when two domains/CPU permits are available; Apply likewise adds four | [local transaction](../src/semanticSync.ml#L250), [parallel inspection](../src/semanticSync.ml#L265) |
| Remote semantic receiver transaction | Original basis + output = two. Bound StagePublication adds four. Unary inspection adds two; Apply adds four; nonce opens one between settled inspection and RPC | [receiver](../src/semanticRemote.ml#L265), [nonce](../src/semanticRemote.ml#L219) |
| Remote semantic source plan | One original source plus one submitted worker duplicate plus one reader duplicate: peak three additions. Source files close before plan encoding / reply return | [source plan](../src/semanticRemote.ml#L74) |
| Candidate validation fingerprint | One candidate/tool original open plus unary worker additions two: peak three. Candidate and executable snapshots are awaited sequentially | [snapshot](../src/candidateValidation.ml#L35), [validation sequence](../src/dngValidation.ml#L115) |
| Helper parent execution | Two pipes = four entries; native spawn duplicates both write ends = two more. Peak six, settling to two capture readers after spawn | [pipes](../src/helperSupervisor.ml#L193), [spawn duplicates](../src/helperSupervisor_stubs.c#L130) |
| Candidate helper I/O grouping | One extra candidate entry spans the helper execution and settlement; combines with spawn peak six for seven additions | [I/O grouping](../src/semanticRuntime.ml#L99), [execution wrapping](../src/dngValidation.ml#L129) |
| Validation tree walk | One directory entry at a time for explicit enumeration; closes before processing another pending path. File-information/resource-fork routines may independently open a reader | [enumeration](../src/candidateValidation.ml#L60), [scan](../src/candidateValidation.ml#L73) |

The fixed pool's two entries, stdio, RPC/loopback/SSH transport channels,
archive operations, file-information/resource-fork probes and runtime-owned
descriptors are not included in the transaction additions above. They require
their own baseline/owner attribution in a real process census. In particular,
these tables do not assert the total number of descriptors in a helper child
or SDK process.

## Selected complete producer forms

These simultaneous counts exclude the process baseline. They cover the named
regular-file control flow with successful descriptor acquisition. They are
not an exhaustive maximum for every legacy directory, sidecar, merge,
external-copy, backup or error backend. A census must verify those branches
before claiming a complete process ceiling.

| Form / phase | Simultaneous entries | Explanation |
| --- | ---: | --- |
| Bound local SDE, active two inspectors or Apply | **15** | Final prepared context 4 + Stage adopted context 4 + originals basis/output/source 3 + worker additions 4 |
| Bound remote SDE receiver, active Apply | **14** | Final prepared 4 + Stage adopted 4 + basis/output 2 + worker additions 4 |
| Bound remote SDE receiver, unary inspection | 12 | Final 4 + Stage 4 + originals 2 + worker additions 2 |
| Bound remote SDE receiver waiting for source RPC | 10 | Final 4 + Stage 4 + originals 2; nonce temporarily makes 11 |
| Legacy unbound async local SDE | 7 | Originals 3 + two inspectors / Apply 4; clone acquisition separately peaks 5 |
| Legacy unbound remote SDE receiver | 6 | Originals 2 + Apply 4; clone acquisition separately peaks 5 |
| Synchronous local SDE planning | 5 | Basis/output 2 + basis reader 1 + source original/reader 2; no worker queue |
| Bound APFS clone acquisition, source clone / local clone / remote ordinary receiver | 12 | Final prepared 4 + Stage prepared 3 + native clone peak 5 |
| Bound ordinary remote APFS receive during token processing | 10 | Final prepared 4 + Stage adopted 4 + basis/output channels 2; range lease adds zero |
| Bound local ordinary receiver-basis producer during comparison | 11 | Previous row plus local incoming source channel 1 |
| Bound ordinary local byte copy after output adoption | 7 retained | Final witnessed 5 + input/output channels 2; native checks can add probes. Channels consume the descriptors instead of duplicating them |
| Bound ordinary remote nonclone receive after output adoption | 6 retained | Final witnessed 5 + output channel 1, plus reference input when rsync uses it |
| Bound resume admitted before hashing | 5 retained, then +1 for ordinary fingerprint reading | Final prepared 4 + opened resume witness 1; append writer adds another 1 while active |
| Bound candidate validation helper spawn | 12 | Final witnessed 5 + grouping descriptor 1 + helper parent's native spawn peak 6 |
| Finalized ticket awaiting later source check / commit | **5 retained** | Producer callback has returned, while FinalPublication witness and four directory entries remain owned |

Final adoption and resolution checks have their own probe peaks. For example,
local SDE's producer adoption after worker settlement can hold final 5 + Stage
4 + originals 3, with one binding probe making 13. It does not overlap the
previous four worker duplicates, so adding witnessed-final 5 to the earlier
active-worker 11 would incorrectly produce 16 for that particular path.

Resource forks and ordinary fingerprinting open actual readers, rather than
being free metadata-only calls. [Copy's paranoid fingerprint](../src/copy.ml#L277)
calls [Os.fingerprint](../src/os.ml#L261); [Fingerprint.file](../src/fingerprint.ml#L34)
holds one reader, and [Osx.ressFingerprint](../src/osx.ml#L472) can open a fork or
AppleDouble reader. The two fingerprint components are sequential. Existing
AppleDouble file-information probes need their own phase attribution before
an exact all-branch peak is asserted.

## Where current admission loses the lifetime

`SemanticRuntime.with_transaction` charges eight descriptor credits at
[lines 126–131](../src/semanticRuntime.ml#L126). This is already less than the
bound receiver semantic component's ten or bound local component's eleven,
before four final-target entries are added. A source plan's three entries do
not justify treating unused source credits as consumer ownership. Role
headroom is a capacity guarantee, not a transfer of another role's credits.

[Target setup](../src/files.ml#L690) prepares the four-entry native final
context before Copy/SDE admission. [TargetBinding.prepare](../src/targetBinding.ml#L219)
uses only a 128-slot registry limit. Ready and Finalized tickets can retain
four or five entries while no semantic callback is active. A completed SDE
callback releases its eight-credit transaction lease even though producer
completion retains a five-entry Finalized context through later source
checking and the commit RPC. Ordinary, source-clone and resumed paths can
retain the same final context without ever entering that SDE lease.

Validation's [nine-credit scope](../src/candidateValidation.ml#L126) covers its
own snapshot/helper additions conservatively for the named regular-file path,
but the already retained final context is outside it. Moreover, worker
duplicates are allocated before the CPU and I/O queue gates, so charging only
active jobs cannot bound waiting descriptors.

There is no sound fix consisting only of increasing eight to another estimate.
An admission owner must exist before target preparation, persist through
producer return/source checking/commit/disconnect settlement, and authorize
new opens/duplicates before they happen. Borrowing or converting a descriptor
must not independently charge it again; changing its owner must move or split
the existing reservation atomically. Parent/helper memory and child descriptor
limits remain separate requirements.

## Concrete admission shape for implementation

1. Create an endpoint-local lifetime lease before target setup can open native
   contexts. Store it in the target registry record and carry a stable local
   owner through Copy, resumption and validation. Wire tokens identify the
   owner; peer-reported descriptor counts cannot change capacity.
2. Reserve persistent and bounded transient capacity before native entry.
   Native context occupancy and per-operation temporary headroom are distinct.
   Transfer reservation ownership when StagePublication consumes the actual
   parent or FinalPublication duplicates/adopts output. Release actual owned
   slots only after their close/settlement, retaining uncertainty on failed
   settlement instead of inferring it from an emptied slot.
3. Worker submit must obtain a child reservation before duplicating borrowed
   basis/output. Its queued duplicates retain capacity through I/O/CPU waits;
   execution reserves reader headroom. Completion closes them before releasing
   capacity and before waking the owner. Local paired inspectors need atomic
   capacity for both jobs or a serial fallback that settles the first before
   admitting the second; two partial acquisitions must not deadlock.
4. Keep persistent target proof capacity after producer return. Release it
   only on actual commit/abort/legacy ownership handoff and settled callbacks.
   A legacy handoff closes native proof but is not evidence that subsequent
   legacy Copy/helper work has ended; its separate work lease must survive.
5. Reserve helper grouping/pipe/spawn duplicates before opens. Keep parent
   capture capacity until both drains and owned child settlement finish. SDK
   child memory/descriptors need their own declared/qualified envelope; do not
   debit only the parent's six spawn entries and call that a child limit.
6. Preserve independent source service headroom and define a progress-safe
   policy for preprepared receivers. Incremental waiting while many four-entry
   tickets exhaust capacity can otherwise prevent the source or apply work
   needed to retire those tickets. Either reserve the entire chosen work
   envelope before prepare, or admit only a bounded set of prepared owners
   with irrevocable work headroom. These are implementation decisions, not
   claims that the current code supplies either policy.

The selected fifteen-entry local SDE peak is evidence for planning, not a
universal transfer constant. Legacy families, extra resource readers, native
transients, transport baselines and error settlement must be represented and
measured before a global process-wide bound is claimed.

## Synthetic census and lifetime controls to build next

Use compiler-matched private snapshots and only generated byte/DNG fixtures.
Add test-only phase hooks to the complete Files/Copy/TargetBinding/worker code,
and native hooks after each relevant context/clone/helper allocation and close.
Enumerate `/dev/fd` from a private C helper, exclude the enumerator's own
directory entry, and record PID, phase, fd number, flags and native identity.
Sampling just before/after an opaque native call misses its transient peak.
Record native slot ownership separately from kernel descriptor enumeration.
At barriers, workers must be paused outside the OCaml owner loop so all
required overlaps can be reproduced without blocking source service.

Measure a baseline after pool and transport initialization; report both the
absolute process inventory and incremental attributed entries. Record old
semantic usage alongside the inventory to demonstrate the eight-credit
consumer bound is violated by one actual bound SDE job. A second control
should prepare several tickets without starting Copy, and a third should hold
a Finalized producer across a finite source-check/commit barrier: both expose
native entries absent from the old semantic lease.

After implementing admission, use the same controls to prove:

- No target, clone, worker duplicate, validation pipe or spawn duplicate opens
  before sufficient owner capacity is reserved, including queued work.
- Open owned entries never exceed the attributed live reservation at each
  allocation/close barrier; budget-bound siblings wait before opening.
- Producer completion retains target capacity through later RPC/source
  checking; disconnect cancels admission waiters while borrowed worker/helper
  capacity remains until settlement.
- Local paired inspections and bidirectional remote source requests make
  progress at the minimum supported budget, without borrowing reserved source
  headroom for consumers.
- Partial native writes, native preparation/adoption errors, helper deadlines
  and close-error/descriptor-reuse controls neither leak credits nor close a
  newly reused descriptor. Ambiguous settlement is reported rather than
  converted into available capacity.
- Ordinary, direct-source clone, receiver-basis clone, complete/prefix/invalid
  resume, local/remote SDE, validation-off, synthetic warn/require helper and
  explicit legacy family paths each exercise their actual owner transitions.

Persist exact source/mutation/compiler/object/binary/log pins and terminal
receipts. Keep census and barriers entirely private; no production preference,
environment fault switch, Adobe invocation or real photographic input is
needed to qualify the descriptor ownership mechanism.

## Inspected source version

The worktree was clean apart from this new audit and external coordination
files at `e9be47381d35af82d816b1f80df348ddf7409180`. Line references and counts
above bind to these inspected inputs; future resource-admission edits need a
fresh census and revised lifetime proof.

| Source | SHA-256 |
| --- | --- |
| `src/targetBinding.ml` | `3fed72285b9cbf61b2f1013e44812a2dcada84be02815fdd6894f11afa762231` |
| `src/finalPublication_stubs.c` | `0ec93d78d3c94a8e1dc613f84f47577f2f93f689a76ee6657cb52cbd9088b238` |
| `src/stagePublication_stubs.c` | `f292e14692347583ae42a5ca4ee3bf0181f9f00446feccabbdbe927b31610474` |
| `src/copy_stubs.c` | `8478e89400128ba53500e3d78e4e8eab854ad744ffc3a886a6d5b037c9d8760b` |
| `src/copy.ml` | `825b0fd8b721cdcf24715924746e676807bdf109b1a9dc477dd4d5f7a9cc0082` |
| `src/semanticSync.ml` | `e8e2b14042ea9b8785f08a987c37929978d5067485ab1c32210c44a8120a27b3` |
| `src/semanticRemote.ml` | `0dec71478fea4d1a34bb02482f0b21d21f0df15d8576bb764da6316f65203d9b` |
| `src/semanticWorkers.ml` | `5cbfe5f34746797f9af57a71b0045549fe6a7387b5c5ec13eea4acd4156c1c73` |
| `src/semanticFile.ml` | `2526e9334c5ca6cb34be2d0e2c4d1ee43fbc067b5177fa0cacb54a8ecf279372` |
| `src/semanticDelta.ml` | `0723ba20acc53fd3a0e7e55355420fa354df468ad5c3a2b896115448bb34b7a2` |
| `src/semanticRuntime.ml` | `aa4a89c459e171807e4f7ea38009ab155d5cfe53f1b4155881284dc24dc751cd` |
| `src/candidateValidation.ml` | `a5cd5a8265387a0733280df3c1030243da1edf69c854c3c06693cc54e4f870d9` |
| `src/dngValidation.ml` | `657e9e858e897950b026a23b768dd26d1510e48f5893579a08c51c3c5bc4735a` |
| `src/helperSupervisor.ml` | `d13911bbcd5b12b2c2abe3a34a0b0a450366f2a387701b808452e830ee0ac78a` |
| `src/helperSupervisor_stubs.c` | `8b09080d7c743ae781ad3c9420ea6b7fc5da5df58587f4d84ffb6ab834fec9e4` |
