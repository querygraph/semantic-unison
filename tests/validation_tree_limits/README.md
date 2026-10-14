# Validation tree structural limits

`run.py --build SNAPSHOT --compiler OCAMLOPT --receipt FILE` links the actual
`ValidationTreeBudget` object and executes complete Unison loopback receiving
tests. Fourteen checks cover exact entry/path/memory boundaries, rejected charges without
counter mutation, disabled caps, negative values and arithmetic overflow.

Ten CLI cases cover an exact entry ceiling, require/warn entry and path
rejection before helper execution, invalid settings and a helper-added hidden
entry rejected before publication. A lower client cap cannot override the
receiving endpoint's local settings. Every source remains exact; rejected
private staging is discarded.
Positive manifest admission also proves two simultaneous synthetic helpers with
one global transaction; oversized whole plans and retained estimates reject
before helpers. A separately linked actual-object probe exercises success,
rejection, cancellation and fresh retry in the same process, with zero residual
resource/CPU/I/O ledgers and unchanged private originals.

The actual CandidateValidation implementation is separately linked with private
read/close observations. Cancellation after three real native reads closes the
handle once. Removing only the enumeration check makes the same oracle fail.
This qualifies a cooperative checkpoint, not OS syscall interruptibility.

[Evidence](qualification.json) pins current sources, binaries, objects, logs,
compiler/build variants and receiving regressions. Limits are opt-in structural
counts; the [memory successor](memory-qualification.json) records partitioned
estimate admission. Pre-creation directory admission, transient property/SDK
allocation and RSS remain open.
