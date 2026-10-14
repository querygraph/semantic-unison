# Checked semantic hash execution component

SemanticHash's fallback SHA-256 round constants now use an immutable function
lookup. The former global mutable array was read-only by convention, but prevented
its captured reference implementation from satisfying OxCaml portability. Digest
formats, archive fingerprint algorithms and the native CommonCrypto data path
are unchanged. No payload or metadata serialization is normalized.

The checked interface template declares exported hash functions portable;
opaque mutable contexts remain domain-local. Three `ox-portable-ffi` comments
mark the only native declaration contracts. The qualification runner selects
that template and turns those exact markers into OxCaml portability annotations.
Stock source treats them as comments. Normal Make/Dune builds currently retain
the ordinary interface: production checked-interface selection and the complete
worker execution migration remain open. The template is not a suppressed error
or unsafe cast; all exported OCaml functions type-check against it. Portability
of foreign calls remains an explicitly reviewed C contract, not compiler proof
about their implementation.

The C audit for those contracts is narrow and concrete:

* Init allocates and roots a fresh state buffer and option. CommonCrypto's
  context is initialized on the C stack and copied into that private buffer.
* Feed roots context/input/offset/length, checks buffer/slice bounds and64KiB
  maximum, copies state to a private C stack context, consumes input and writes
  updated state back. It stores no process-global pointer or OCaml callback,
  performs no OCaml allocation while using input pointers and does not release
  the OCaml runtime during those accesses. Inputs/state require uncontended
  ownership at the exported interface.
* Finish roots state/result, validates context size, finalizes a private stack
  context, zeros stored state and returns a rooted fresh32-byte digest.
* Non-Apple init returns None, selecting the reference implementation. The
  unavailable native feed/finish paths raise; the reference operations remain
  subject to the same checked local-context contract.

Both compiler runs verify15 independently generated hashlib vectors spanning
padding/read/chunk boundaries. Four actual domains stream fresh private contexts,
compare native and direct reference results, and reject double finish/feed after
finish. A separately compiled qualification-only stub disables the Apple branch
to execute the actual create/feed/finish fallback, not merely the direct reference
helper. OxCaml uses Safe.spawn and rejects shared context and mutable input
capture in both stub modes. The forced stub is never installed in production.
Source/stub/compiler/interface and binary/log pins are in
[qualification.json](../tests/checked_hash/qualification.json).

A cached-string microbenchmark compares the exact prior source at e519dda with
current source,9 samples of1MiB each, alternating reference order. Median CPU
new/old reference ratios were0.995 stock and1.006 OxCaml; native ratios0.949 and
1.003. These noisy small samples do not establish a speedup or end-to-end
throughput. They show no large reference slowdown in this finite control.
Representative worker/sync/storage/RSS qualification remains outstanding.

The production source, current Make/Dune CLI+selftests and semantic kernel
regressions are verified separately. Root owns this component review; no new
independent-agent implementation approval, full checked worker boundary,
other-platform runtime or Adobe/Photo/Lightroom qualification is inferred.
