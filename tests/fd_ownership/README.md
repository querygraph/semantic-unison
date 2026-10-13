# Early descriptor ownership guards

Run private compiler-matched snapshots with synthetic files:

    python3 tests/fd_ownership/run.py --ocamlopt /usr/local/bin/ocamlopt
    python3 tests/fd_ownership/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt

Twenty positive controls cover SemanticFile duplicate-to-channel/record handoff,
callback and close errors; SemanticWorkers notification-pipe setup, shared
record/domain-list/reader/pump construction; and both submit duplicates through
cancellation-listener, monitor and admission-continuation setup. They count
actual kernel descriptors, keep borrowed caller descriptors live, verify source
bytes, and join actual spawned domains. Close-error controls first close the
owned descriptor, open /dev/null at the identical integer and raise EIO. Cleanup
must preserve the primary error and the replacement sentinel while attempting
each owned close once.

Three private negatives restore the pre-guard function bodies from pinned
commit e9be47381d35af82d816b1f80df348ddf7409180. Channel construction, first pipe
flag setup and submit-listener faults each expose actual leaked kernel FDs,
rather than merely resource-counter differences. The broken submit negative
also strands its old pending counter, so negative-only harness teardown does
not await that broken pool's shutdown. The designated FD assertion terminates
the disposable process; every positive control performs normal shutdown.

Faults are injected at exact private source seams using a one-shot marker
exception. The fixture does not force global allocator exhaustion or claim
universal OOM/asynchronous recovery. In particular, the new submit guard does
not qualify allocation failure in an already-dispatched promise chain. A queued
job has transferred its duplicates to the worker, and controller cleanup must
not close them underneath execution.

Production contains no mutable test hook or interface change. Retained receipts
pin copied and instrumented sources, historical negative bodies, objects,
binaries and complete terminal logs. No Photo, Adobe, Lightroom, catalog/cache
or production data are accessed.
