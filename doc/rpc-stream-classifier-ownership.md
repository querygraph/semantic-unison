# Stream classifier failure ownership

The original stream error path ran ownership predicates in an exception filter.
When a predicate threw, that exception replaced the original failure before the
outer raw-body owner could classify it. The prepared carrier contract in
`Remote.register_body_ownership_classifier` promises retention on predicate
failure; the stream path violated it.

An original five-byte input demonstrates this: the classifier throws for a custom
handler exception, the receive promise fails, raw accounting returns to its prior
3-byte/3-owner baseline, and no retention entry records either cause. The actual
counterexample wrapper11298/2f5449/0 expected its controlled child to fail; it did
not acquire a directory, SDK, Photo, native helper or EXglobal resource.

The successor invokes the synchronous stream callback once through the prepared
`RetainedOwnership.guard`, before the ordinary diagnostic-cache/abort handler.
Core or registered ownership uncertainty, including a throwing classifier, thus
returns a retained promise holding the outer raw ticket and exact buffer. The
carrier preserves both original and classifier failures. Standard known failures
still follow existing diagnostic-cache limits and abort/ping behavior. Unknown
unregistered custom exceptions still propagate unchanged and release their raw
allowance after known processing failure. Capacity refusal remains before the
callback. This does not add custom decoded-argument, workspace, heap or RSS bounds.

Original controls use custom and standard classified errors, assert exact cause
pairs and weak raw-buffer reachability across connection closure, and check the
unregistered path. Two controlled regressions reintroduce the exception filter
or omit inner classification. The latter must fail before uncertain standard
errors can be treated as ordinary cached diagnostics. The existing typed-stream
abort regression is adapted to the new guard, preserving its original purpose.

All four stock/Ox Make/Dune builds+selftests passed. Focused controls passed both
compilers. The final regression union passed55 designated negatives/compiler, with actual
resume parent72746/c5db4c/0/no session. Evidence is
`tests/qualification/rpc-stream-classifier-actual-20261018.json`. The old
preflight mutation fixture accepted only synchronous refusal; its corrected
version also polls an immediately failed promise. This is a separately compiled
nonproduction test change, not a change to any built production source or binary.
Earlier reports remain preserved, and no all-input-identity claim may hide it.

The frozen producer V5 candidate is untouched. Its generated wire/property scope
must not be presented as proof of this classifier-fault boundary. No transport,
SDK, Photo or deployment grant follows from these source controls.
