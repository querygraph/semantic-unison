# Local build and test commands

Run from the repository root. Routine development uses the standing **Unison8 /
Photo8 / system2** policy. Unison owns only canonical CPU tokens00..07; Photo owns
08..15. Build jobs must fit inside the Unison grant, with **at most two compiler
jobs**. Both endpoints and owner overhead count when a test launches two replicas.
Credits coordinate participating owners; they are not an OS CPU or RSS hard cap.

Use the installed compiler-matched switches: stock OCaml under
`$HOME/.opam/default/bin`, OxCaml under `$HOME/.opam/5.2.0+ox/bin`. Do not use the
unrelated Homebrew compiler or change the selected opam switch. The qualified
local test interpreter is:

```sh
UNISON_TEST_PYTHON=/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14
```

## Complete CLI builds and self-tests

The shared dispatcher acquires existing canonical Unison tokens and retains
ownership through child/group settlement. Each `OUTPUT_DIR` must be fresh; an
existing directory is refused rather than overwritten or reused.

```sh
SHARED_CPU_CREDITS=8 JOBS=2 OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" \
  OUTPUT_DIR=/private/tmp/unison-local-ox-check-001 \
  "$UNISON_TEST_PYTHON" tests/manual.py ox-check

SHARED_CPU_CREDITS=8 JOBS=2 STOCK_PREFIX="$HOME/.opam/default/bin" \
  OUTPUT_DIR=/private/tmp/unison-local-stock-check-001 \
  "$UNISON_TEST_PYTHON" tests/manual.py stock-check
```

Run these sequentially. `ox-dune-check` and `stock-dune-check` select Dune with
separate fresh output directories. The `*-check` targets cap each self-test
endpoint at three workers, so two endpoints plus two owner credits fit eight.
`ox-build` and `stock-build` compile only and do not execute the resulting CLI.

Add `DRY_RUN=1` to inspect the exact command and resource declaration without
creating an output directory, acquiring tokens or launching a compiler/test.
The resulting `RESULT.json` binds the retained build snapshot, compiler,
binary, source hashes and actual test outcomes. Consult `SHARED-CLOSED.json`
for child/group/token settlement and the owning tool for its actual terminal.
A marker or process absence alone is not a parent-terminal receipt. Unknown
ownership retains the owner; do not restart a job merely because observation
has timed out.

This qualifies the text CLI/core for the recorded snapshot. It does not qualify
the native macOS GUI, every filesystem backend, SDK decoding or performance.
Low-level `tests/build_snapshot.py` remains available for separately owned build
controllers; invoking it directly does not acquire the shared token pool.

## Existing fixed synthetic controls

The dispatcher also offers finite original controls, for example:

```sh
SHARED_CPU_CREDITS=4 OUTPUT_DIR=/private/tmp/unison-local-sde-001 \
  "$UNISON_TEST_PYTHON" tests/manual.py sde-conformance
```

This runs the existing fixed independent SDE/SDR vectors and designated negative
controls serially under stock/Ox. It uses no camera, SDK or Photo input. Controls
with a different linked dependency graph must use its matching retained build
receipt. The current qualification map is
[release readiness](sol-release-readiness-20261017.md); historical results are
not automatically rebound to later source edits.

Parser fuzzing and sanitizer runners remain historical developer tooling, not
part of this session's selected workflow. Do not start a new campaign from this
document. Current XMP observation qualification uses `--fixed-only`, which skips
both random-byte and XML-mutation campaigns.

## Synchronization and SDK windows

Actual transport, bulk IO, camera and SDK jobs need their own exact fresh
coordinated request/admission. Revalidate source/binary/interpreter pins, unused
workspace and deadline before the one authorized dispatch. A previous consumed,
withdrawn or expired admission cannot authorize another run. IO is acquired
before CPU; canonical physical IO currently has only the exclusive-global
fallback, not independent physical-device lanes. Do not repurpose Photo's UI
lease or create another IO pool.

The existing [complete-sync benchmark](../bench/sync/README.md) supports
metadata-only preparation. A routine shared loopback pair fits at most three
workers per endpoint plus two owner credits inside Unison8. Larger 1/2/4/8/auto
comparisons need a separately coordinated budget; **18 is an explicit temporary
borrow, not the default**. Shared activity must remain disclosed, and a quiet
window requires a distinct agreement. Logical counters and extent models do not
establish physical APFS savings, cold-cache/network behavior or hard RSS limits.

Original fake-helper tests do not qualify Adobe behavior. Actual SDK execution
requires the pinned qualified tool and separately coordinated native/IO scope;
no build success, token release or historical SDK receipt grants another run.
Preserve photos, existing workflows and all failed/partial receipts. No merge,
production deployment or full-goal completion follows from these commands.
