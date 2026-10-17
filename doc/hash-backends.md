# Semantic SHA-256 backends

The semantic hash API now uses an opaque native state. Each worker owns its
context; callers cannot interpret, serialize or share its representation.
Archive digests and the SHA256 algorithm/output remain unchanged.

`SEMANTIC_HASH_BACKEND=platform` is the default. It retains CommonCrypto on
macOS and the existing portable reference fallback on other platforms.
`SEMANTIC_HASH_BACKEND=openssl` explicitly selects OpenSSL3 EVP instead.
Unknown selections fail configuration. Selecting OpenSSL does not silently
fall back if headers, the library, the provider or initialization are unavailable.

Make and Dune accept the same optional installed dependency directories:

```sh
SEMANTIC_HASH_BACKEND=openssl \
SEMANTIC_OPENSSL_INCLUDE=/absolute/openssl/include \
SEMANTIC_OPENSSL_LIB=/absolute/openssl/lib \
make -C src NATIVE=true -j2
```

```sh
SEMANTIC_HASH_BACKEND=openssl \
SEMANTIC_OPENSSL_INCLUDE=/absolute/openssl/include \
SEMANTIC_OPENSSL_LIB=/absolute/openssl/lib \
opam exec --switch default -- dune build -j2 src/linktext.exe
```

Empty directory overrides use the compiler/linker's existing search paths.
Overrides must be absolute and omit control characters, `$`, `#` and backslash;
configuration uses explicit arguments and performs no dependency download or
installation. Configure a fresh Make build after changing these settings; the
generated Makefile.cfg is not an automatic environment-change cache. Dune's
generated flag files depend explicitly on these environment values. The normal
runtime loader must be able to resolve the installed libcrypto; no system
library path or provider configuration is changed by Unison.

The shared implementation in `src/semanticHash_evp.h` owns both EVP_MD_CTX and
the fetched EVP_MD. A rooted custom block owns them without storing OCaml
pointers. Finish/API failure free both resources; an idempotent finalizer handles
abandoned contexts. Native calls retain the OCaml runtime lock and feed at most
64KiB per call. Contexts and mutable inputs remain private to their worker.
The GC pressure hint is not measured allocator coverage, a peak estimate or a
hard memory cap. The experimental adapter uses this same implementation with
a separate symbol namespace and test-only failure/count instrumentation.

[Actual qualification](../tests/qualification/openssl-production-backend-actual-20261017.json)
records stock5.2.0 and Ox5.2.0+ox Make/Dune OpenSSL builds, a default-platform
stock Dune build, actual object-symbol/configuration readback, and two component
runs covering production/default paths. Fifteen vectors, four private domains,
state/range checks and shared-implementation cleanup controls passed. Expected
Ox portability compile refusals are recorded as such. Eleven configuration/build
children, five inspectors and both component groups settled with CPU8 closed.
The first harness reporting failure is preserved; no SDK/media work occurred.

This evidence is **macOS with installed OpenSSL3.6.4**. Actual Linux/Windows
builds/runtime qualification, broad cryptographic review, provider/FIPS policy,
resource peaks and performance remain open. The default non-Apple reference
fallback therefore remains a separate deployment/portability scope; this
optional backend is not universal platform acceptance.
