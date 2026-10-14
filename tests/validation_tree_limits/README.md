# Validation tree structural limits

`run.py --build SNAPSHOT --compiler OCAMLOPT --receipt FILE` links the actual
`ValidationTreeBudget` object and executes complete Unison loopback receiving
tests. Eight checks cover exact entry/path boundaries, rejected charges without
counter mutation, disabled caps, negative values and arithmetic overflow.

Seven CLI cases cover an exact entry ceiling, require/warn entry and path
rejection before helper execution, invalid settings and a helper-added hidden
entry rejected before publication. A lower client cap cannot override the
receiving endpoint's local settings. Every source remains exact; rejected
private staging is discarded.

The actual CandidateValidation implementation is separately linked with private
read/close observations. Cancellation after three real native reads closes the
handle once. Removing only the enumeration check makes the same oracle fail.
This qualifies a cooperative checkpoint, not OS syscall interruptibility.

[Evidence](qualification.json) pins current sources, binaries, objects, logs,
compiler/build variants and receiving regressions. Limits are opt-in structural
counts; full directory admission, property/SDK allocation and RSS remain open.
