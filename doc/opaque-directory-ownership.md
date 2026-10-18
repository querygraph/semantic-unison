# Opaque directory ownership

`DirectoryOwner` prepares a carrier, retention link and monomorphic handle slot
before `Unix.opendir`. `System_generic` prepares the returned callback record
before acquiring the handle, retaining the existing `dir_handle` record interface.
The actual returned `Unix.dir_handle` goes into its typed private GC-root slot
without allocating `Some`; the unopened placeholder is never interpreted as a
handle. Known open owners remain rooted until known close. The underlying Unix
stub's own failures before returning a handle are still its acquisition boundary.

A close consumes its authority before entering `Unix.closedir`. Failure preserves
the opaque owner, acquisition path, original operation failure and close failure.
No numeric descriptor is guessed; the path is not an inode identity assertion.
Repeated cleanup raises the same carrier without calling `closedir` again, even
when the first error followed actual kernel settlement. Known close removes the
owner root. There is no reset, forged-settlement or uncertain-owner release API.
This is cooperative owner-loop code, not a sandbox against arbitrary callers.

`System.with_directory` / `Fs.with_directory` scope the callback and close together.
On scan/budget/cancellation failure they preserve that error while attempting the
close once; uncertainty supersedes ordinary failure as the carrier and retains
both causes. Callback/publication metadata exists before acquisition. The Windows
wrapper retains its wildcard-path refusal before invoking the same scoped owner;
its fsmonitor link list must include DirectoryOwner before System_generic.

CandidateValidation uses the scoped wrapper for enumeration and guards its complete
tree promise, including legacy unadmitted manifests. A recognized directory carrier
therefore cannot become an ordinary completed/failed tree and release a surrounding
publication borrower. Positive manifest admission also recognizes that carrier
inside SemanticRuntime.with_admission. The standalone guard acquires no admission
and does not invent credits for legacy unadmitted accounting.

## Qualification scope

Fixed controls must exercise actual CandidateValidation.before_commit with trusted
original synthetic TOY0 validators, not an isolated mock of the admission gate.
Cover known enumeration and original read error, cancellation, acquisition and
wrapper/publication failures, before/after actual closedir failure, combined read
or cancellation and close errors, repeated cleanup and independent replacement
opaque handles. Check known FD census, admission retirement only on known paths,
unchanged synthetic source identity/bytes, and retained tree promises for both
positive and legacy-zero manifest budgets. Deliberately removing the tree guard
or raising an ordinary close error must fail designated assertions. Compile the
Windows Core signature separately; that is not native Windows runtime proof.

The runtime evidence file records actual outcomes; this source contract is not by
itself evidence of passing tests. Unknown injected owners settle at process exit,
not by a claimed normal closedir. Other legacy opendir callers still need their own
complete borrower/error-path review; a prepared System wrapper alone does not prove
every directory consumer's lifetime. Aggregate descendant FD/RSS, complete baseline
accounting, broader benchmarks and final SOL integration remain separate work.

## Actual checkpoint — 2026-10-18

Evidence: tests/qualification/directory-owner-actual-20261018.json. Stock and
OxCaml Make/Dune builds and selftests pass on the same329 production hashes.
All26 directory cases and4 designated bad-implementation rejections pass, along
with both fixed in-process tree suites. Current Runtime I/O(12+4negative),
reader(24+4negative) and pool(20+4negative) controls pass. Windows wrapper/Core
signature compile checks pass on this Darwin host; no Windows runtime claim.

Build parent24471/1439af/0 and remaining-control parent67451/d4706b/0 are actual
terminals/no sessions. Stock directory controller99165 itself passed0/closed,
although its outer driver13332/55d9ae exited1 at a later unrelated historical
fixture compilation; the receipt preserves that distinction. Initial harness
path collision, synchronous-negative assertion, combined60s timeout and obsolete
historical interfaces are preserved with their actual known process settlement.
No failure was reclassified as a normal pass. Historical Runtime comparisons use
only an uncalled compatibility export; the historical tree budget comparison uses
a destination context-field compatibility addition and its real old interface,
and refuses before that context is used.

All owned groups and CPU scopes closed; no EXglobal/Photo/SDK input. Next review
legacy Os.childrenOf and Files.get_files_in_directory complete borrowers, rather
than inferring their exception cleanup from the prepared underlying wrapper.
