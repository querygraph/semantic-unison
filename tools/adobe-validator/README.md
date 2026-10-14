This optional, read-only driver invokes Adobe DNG SDK 1.7.1 build 2724 directly.
Unison runs it through `HelperSupervisor` and accepts its versioned receipt via
`DngValidation`. It is separate from the stock `dng_validate` CLI and from
Lightroom's proprietary Validate UI.

Native object reuse now checks compiler, options, selected compiler environment,
source/transitive-header contents and object contents. Clang dependency rules
include system headers and support escaped spaces/dollar signs. Build inputs
are checked around compilation; observed changes reject the object. This is
not an atomic source snapshot against an uncooperative writer. Keep the SDK and
adapter inputs stable during a build. Missing/corrupt cache receipts rebuild;
old timestamp-only objects are not silently accepted. JPEG XL still uses its
separate CMake dependency machinery, and every driver link remains explicit.
Cache checks do not qualify an SDK binary or change the production v1 protocol.

Run the Adobe-free cache controls with
`python3 tests/native_object_cache/run.py`. They compile tiny original C files
without executing them and include the actual builder function plus its previous
stale-cache counterexample. No SDK link/load/runtime test is performed.

Obtain the [official Adobe SDK](https://www.adobe.com/go/dng_sdk) and read its
`LICENSE.txt`. Keep the unpacked SDK outside this repository. This directory
contains original adapter/build/test code, and does not vendor Adobe sources.
The SDK license permits use and modification while requiring its notices to be
retained when distributing its source; review all bundled dependency licenses
before distributing a built binary. The build keeps source/notices in place.

On macOS with Command Line Tools, Python 3, and CMake installed:

```
python3 tools/adobe-validator/build.py \
  --sdk-root /absolute/path/dng_sdk_1_7_1 \
  --build-dir /absolute/path/adobe-validator-build --jobs 12
python3 tools/adobe-validator/qualify.py \
  --build-dir /absolute/path/adobe-validator-build
```

No Xcode.app or SDK installation is required. The build reads Adobe's Xcode
source manifests and compiles static XMP, JPEG, and JPEG XL dependencies. The
qualified target uses embedded XMP support, `qDNGValidate=1`, and SDK error
reporting; unrelated XMPFiles/DocOps features are disabled. Native Windows and
Linux build recipes are not yet qualified. Use a fresh build directory after
changing SDK headers or dependency versions.

The build writes `build-manifest.json` containing the executable SHA-256 pin,
build ID, and SDK location. Qualification adds a result and writes the generated
fixtures, stderr, receipts, and `qualification.json`. Only use the resulting
pin after qualification passes. Set the requested policy in the synchronizing
client's normal profile:

```
adobevalidate = require
semanticworkers = 0
```

Configure the driver separately on each endpoint that receives DNG files. Put
these settings in that host's reserved `endpoint.prf`, inside its Unison
configuration directory (`$UNISON`, or `~/.unison` by default):

```
adobevalidator = /absolute/path/adobe-validator-build/unison-adobe-validator
adobevalidatorhash = <executable_sha256 from build-manifest.json>
adobevalidatorbuild = unison-sdk171-2724-v1-single
adobevalidatorthreads = 1
adobevalidatetimeout = 300
```

`endpoint.prf` is optional and accepts only these endpoint-local settings,
including any files it includes. Other settings, such as `adobevalidate`, roots,
or `semanticworkers`, are rejected there. A normal client profile can override
its own endpoint defaults; client command-line options take final precedence.
Each server connection reloads its host's `endpoint.prf` and applies its own
startup driver options, such as `unison -server -adobevalidator ...`. For SSH,
install the file in the remote host's configuration directory, or have a local
server wrapper pass these options to Unison. The client never transmits driver
paths, pins, build IDs, thread counts or timeouts, and a receiver ignores such
values sent by an older client. Different hosts can use different qualified
builds. The requested `off`, `warn` or `require` policy still applies to both
receiving endpoints; `require` rejects a receiver with no local driver.

`semanticworkers = 0` uses physical cores on macOS, with logical CPUs as the
fallback elsewhere or if topology is unavailable; a positive value overrides
the budget. This driver accepts only
`--threads 1`, allowing many independently admitted files to use all cores.
It rejects other thread settings. `warn` permits validator findings explicitly;
`require` blocks an unavailable tool or failed validation. Candidate mutation
and cancellation reject under either policy. Validation runs before commit on
each receiving path, independently of whether semantic transfer was used.
See [the protocol](../../tests/helpers/README.md) for the exact argv and receipt.

The SDK host's default `PerformAreaTaskThreads()` is one. The SDK explicitly
passes that cap to `JxlResizableParallelRunnerSetThreads`; the bundled runner
subtracts one before creating workers and includes the caller in the total.
Consequently the one-thread host creates zero JXL worker threads. The default
hardware-concurrency helpers exist in libjxl but are not called by this SDK
decode path. The JPEG and embedded XMP paths do not create worker threads.
Changing the host or codec runner requires repeating this budget audit.

The repository also contains an **unqualified, source-only** capped area-task
host. It does not change the default build or enable additional threads in
Unison. An explicit `build.py --experimental-area-task-host` selection produces
`unison-adobe-validator-area-unqualified`, a separate
`build-manifest-area-unqualified.json`, and build ID
`unison-sdk171-2724-v2-area-unqualified`. Use a fresh build directory for this
variant. Its entrypoint is
`--unison-dng-validation-area-source-v0`, which the production v1 caller never
sends. Installing or pinning this artifact therefore cannot silently enable a
multithread validator. This variant has not been linked or run in the source
qualification below, and it must not replace an endpoint's qualified driver.

The adapter overrides the SDK's actual `PerformAreaTask` and
`PerformAreaTaskThreads` interfaces. It accepts an explicit total allowance of
1..128 threads, including the caller. An explicit one-thread host delegates to
the SDK's original execution path. For a parallel area task, its strip plan
honors `MaxThreads`, `MinTaskArea` and `UnitCell`; the SDK's `ProcessOnThread`
continues to apply repeating-tile boundaries, tile iteration and maximum tile
size. `Start` receives the actual partition count. Every created worker joins
before `Finish`, which receives the same count. A completed `Start` gets one
`Finish` even after processing or thread-creation failure; a failing `Start`
retains the SDK's own partial-construction cleanup convention. The first task
error survives a secondary finalization error.

Area-worker, startup and finalization scopes report one thread to nested area
tasks and codecs. This matters because SDK tiled reads can decode JPEG XL from
inside an area worker. Returning the full allowance there would multiply both
sets of workers. Top-level JPEG XL decoding receives the requested total
allowance; the bundled runner includes its caller and creates at most allowance
minus one workers. Area threads are created per synchronous task and joined,
so an idle persistent area pool cannot overlap a subsequent top-level codec
runner. The endpoint must reserve the entire requested allowance in Unison's
shared CPU-credit budget before invocation; this source adapter does not acquire
credits from the parent process itself.

Worker failures request cooperative cancellation of the other workers. The
shared abort wrapper checks this request at SDK sniff points and forwards an
existing sniffer's cancellation checks, serializing delegates which do not
declare `ThreadSafe`. Tile-progress notifications are serialized. Cancellation
does not interrupt arbitrary SDK work between sniff points, and runtime timeout
and subprocess settlement remain the caller's responsibility. The current
validator uses no custom sniffer or progress reporter. The wrapper does not
claim to forward protected nested sniffer task/progress notifications; a future
host exposing those notifications needs a separately qualified adapter contract.

Only the generic scheduler, which contains no Adobe or codec code, has been
executed. Its controls cover 1/6/18/36/128 allowances, disjoint rectangle
coverage, task constraints, signed-coordinate bounds, caller accounting,
nested allowances, startup/worker-launch/processing/finalization failures,
cooperative cancellation and joining before cleanup. AddressSanitizer and
UndefinedBehaviorSanitizer pass, and deliberately removing the nesting cap
fails the controls. Compile-only checks against the actual separately obtained
SDK headers verify both driver modes without linking or loading the SDK:

```
python3 tests/area_scheduler/run.py \
  --sdk-root /absolute/path/dng_sdk_1_7_1 \
  --dependency-build-dir /absolute/path/existing-adobe-validator-build
```

This command never executes the SDK driver, fixture writer, codec or Lightroom,
and writes its artifacts and source-pinned receipt to a private temporary
directory. See [the scheduler source review](AREA-TASK-SOURCE-REVIEW.md).
Real SDK output equivalence, tile-layout/codec coverage, allocator/task safety,
actual thread counts, cancellation and performance still require a coordinated
finite invocation window. Successful source controls are not a production
capability advertisement. A later versioned caller capability and endpoint
qualification must be added explicitly after those runtime checks.

The driver independently hashes the entire candidate before and after decoding,
parses SDK structural metadata and embedded XMP, decodes the original stage-1 raw
image (not an enhanced-image substitute), reads associated masks, and checks
each present RawImageDigest and NewRawImageDigest. A present all-zero digest is
a mismatch; missing optional digest tags remain distinct from corruption.
Transparency-mask compression whose digest behavior is not qualified returns
`unsupported`. Stage-2/3 rendering, all previews, OriginalRawFileData, and
Lightroom's UI behavior are outside this validator's stated scope.

SDK `ReportError`/`ReportWarning` calls are counted by explicit function
interposition at compile time; no stderr text matching is used. The XMP toolkit
can silently recover from XML parser errors by default, so a strict global XMP
error callback also records and rejects them. SDK stdout is redirected to
bounded stderr, leaving stdout exclusively for the receipt. Findings return a
receipt even with exit zero, ensuring the caller must examine the error count
and all statuses. The driver exposes no write, output, or render options.

Qualification generates small synthetic CFA DNGs, checks valid old/new/both
digests, valid XMP, missing tags, actual lossless JPEG and JPEG XL compression,
and rejects altered raw samples/digests, all-zero tags, malformed XML, and bad
structure. The separate `fixture-writer` creates codec fixtures and is never
invoked by Unison. No real photographs or Lightroom UI are used. These fixtures
establish the tested cases; they do not establish coverage of every DNG variant.

Primary implementation evidence in the separately obtained SDK:

- `dng_sdk/source/dng_negative.cpp`: `ValidateRawImageDigest` and embedded XMP parsing.
- `dng_sdk/source/dng_exceptions.cpp`: reporting functions do not imply a failing exit status.
- `dng_sdk/source/dng_host.cpp`: default area-task execution and thread count.
- `dng_sdk/source/dng_jxl.cpp`: explicit resizable decoder runner thread cap.
- `libjxl/libjxl/lib/threads/resizable_parallel_runner.cc`: total-thread semantics.
- `xmp/toolkit/source/XMP_LibUtils.hpp`: recoverable-error behavior and callbacks.

An additional source-only host allocation adapter uses the SDK-independent
`memory_budget.h` quota and `memory_allocator.h` SDK callbacks. Multiple adapters
can share an injected quota rather than multiplying capacity. The quota accounts
requested backing storage, headers, block objects and SDK physical padding.
`Allocate` uses SDK memory-full/overflow behavior; codec `Malloc`/`Free` callbacks
never unwind C++ exceptions through C. Buffers retain accounting state through
release, and the synchronous driver owns the allocator through joined tasks.

`--experimental-memory-budget` selects separately named unqualified memory or
area-memory artifacts/manifests. Their argv protocols require explicit
`--host-memory-bytes` and differ from the production v1 protocol. Current Unison
cannot enable them as production v1. The known qualified v1 executable is not
rebuilt by source-only checks. Actual SDK/codec parity and runtime resource/thread
measurements remain required before a versioned caller enables these modes.

Coverage is limited to the host allocator and its SDK JPEG XL bridge. Direct
`dng_memory_data`, XMP/ordinary heaps, thread stacks and allocator caches remain
outside this pool, so it is not a full process/RSS cap. The
[pluggable resource contract](../../doc/backend-resource-interop-v0.md) records
shared core-admission integration and remaining coverage. The
[source tests](../../tests/sdk_memory/README.md) run no Adobe or photograph.
