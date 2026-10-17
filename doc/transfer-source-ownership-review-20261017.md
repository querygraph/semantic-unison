# Semantic transfer ownership review — 2026-10-17

The source half and receiver half have different owners. A passing source report
control does not prove receiver-stage cleanup or actual RPC settlement.

## Source planning

`SemanticRemote.make_plan` now uses the same `with_owned_source` helper as
ordinary semantic reports. The helper opens a regular source through the portable
close-once owner, waits for borrowed worker completion, settles before delivering
the result, and preserves the operation cause on cleanup failure. Uncertain close
keeps the carrier and an unresolved promise inside `source_scope`'s existing
Source transaction. Encoding and queued RPC output remain covered by that outer
scope. It does not receive peer code or change the wire format.

The production-linked ordinary report control exercises this exact helper's
normal and injected-close paths. Source-plan integration is source-reviewed and
compiled, not a fresh actual transport/failure execution. The separate frozen
property request does not use this newer source and cannot qualify it by proxy.

## Receiver cleanup still to address

The receiver retains a separate `held_files` owner for basis/output descriptors.
`close_files` consumes numeric descriptors once and attempts all closes, but it
raises only the first Unix error. `cleanup` suppresses that error and can proceed
to unlink an owned stage. Callback error cleanup also uses suppressed release.
That is not the retained-uncertainty protocol now used by read-source owners.

`StagePublication` separately owns native working-directory/parent/witness FDs.
Its C `close_slot` clears each slot before close (no numeric retry), but retains
only a first error when a collector is supplied. Disarm and some preparation/
finalizer paths intentionally suppress close errors, as its current interface
states. Changing only the ML candidate owner would therefore not prove complete
publication ownership. Native state/evidence and the ML transaction owner must
be revised together, preserving the original operation cause, every uncertain
close identity, remaining known handles, and the actual name-ownership phase.
A published name must not be retried, overwritten, or reported rolled back merely
because proof-handle cleanup failed. Unknown ownership must prevent a normal
resource release; finalization must not retry uncertain numeric descriptors.

Next qualification should use disposable native fixtures and copied fault stubs,
including multiple close failures and operation-plus-close failures, before any
fresh coordinated transport run. Do not use camera originals, reinterpret an
old admission, or treat this review as a new IO/native grant. Existing normal
publication and original historical tests remain evidence only for their actual
scope; they do not establish these new uncertainty cases.
