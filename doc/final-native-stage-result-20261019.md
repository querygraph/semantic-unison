# Current native clone-stage qualification

Both stock OCaml and OxCaml passed the directed native matrix. Actual owning
session `5267` returned terminal `cfd95f`, exit 0, no running session. All 50
compiler/native/metadata children settled: 46 exited 0 and four expected native
refusals exited 77. The metadata store and Unison8/EXglobal leases closed.

The probes link the same `copy_stubs.o` objects previously bound to the current
production builds and final rsync qualification. Current build receipts, 329
production source inputs, 170 harness inputs, selected compiler/library hashes
and native-object hashes are checked before and after execution. The original
`clone_stage.ml`, `clone_stage_status.ml` and `test_clone_stage.py` test bodies
are unchanged. A source-bound bridge gives their child calls retained ownership
and preserves their private temporary fixtures instead of deleting them on exit.
Only one compiler job runs at a time.

| Case | Actual behavior checked on both compilers |
| --- | --- |
| FIFO without writer | Prompt legacy refusal, no output/snapshot leftover. |
| Read-only regular source | Private writable stage, distinct snapshot/stage inodes, snapshot link count zero, original source mode preserved before deliberate fixture mutation. |
| Source modification/open snapshot | Held snapshot bytes survive deliberate live-source rewrite; stage changes do not alter snapshot bytes. |
| Xattrs and resource fork | Stage has no inherited xattrs or old native resource fork. |
| ACLs | Read-allowing and write-denying source ACLs are removed only from the private stage; the protected live source remains protected. |
| Existing target | Repeated native collisions preserve existing target bytes and report the precise error phase. |
| Source flags, nonregular input, missing parent, symlink | Strict refusal/error scope and phase; no inappropriate created names. |
| Native descriptors | Strict probe compares `/dev/fd` counts after repeated outcomes and major GC. This is not a whole-process peak-descriptor measurement. |
| Real sparse input | Native snapshot preserves all 1 MiB of expected bytes after live-source mutation, including the zero interior and patched prefix. Source and stage each report 16 blocks; no physical-sharing/write claim follows. |

The first attempt passed the stock ordinary/status prefix, then correctly held
before its sparse native call because its generated file was not sparse. It
was independently recovered after all 24 original children were proved settled;
actual outer exit `24444/83daa3/137` is preserved, not relabeled normal exit.
The old source and prefix remain under
`tests/qualification/final-native-stage-v1-failed-recovery-20261019.json`.

A separate five-case generated-file control (`465356`, exit 0) found that
`ftruncate`, pwrite extension and seek/write extension all reported full
allocation on this host, including a 16 MiB example. Explicit Darwin
`F_PUNCHHOLE` returned success, preserved the exact bytes and reported 16 blocks
for the 1 MiB file. The constant and 24-byte `fpunchhole_t` layout were verified
in the installed macOS SDK header. The corrected fixture punches only its own
fresh generated zero interior. It neither weakens the sparse prerequisite nor
modifies production source or borrowed inputs.

The independent post-closure audit (`2a4ba1`, exit 0) checked all 50 exact child
argument vectors and group proofs, four designated 77 outcomes, canonical nine
resource inodes, all source/object/toolchain pins, and 2,146,342 bytes of freshly
read complete stage/source outputs. Generated probe/source hashes are retained
as post-execution observations, not invented pre-exec hashes. It independently
acquired and closed the entire Unison8/EXglobal bundle.

[Actual receipt](../tests/qualification/final-native-stage-v2-actual-20261019.json)
and [exact plan](final-native-stage-plan-v2-20261019.json) retain raw references.
[Generated sparse-creation control](../tests/qualification/generated-sparse-creation-actual-20261019.json)
preserves both the successful and unsuccessful creation methods.

This closes the current native ABI/property/sparse-snapshot execution binding.
It does not qualify every end-to-end synchronization property transition,
compressed inputs, crash durability, other platforms, physical extent sharing,
SDK validity, photos, pixels or production deployment. No Photo original,
catalog/cache, Adobe SDK or mounted image was accessed by this matrix.
