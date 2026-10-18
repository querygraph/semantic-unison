# Bound namespace publication timing

`FinalPublication.publish_timed` performs the same bound candidate/target checks,
exclusive-or-replacement rename and post-rename identity observation as ordinary
`publish`. Native publication state changes before result-stat errors or pending
exception delivery, so abort cleanup never mistakes an already published live
file for a disposable candidate. Neither entry point retries publication or
changes fallback policy.

The timed variant allocates its result float **before** looking up the rooted
native context or entering publication. Allocation failure therefore precedes
rename. Once publication starts, it records monotonic timestamps in native
locals and fills that already allocated float after returning from the native
blocking section. There is no post-rename diagnostic allocation in this API.
The ordinary variant allocates no diagnostic float and makes no clock calls.

The interval includes native mutex acquisition, candidate/target/auxiliary
checks, descriptor-relative rename, result observation and unlocking. It excludes
runtime release/reacquisition, receiver materialization/validation, later
`check_published`, archive advancement and resource closure. It is **namespace
publication timing**, not crash durability, total transfer commit latency or
proof of transfer success. This mechanism supports the qualified bound branch;
legacy pathname/sidecar branches remain unmeasured.

Clock calls preserve native `errno`. Unavailable, backwards, nonfinite or
invalid duration returns NaN rather than falling back to wall time or changing
an operation error. A native publication failure still raises its original
phased error instead of returning a successful timing sample. This currently
uses the existing macOS-only native bound-publication backend.

When `-debug semantic-timings` is enabled, Files selects the timed variant and
emits `Semantic bound publication native-inclusive-seconds=...` or an explicit
unavailable message. This can cover non-DNG bound transfers too; the trace tag
is not an eligibility or format claim. The event precedes later readback and
archive updates and must not be interpreted as full transfer success. Known
logging sink errors (`Sys_error`, `Unix_error`) and diagnostic allocation errors
are suppressed after native success. Other exceptions, including control
exceptions, propagate; the native published state still protects live output.
No filenames, content bytes, transferable ownership or archive authority are
included in this diagnostic record.

## Directed qualification

The original native publication/retained-producer lifecycle suite is run both
normally and through `publish_timed` on stock/OxCaml. It checks absent/existing
names, identity changes, concurrent-name refusals, native operation errors,
post-rename readback failures, pending exceptions and cleanup. Additional fixed
controls inject unavailable/backwards clocks and diagnostic-allocation failure
before publication. Ordinary publication must perform zero clock reads.

An exact-source reporter test compiles the Files diagnostic expression with
original fake trace/message sinks. Twenty-eight cases per compiler cover both
finite and unavailable durations, prefix/callback failures, known sink/OOM
errors and unrelated/control exceptions. A private catch-all regression must be
detected. This qualifies the local guard; it is not an actual sync benchmark.

See [actual qualification](../tests/qualification/bound-publication-timing-actual-20261018.json).
Whole-operation commit timing, end-to-end repeated samples, physical I/O and hard
aggregate RSS/FD bounds remain separate requirements. No Photo/source-camera,
SDK or existing sealed runtime is replayed to obtain these source-control proofs.
