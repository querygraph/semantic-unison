These tests compile the byte-identical production `TargetBinding` module with
the bundled Lwt implementation in a private `/private/tmp` directory. Small
dependency seams expose connection closure, path-policy changes and native
owner lifecycle. The native owner seam holds actual close-on-exec descriptors;
mutable producer admission retains a separate duplicate of a real private
candidate descriptor and keeps the original descriptor borrowed.
It does not implement a ticket registry or qualify native namespace operations.
Native filesystem behavior is tested separately in `tests/final_publication`.

Run either compiler:

```sh
python3 tests/target_binding/run.py --ocamlopt /usr/local/bin/ocamlopt
python3 tests/target_binding/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt
```

The private Lwt copy has explicit fault hooks at its actual continuation
dispatch and sleeping-promise waiter registration. Tests check that failures
before callback dispatch close the owner, while a waiter-installation exception
after dispatch keeps descriptors open until the helper promise settles. Retry
is bounded by the same registry capacity; no claim covers every asynchronous
exception or allocation boundary.

`--negative-control` privately replaces the handoff-failure ownership guard
with unconditional cleanup. The sleeping-helper descriptor test must reject
that premature-close variant. Production files are never changed. The runner
prints source and generated instrumentation hashes.

`--negative-handoff-control` privately restores unchecked legacy release.
The rebound-resolution case must reject that variant: stale resolution cannot
become a successful legacy completion. Native phase/namespace behavior remains
separately qualified; this verifies that the production registry calls its
fresh resolution and native handoff fences before relinquishing ownership.

Other cases cover 256-bit hexadecimal tokens, replay, physical connection/root
ownership, path and preference binding, the 128-slot backstop before native
preparation, preparation-only decline, reservation recovery, idempotent release,
session expiry, deferred close, legacy handoff, quarantine naming, publication
receipt retention, and original-error preservation. The backstop is not a
request scheduling or backpressure mechanism.

The original 50 cases remain. Another 45 cases cover separately negotiated
producer support and the strict Ready → Producing → Finalized → Committing
lifecycle. State-ineligible calls preserve current authorization; matching-owner
path or policy errors close eligible scopes. Commit requires producer-origin
freezing and a non-pseudo actual fingerprint receipt. Both fingerprint checks
reject native identity/operational faults without publishing a partial receipt.
The `Os` seam uses opaque Actual/Pseudo markers to test receipt handling; it
does not calculate or authenticate a file fingerprint.

Tests observe real candidate witnesses through idle source-check intervals,
busy producer and commit helpers, connection closure and repeated release.
Historical fingerprint/publication receipts survive close without granting
current operation eligibility. Only explicit producer legacy handoff yields
`Legacy_backend`. A mixed 128-owner case holds 32 tickets in each active phase.
Actual bundled Lwt allocation hooks cover both producer and strict commit
dispatch, sleeping-helper retention and bounded recovery on later admission.

Another 10 cases cover planned mutable/frozen handoff, changed resolution and
follow/case/resource-fork policy, native prepared/named refusal, and lost or
changed producer witnesses. Both negative controls are rejected under both
compilers.

All 105 cases passed under stock OCaml 5.5.1 and OxCaml 5.2.0+ox on 2026-10-13
against production `targetBinding.ml` SHA-256
`3fed72285b9cbf61b2f1013e44812a2dcada84be02815fdd6894f11afa762231`.
Both compilers also reject the retained premature-close negative control at
the original sleeping-helper ownership check.
This is registry/seam qualification. Native namespace correctness, source byte
verification and production materializer integration remain separate work.
