# Native positional-write and materializer qualification

This fixture currently runs on macOS; it does not qualify other POSIX hosts.
Compile only private snapshots and use disposable synthetic files:

    python3 tests/positional_write/run.py --ocamlopt /usr/local/bin/ocamlopt
    python3 tests/positional_write/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt

The fixture uses actual SemanticFile and SemanticDelta implementations, with
native C-only wrappers around the new preparation and pwrite stubs. No
production source contains a fault API, preference or environment switch.
Released-runtime fixture code invokes no OCaml callback and dereferences only
the bounded native copy supplied by production.

The unmodified native path covers direct absolute writes; a duplicate's
deliberately disturbed shared offset; binary input copied before runtime
release; read-only/closed/nonregular/multilink/O_APPEND rejection; cancelled and
interrupted admission; invalid descriptor, slice, size and signed-offset
boundaries; zero and exact 64KiB calls; an actual sparse write above 2GiB;
short, interrupted, operational and malformed syscall results; and a pending
Sys.Break injected immediately after native copying. The prepared writer owns
no FD, and per-case descriptor counts verify caller ownership survives errors.

Production materializer cases use independently constructed generic editable
regions with nonuniform binary target bytes, so incorrect source-slice advancement
cannot hide behind a constant packet. Every native invocation records absolute address, requested count,
returned result, errno, actual successful bytes and shared position before/after.
Exact targets, immutable basis bytes, bounded 64KiB calls, short-write/EINTR
counts, one native admission, partial errors, cancellation, zero progress,
unchanged packets and append rejection for an unchanged plan are checked.
Both successful and unsuccessful materializations inspect remaining synthetic
staging bytes. No publisher is linked into these direct tests: preservation of
an unrelated live-name sentinel is a materializer bound, not qualification of
an entire receive/publication consumer.

Native fcntl/fstat counters count only queries through the new C admission
stub. They exclude existing proof queries in ML/Unix. The native pwrite attempts
perform no per-write admission query. A borrowed writer requires the caller to
keep its descriptor live, flags stable and output exclusively writable; this
fixture makes no concurrent-close, recycled-FD or hostile F_SETFL guarantee.

Two additional private positive variants qualify separate layers:

- Forward impossible positive/negative syscall counts past native validation
  into the unchanged production ML loop. Its invalid-progress guard must stop
  immediately without trusting counts or performing another write. The shipped
  native boundary independently rejects these results as EIO.
- Force native preparation to return false, selecting the actual production
  ML seek/write branch on this POSIX host. Checked slices/offsets, exact interior
  bytes and changed-position semantics, complete target materialization and
  unchanged packets work without any pwrite invocation. This verifies wiring;
  it does not qualify Windows descriptor representation, ABI or runtime.

Three private source negatives fail exact designated assertions:

- Replace pwrite with actual lseek/write: detect the changed caller position.
- Remove only the preparation append guard: detect admission of O_APPEND,
  directly and for an unchanged materialization.
- Pass the original heap address to the released syscall boundary: the fixture
  compares pointer values and returns EFAULT before dereferencing that pointer
  or calling libc. Its bounded-copy assertion detects the defect safely.

Retained receipts pin actual source snapshots, mutations, compiler configuration,
objects, binaries, terminal logs and synthetic artifact inventories. Files of at
most 1MiB receive full digests; the large sparse fixture records exact native
size/identity and bounded endpoint samples without reading its entire hole.
Development --case and --fixed-only runs are narrower than complete qualification.

Only the POSIX write attempt preserves the shared file position. Existing
SemanticFile inspection and readback hashing still use seek/read on duplicate
descriptors, so whole materialization is not position-preserving. Windows keeps
the existing seek/write backend. No physical APFS allocation, crash durability,
native-I/O deadline, Photo/Adobe/Lightroom invocation, catalog/cache publication
or production-volume behavior is claimed by this direct fixture.
