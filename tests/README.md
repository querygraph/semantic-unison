# Semantic extension qualification

Tests create synthetic files in disposable directories. They do not inspect
personal photographs, modify production profiles or require a real SSH server.
Build each compiler in its own snapshot:

```sh
python3 tests/build_snapshot.py --compiler-prefix /absolute/compiler/bin --selftest
python3 tests/semantic/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/report/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/workers/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/helpers/run_tests.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/admission/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/lwt_close/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/copy_range/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/clone_range/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/file_observation/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/clone_lease/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/clone_handles/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/stage_publication/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/test_clone_stage_status.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/test_clone_stage_signals.py --ocamlopt /absolute/compiler/bin/ocamlopt
```

The snapshot builder prints the build directory. Use its `src/unison` for the
following tests:

```sh
python3 tests/test_clone_sync.py /absolute/build/src/unison
python3 tests/test_semantic_remote.py /absolute/build/src/unison /optional/old/unison
python3 tests/test_semantic_reports.py /absolute/build/src/unison /optional/old/unison
python3 tests/test_validation_sync.py /absolute/build/src/unison
python3 tests/test_validator_config.py --unison /absolute/build/src/unison \
  --legacy-sender /optional/pre-fix-feature-branch/unison \
  --old-peer /optional/unmodified/unison
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_endpoint_prefs.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_local_clone.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_remote_bounds.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_socket_reconnect.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_generic_format.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_report_details.py /absolute/build
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_nonblocking_open.py /absolute/build --negative-control
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_clone_adoption.py /absolute/build --negative-control
python3 tests/test_clone_bound_range.py /absolute/build --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/test_clone_bound_range.py /absolute/build --ocamlopt /absolute/compiler/bin/ocamlopt --negative-control
python3 tests/test_clone_publication.py /absolute/build --ocamlopt /absolute/compiler/bin/ocamlopt --keep-work
```

Omit optional binary arguments when unavailable. Validator configuration tests
give the two endpoints separate configuration directories and distinct driver
paths, pins and build IDs. The legacy sender still transmits helper settings,
exercising the receiver's incoming-value protection. The preference tests also
cover aliases, malformed incoming values and local profile/CLI precedence.
The generic-format
suite injects one trusted synthetic registration into a private test binary
and exercises the unchanged transfer machinery. Compiler arguments must match
the snapshot being linked. APFS tests require a filesystem supporting cloning;
see [CLONE.md](CLONE.md) for native property tests and platform limits.

The report suites check [bounded SIR/0 descriptions](../doc/semantic-report-v0.md)
and escaped metadata byte previews, then request real CLI diff/details on local
and remote current file pairs. They preserve existing conflict choices and file
bytes, exercise old-peer unavailability and ordinary text-diff fallback, and verify that a second format
uses the same reporting path. Details observations are consumed once; changed
or replaced local files, other rows and disconnects invalidate them. Reporting
does not infer changes against an archived base or authorize synchronization.
Supply the unmodified old-peer binary to `test_semantic_reports.py` to exercise
the negotiated-unavailable report and ordinary text fallback as well as the
local and remote current-pair cases. `test_report_details.py` checks local
stamp freshness, replacement, followed links and one-shot consumption.

The nonblocking-open suite gives synchronous/async source inspection, source
planning and validator candidate/executable snapshots disposable FIFO paths.
It checks prompt regular-file rejection, clean descriptor/admission/CPU state
and exact follow-up work. Its optional private old-open controls reproduce the
former blocking behavior under a timeout; production sources remain unchanged.
The [copy-range suite](copy_range/README.md) independently injects short/zero/
invalid native progress, unsupported and operational errors, and callback or
cancellation exceptions, checking exact suffix fallback and progress counts.
The [constrained clone-range suite](clone_range/README.md) independently checks
alignment, bounded streaming, exact progress, scoped fallback and fresh injected
identity/generation observations. Its 48 named tests include 960 geometry cases;
it does not supply a native mounted-volume observer or qualify ZFS/ReFS.
The [held-descriptor observation suite](file_observation/README.md) qualifies
macOS file/volume facts separately: independent stat/utime values, validated
UUID attribute buffers, error phases, replacement, unchanged offsets and
descriptor retention. The [borrowed-lease suite](clone_lease/README.md) connects
those native facts to the range executor, checks fresh identity/constraint and
owner-epoch fences, and uses ordinary positional copying to verify bytes and
sentinels. Neither suite establishes immutable bytes, mount-incarnation identity
or pathname publication.
The bound-range caller suite compiles the full production `Copy` source as a
private test module, hooking only its native copy step against compiler-matched
snapshot objects. Real leases, channels, bounded planning and fallback remain
unchanged. It checks shifted/chunked offsets, short progress, exact unsupported
suffix copying, quiet fallback EOF, operational failures, stale bindings,
descriptor mismatch and channel-position reconciliation. Its private negative
control removes reconciliation and must fail. These are ordinary copying tests;
no shared-block or physical-write receipt is inferred.
The [creation-parent suite](clone_handles/README.md) checks the additive
three-descriptor native clone result while preserving both older ABIs. It
verifies the actual retained parent after replacement, descriptor/property
contracts, scoped declines, operational failures and cleanup.
The [publication suite](stage_publication/README.md) checks the finalizable
native owner, retained stage witness, fresh directory/name bindings, exclusive
rename, post-rename ownership, and identity-bound cleanup. It covers separate
and followed parents, search-only permissions, sibling directory changes,
collisions, hardlinks, native errors, descriptor reuse and a scoped pending
signal after successful rename. Preparation-only unavailability permits no
later-phase or operational fallback. These tests qualify the intermediate
stage-to-normal-temp boundary; final live commit, logical root/followed-target
binding and crash durability remain separate.
The publication caller harness uses the full frozen production `Copy` source,
actual native ownership and rsync compressor/decompressor through receiver EOF.
Its private seams inject preparation, creation/adoption, channel and registry
failures, collisions, parent rebinding, and exceptions after successful native
rename but before disarm. It also checks ordinary reference FIFO rejection and
descriptor reuse. `--keep-work` retains generated sources and logs; a separate
`--negative-control` run must detect removed publication cleanup. The harness
qualifies this caller boundary and preserves the old live destination; it does
not qualify final `Files.renameLocal` publication.
The strict clone-stage suite exercises the production macOS C stub directly:
separate private descriptors, declined source kinds/flags, phase-specific
operational errors, existing-output preservation, cleanup and the legacy ABI.
It requires a clone-capable disposable filesystem and skips unavailable native
staging; it does not modify mounted photo volumes.
The signal suite privately instruments allocation counters and injects a pending
`Sys.Break` while path buffers are owned. A declined-stage path frees all buffers;
restoring the old release call in a separate negative control exposes three
leaks. It uses the pinned Ox runtime's explicit asynchronous exception boundary
when available, and does not qualify successful-result asynchronous handoff.
The adoption suite compiles privately instrumented production functions against
the matching snapshot's objects. Controlled synchronous Failure/Out_of_memory
exceptions exercise channel, ownership-record, registry and source-FD handoffs,
including a throw after registration. Checks cover FD/stage cleanup, preserved
source/exception, reused descriptors surviving connection cleanup and usable
follow-up work. Private old-handoff controls reproduce the former leaks. These
controls do not impose real memory exhaustion or arbitrary asynchronous delivery.

The socket reconnect suite runs the production persistent socket command loop
with a deterministic source command. Its first client withholds half-duplex
write permission until replies saturate resource admission, then disconnects.
The next client verifies the same server PID, exact replies and released
transaction/payload/descriptor credits. `--negative-control` removes the socket
output-stop call only in a private source copy and reproduces the old leak.

```sh
OCAMLOPT=/absolute/compiler/bin/ocamlopt python3 tests/test_socket_reconnect.py /absolute/build --negative-control
```

The helper suite uses a synthetic protocol implementation to exercise process
supervision and failure handling. It does not establish Adobe behavior. After
building and qualifying the [actual SDK driver](../tools/adobe-validator/README.md),
test its receive gate separately:

```sh
python3 tests/test_adobe_sync.py --unison /absolute/build/src/unison \
  --sdk-build /absolute/adobe-validator-build
```

The final publication suites separately test native descriptor ownership,
endpoint-local ticket phases, actual semantic workers, and the production
Files/CLI caller. Build a fresh compiler-matched snapshot first for the two
integration runners; use disposable fixtures and an installed old peer.

```sh
python3 tests/final_publication/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/target_binding/run.py --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/test_semantic_handoff.py /absolute/build --ocamlopt /absolute/compiler/bin/ocamlopt
python3 tests/test_final_publication.py /absolute/build --ocamlopt /absolute/compiler/bin/ocamlopt \
  --old-peer /absolute/old/unison --keep-work
```

Native producer tests distinguish newly supplied output descriptors from
admitted resume files. Neither native identity nor a ticket authenticates
bytes: actual final fingerprints and the ordinary source check remain
required. These checks guard cooperative namespace changes, with explicit
legacy handling for transactions involving additional names. They do not
qualify hostile lookup/rename races, general first-admission cleanup or a
descriptor-relative resource-fork creator.

Each suite verifies a different boundary: semantic preservation and envelope
bounds; domain ownership and cancellation; helper admission and teardown;
transaction resource budgets; pending I/O settlement and descriptor reuse; file
cloning and normal Unison lifecycle; negotiated peer compatibility; and
precommit validation. Correctness tests do not establish throughput, physical
write amplification, crash durability, Lightroom UI parity or full DNG corpus
coverage. Current evidence and remaining work are recorded in [SOL.md](../SOL.md).

The semantic runner now includes independent SDE/SDR conformance by default:
`tests/semantic/conformance/` contains pinned binary goldens, an independent
Python codec/transcript, boundary recipes and production rejection/materialization
controls. `--skip-conformance` is available for a focused original-kernel run.
`tests/xmp_observation/` independently qualifies the advisory XML subset and
encoding/context transcript. `tests/report/` covers SIR/0 and SIR/1 bounds and
comparison scope. `tests/test_semantic_meaning.py` exercises actual local/remote
worker/CLI paths with synthetic DNGs and a preceding SIR/0 binary.
`tests/area_scheduler/` runs an Adobe-free C++ scheduler and compiles the two
SDK adapter modes only to unlinked objects; this source receipt is not actual
SDK runtime qualification.
