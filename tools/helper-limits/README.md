# Optional native helper resource launcher

Build independently of Adobe and OCaml:

```sh
python3 tools/helper-limits/build.py \
  --output /absolute/private/path/unison-helper-limiter \
  --receipt /absolute/private/path/limiter-build.json
```

Configure each receiving endpoint locally with the build receipt's binary hash:

```text
helperdescriptors = 64
helperlimiter = /absolute/private/path/unison-helper-limiter
helperlimiterhash = <lowercase executable SHA-256>
```

Limits default to zero/off. Copy/merge/diff helpers and selected DNG validation
use the same supervisor and CPU budget, now with a separate native launcher that
sets both soft and hard limits before target exec. It closes inherited extra
FDs, retains stdin/out/err, and preserves literal argv, environment, PID/process
group and the existing timeout/cancellation/reaping lifecycle. Descriptor caps
include stdin/out/err. Each process inherits the hard cap, including descendants;
this is not a group-wide or parent Unison FD ceiling. It never changes the
multithreaded parent or forks an OCaml runtime.

The owner verifies the launcher SHA-256/identity before and after settled work
through the shared workers. Changed/missing pins fail even under Adobe warning
policy. Endpoints retain their own paths/pins/limits; remote requests cannot
supply a launcher. A known valid launcher has an 8 MiB executable size ceiling.
Private creation-parent/publication ownership and candidate checks are unchanged.
Executable pinning does not remove same-UID namespace/exec races.

`helperaddressspace` declares an optional MiB address-space limit, not RSS.
**Current macOS probes reject the tested `RLIMIT_AS` installation.** Do not claim
memory enforcement on this host. A requested unsupported limit makes the
launcher exit125 with a bounded diagnostic before executing the target; it
never retries without the limit. Existing Adobe `warn` semantics can explicitly
permit unavailable validation; `require` rejects it. Zero disables address-space
limits. Other platforms' address-space enforcement remains runtime-unqualified.
Native Windows rejects requested limits instead of using its legacy external
helper path. Zero limits retain baseline behavior without this executable.

The launcher protocol is internal `--unison-helper-limits-v1`, decimal descriptor
and address-space-byte limits, `--`, absolute target, literal argv0 and arguments.
Invalid protocol/limits, inherited-FD cleanup failure, OS rejection and exec
failure exit125 before target execution. The native helper is trusted compiled
local code, not a sandbox or a dynamically received extension.

Build snapshots and [qualification](../../tests/helper_limits/qualification.json)
cover current macOS descriptor enforcement, literal/empty argv0, inherited high
FD cleanup, inherited hard limits, inability to raise the cap, malformed requests,
unchanged parent limits, shared supervisor cleanup and actual receiving paths.
Global RSS, aggregate descendant limits, complete-lifetime parent descriptor
bounds and actual capped SDK/codec scaling remain open. No Adobe, Lightroom,
Photo payload or preview publisher is invoked by these tests.

## Inherited-descriptor cleanup failures

Darwin enumeration now treats every reported close error as a pre-exec failure,
even if the kernel actually closed that descriptor. It never retries the numeric
FD. The isolated launcher exits125, so remaining inherited ownership is settled
by process exit before any target executes. This is different from a live
multithreaded parent retaining uncertain descriptor ownership.

On systems without a working kernel close-range API or closefrom, the fallback
scans only a finite inherited hard limit of at most65536 descriptors. Larger or
infinite limits refuse with ENOTSUP before target execution; high descriptors
are never silently skipped. EBADF from scanning an unused number is expected;
any other close failure stops the scan without numeric retry. These restrictions
apply only when the optional helper limiter is explicitly configured.

Original injected fixtures exercise the portable branch on the build host and
Darwin's kernel-close-success/reported-EINTR case, including target non-entry.
They do not claim native runtime qualification of other operating systems.
