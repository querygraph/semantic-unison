# OpenSSL3 SHA-256 component and production adapter

The initial isolated candidate has now been integrated behind an explicit
production Make/Dune selection. See [backend configuration and current evidence](../../doc/hash-backends.md).
Default platform behavior remains unchanged. The adapter and opt-in production
path share `src/semanticHash_evp.h`; separate symbol namespaces allow both to
be checked in one control executable. The historical component receipt below
describes its earlier source, including this README's previous candidate status.

Each abstract OCaml context owns an EVP_MD_CTX and a fetched SHA256 EVP_MD.
The custom block stores no OCaml pointers. Finish and native API failure free
both native resources; an idempotent finalizer handles abandoned contexts.
Feeds validate the complete range, split it into at most64KiB calls, and reject
messages beyond SHA256's byte-length domain. The OCaml runtime lock remains
held across each chunk. Contexts and mutable input are private to their owning
domain; Ox negative compilation checks reject shared captures.

API ownership and return-code handling follow the
[OpenSSL EVP digest API](https://docs.openssl.org/3.5/man3/EVP_DigestInit/).
The 4096-byte OCaml GC pressure hint is not measured allocator coverage or a
hard memory limit. No FIPS/provider configuration assurance is claimed.

`tests/portable_evp_controls.py` uses the existing installed OpenSSL3.6.4 on
macOS, private generated inputs and the pinned stock5.2.0/Ox switches. Fifteen
boundary-sized vectors agree with CommonCrypto and Python hashlib; empty/abc
known answers, four independent domain contexts, invalid ranges/state, abandoned
context GC, and initialization/update/finalization failure cleanup also pass.
Test-only counters count owned contexts/methods, not arbitrary library memory.
Two Ox compilations intentionally fail when capturing shared context/input.
Eight contained compile/runtime calls completed with their expected statuses.

[Actual evidence](../../tests/qualification/portable-evp-component-actual-20261017.json)
preserves the successful final run and earlier import/compiler test failures.
No SDK, media payload or new dependency installation was involved.

The explicit installed-directory linkage and opaque native context are now
implemented and qualified on macOS. Actual supported non-Apple builds/tests,
broader resource accounting and platform deployment remain outstanding. A macOS
linked component does not qualify Linux or Windows. No backend default change
follows from these controls.
