# Current named receiving suite — actual result

Both compilers PASSED the complete original 21-case named receiving suite on
2026-10-19 at source `10c5d159`: stock (`current-named-receiving-stock-20261019-04`)
and OxCaml (`current-named-receiving-ox-20261019-04`). Each run: 69 CLI calls,
54 fake validator calls, 9 external copies, 7 merges, 4 deliberate receiver
interruptions and 2 client SIGINT cancellations, each audited from raw captures
by the owner while it still held EXglobal IO and CPU00..07, then closed. An
independent post-closure replay under CPU04 matched both owner audits exactly.
[Receipt](../tests/qualification/current-named-receiving-actual-20261019.json).

## Product defects found and fixed by these runs

1. `a5fd1bfb`: when the client exits on a lost connection, running external
   copy/merge helpers are killed and reaped by the exit-time teardown, which
   logged nothing. It now reports a Cancelled `External result` once.
2. `defd5732`: that report's group census ran before the killed leader had
   exited, so it was always `unknown`; it now waits up to one second. Unison
   traces OCaml signal constants (SIGTERM -11, SIGKILL -7), which the harness
   now decodes instead of assuming POSIX numbers.
3. `10c5d159`: a merge whose second publication is rejected left the replicas'
   archives different, and Unison aborted the whole sync with "Internal error:
   New archives are not identical". The first replica's archive entry is now
   restored; the item fails with exit 2 and the next sync merges again.

## Failed predecessors (preserved, not replayed)

Stock `-01`, `-02` and `-03` each have `FAILED-RECOVERY-CLOSED.json` with saved
process, descriptor and workspace evidence. Only idle Python controllers were
stopped, by exact PID, after confirming no Unison, helper or group remained;
locks were then freshly acquired and closed. Unadmitted Ox `-01..-03` plans are
superseded.

## Scope

Generated tiny files, fake validators and fixture copy/merge programs only. No
SDK, camera payload, Photo/Lightroom, performance, or crash-durable publication
claim. The cancellation cases did not need an exit-time validator record.
