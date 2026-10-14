# Checked semantic file execution component

The checked SemanticFile interface compiles against the unchanged file-operation
logic and the checked hash dependency. Two explicit markers on native writer
admission/pwrite declarations select portable foreign contracts in qualification.
The matching interface template exports portable functions while retaining
nonportable opaque reader/writer contexts. Production Make/Dune now select this
interface and the two exact native contracts for OxCaml; stock source remains
unchanged. See [production selection](production-oxcaml-mode-selection.md).
The subsequent checked worker integration completes the OCaml execution
boundary; native/resource/performance requirements remain open.

Actual OxCaml Safe.spawn tests create private readers/writers inside four domains.
They verify exact bounded reads and iteration, independently generated hashlib
digests, cancellation hook execution/rejection, original-descriptor survival,
60006-byte positional writes with unchanged cursor, write/read extent limits,
offset overflow, rejected append/read-only outputs and nonregular readers.
Python compares full staged bytes, including unchanged prefix/suffix. All source
inputs remain byte-identical and process descriptor count returns to baseline.
Shared reader/writer contexts and borrowed mutable iteration buffers cannot be
captured for another checked domain: three negative compilations reject them.
Stock OCaml exercises the same implementation/runtime controls with ordinary
spawn. [Pins and actual compiler logs](../tests/checked_file/qualification.json)
retain both selected interfaces, sources, stubs, binaries and output hashes.

Foreign portability is a manual contract, not compiler proof about syscalls:

* Writer admission roots the descriptor, processes runtime pending actions before
  interpreting it, converts the POSIX descriptor to a bounded native integer,
  and releases the runtime using only native scalar state. fcntl/fstat inspect
  writable/nonappend flags, regular-file kind/size and single-link ownership.
  After reacquisition, errors are converted with the runtime held.
* Positional write roots every OCaml argument, processes pending actions before
  interpreting the borrow, checks the slice/64KiB cap and signed/native offset
  bounds, and copies immutable input into native stack storage. Released pwrite
  uses only the copied buffer/native scalars. No OCaml heap pointer is retained
  across runtime release, and syscall results/errors are interpreted after
  reacquisition. Short writes/EINTR/cancellation remain caller obligations.
* The primitives register no application callbacks or process-global pointers.
  Runtime pending actions at entry may raise; this is not a no-reentrancy claim.
  Kernel descriptor lifetime/exclusivity/status flags require the existing caller
  borrowing contract even though Unix descriptor values themselves are portable.
* Windows retains its existing ML seek/write fallback; the current positional
  cursor tests and native foreign contract qualification cover POSIX macOS only.

The reader wraps a duplicated regular descriptor in a private channel with
stable initial identity and a cancellation callback. Each callback/iteration is
worker-local; with_fd checks identity at completion and closes its duplicate on
normal/exceptional return. A reader is valid only during its callback and an
iteration buffer is borrowed only for that invocation. The API/type checker does
not enforce arbitrary same-domain escape/lifetime misuse, hostile external
writers, or use of raw duplicate kernel descriptors in multiple domains.

No file algorithms, source-photo paths, archive formats, publisher APIs or
validation policy changed. Current Make/Dune CLI+selftests pass both compilers.
Root owns this component audit; it does not qualify the complete worker boundary,
other-platform runtime, full RSS/FD/performance guarantees or Lightroom/Adobe
operations.

The subsequent [production worker integration](checked-semantic-worker.md)
now compiles the complete worker closure with Safe.spawn on OxCaml, including
checked extension execution and atomic counters. Earlier component receipts
remain historical; full native/resource/performance M6 requirements stay open.
