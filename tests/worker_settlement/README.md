# Returned worker settlement

Run compilers sequentially, outside shared build directories:

```sh
python3 tests/worker_settlement/run.py --ocamlopt /absolute/compiler/bin/ocamlopt \
  --keep-work --receipt /private/tmp/worker-settlement-receipt.json
```

An actual one-domain Identify callback pauses on an Atomic barrier while the
owner event loop runs timers and reads completions. Private legacy-Lwt
instrumentation watches the physical identity of a returned production promise
and fails its first two waiter installations with distinct preallocated errors.
It never changes a promise state or injects a failure before work returns.

Six phases cover the raw worker reply, CPU result mapping, I/O callback result,
I/O result mapping, submission guard and public Identify response mapping. Each
phase checks normal success/error/cancellation underneath the installation
failure, queued CPU and I/O admission, and two finite polling timer failures.
Three no-fault controls qualify the ordinary outcomes.

A kernel FD census independently confirms both worker duplicates remain owned.
CPU, filesystem, pending-job, private domain-slot and retained workspace credits
must remain charged until the callback leaves and actual worker cleanup settles.
Retirement/cancellation cannot start a next consumer or same-device callback
early. Owner timers continue progressing; exact reuse and shutdown must close
descriptors and settle every ledger while preserving the first exception.

The negative uses the actual parent `9fbfc00` implementations of CPU ownership,
I/O admission and worker submission with the same private raw-reply fault. It
must fail the independent active-FD/admission oracle. Current source, parent
participants, private transformations, compiler, commands, logs and generated
artifacts are retained and hashed by `--keep-work`.

This tests finite observer-installation and polling setup failures using small
synthetic temporary files. It supplies no persistent-OOM, arbitrary asynchronous
exception, compiler-proved domain safety, process RSS, actual SDK, Photo,
filesystem sharing or performance guarantee.
