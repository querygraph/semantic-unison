# Native helper resource qualification

`run.py --compiler /absolute/ocamlopt --receipt /private/tmp/result.json`
compiles actual HelperSupervisor/vendored Lwt, the native launcher and a private
C probe. It exercises OS descriptor hard limits, literal/empty argv0/environment,
PID/group retention, high inherited-FD closure, descendant inheritance, cap-raise
rejection, timeout/cancellation/output cleanup, malformed requests and parent
limit preservation. The address-space probe records OS rejection separately.

`integration.py --unison /absolute/unison --launcher /absolute/limiter
--receipt /private/tmp/pins.json` tests wrong pins, changed executable bytes and
invalid settings on both require/warn receiving paths; live inputs stay intact.

The existing `tests/validation_paths/run.py` accepts `--helper-limiter` and
`--helper-descriptors`, optionally `--server-helper-descriptors`, and runs its full
resumed/reused/external/merge/timeout/cancellation suite with real child hard-limit
readbacks. Endpoint limits must remain independently local. Helpers are synthetic;
there is no Adobe SDK, native Lightroom operation, Photo input or production write.

[Qualification](qualification.json) preserves actual compiler/build/test/input
pins, terminal receipts and the failed closefrom compilation. Darwin has no public
closefrom declaration here; the successor uses bounded own-process FD enumeration
and verification. Source/kernel/OS and child memory limits are separate claims.
