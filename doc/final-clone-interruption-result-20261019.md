# Current receiver-clone interruption and recovery

The current stock and OxCaml binaries passed a fresh generated-file scenario:
2MiB seed, replace source with8MiB new bytes, observe a private receiver-clone
stage, interrupt only the still-owned native server, then recover and no-op.
Actual owning session61494, initial46d9d2, terminal84393d/exit0/NOsession,
PID59868. All eight calls and24primary peer roles settled. Six normal pairs
exited0; the two designated interrupted calls had client exit3 with the exact
lost-server diagnostic, proxy exit0 and server actual wait4 statusSIGKILL(-9).
The native server PID was still reserved/unreaped and its proxy group checked
before the single signal. No timeout or guessed PID caused a signal.

After each interruption, the live destination still contained the exact old
2MiB bytes. An open reader and a hardlink retained that old file through fresh
recovery. Recovery used the actual immutable receiver-clone path, produced the
exact new8MiB bytes, removed staging files, and published a different inode from
the abandoned partial clone. A subsequent synchronization preserved every
recorded target identity field. Only this disposable test's archive state used
`-ignorelocks`; user profiles and state were never opened.

The fault transport is test-only. It throttles forwarding enough to observe a
clone stage, sends SIGKILL only to its own reserved server PID, explicitly records
discarded protocol bytes after that event, drains EOF, actually reaps the server,
and closes pipes/sockets with the qualified uncertainty carrier. Its special
launcher propagates the intentional EOF. It does not claim successful protocol
completion or replace the production/ordinary transport. Unknown process or
close state retains owners and descriptors; no timeout cleanup kills peers.

## Independent audit

Auditc160ba/exit0/NOsession reparsed all eight raw pairs,24distinct recorded
client/proxy/server identities, native wait/group/EOF evidence and exact shim
commands. It rehashed542execution sources,329production bindings, current stock/
Ox/compiler/interpreter artifacts, and37,748,736B of surviving generated source,
replica and hardlink bytes. Source epochs and temporal held-reader preservation
remain bound to the original owner records. Fresh exact canonical Unison00..07
and EXglobal acquisitions/closures matched the original nine identities. All
resources are released; this is not an OS-process absence inference.

[Immutable V3 plan](final-clone-interruption-plan-v3-20261019.json),
[actual audit](../tests/qualification/final-clone-interruption-v3-actual-20261019.json),
[audit terminal/source](../tests/qualification/final-clone-interruption-audit-terminal-20261019.json).
Nine original controls passed581fe3/0: reserved-PID signal order, no signal for
terminal/wrong-group peers, stage identity, actual socket/pipe EOF with original
injected signal, explicit hardlink reader, both log channels, uncertainty versus
known failed-prefix policy, and strict negative outcome/group audits.

## Preserved harness failures

V1 reached the intended server interruption and settled its seed/interrupted
pairs, then its single-link artifact reader rejected the deliberately hardlinked
live target. V2 fixed that reader and actually completed recovery, but checked
only client output for the clone marker; it was in the server/proxy capture.
Neither was a production clone failure. Each controller retained resources at
that point. Separate source-bound audits reparsed the known completed prefix,
verified no remaining owned child/group member, then stopped only the idle Python
controller. Actual owning terminals71464/de1bb4/137 and92422/f83abb/137 are
preserved, never reported as normal exits or complete passes. No original-child
wait was invented. V3's full-set reacquisition independently confirms release.

[V1 recovery](../tests/qualification/final-clone-interruption-v1-recovery-actual-20261019.json),
[V2 recovery](../tests/qualification/final-clone-interruption-v2-recovery-actual-20261019.json).
First and second owner source snapshots preserve their plan hashes. The V2 test
snapshot was reconstructed afterward by reversing exactly the two added controls
and import extension; its bytes match the pre-existing V2 plan SHA, without
claiming it was saved before execution.

The corrected harness now releases an ordinary failed prefix only after every
attempted peer is proven settled, closing its held readers once. Any live peer
or unresolved FD carrier still retains ownership. The shared strict artifact
reader was not weakened; only this generated fixture reader permits an exact
explicit link count of1or2.

No photo, SDK, Adobe, Main or cache payload was used. This is controlled peer
loss, not power-loss durability, a physical disk-full test, or all generic clone
edge cases. The legacy seven positive prefix/shift/EOF scenarios and flagged
basis policies remain separately mapped/renewed; this result does not silently
count them as executed.
