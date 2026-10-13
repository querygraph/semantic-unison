This optional, read-only driver invokes Adobe DNG SDK 1.7.1 build 2724 directly.
Unison runs it through `HelperSupervisor` and accepts its versioned receipt via
`DngValidation`. It is separate from the stock `dng_validate` CLI and from
Lightroom's proprietary Validate UI.

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
