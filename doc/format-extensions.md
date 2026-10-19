# Trusted format extensions

`FormatExtension.S` defines a versioned profile and an inspector that describes
bounded editable byte regions in a `SemanticFile`. The transfer core checks
those regions independently and hashes the entire file, the protected
complement, and the editable contents. It classifies two proofs as exact
bytes, editable metadata, or other bytes. Unsupported structures decline the
optimization and use normal exact copying.

An extension does not override the expected target bytes. Plans bind the
profile, basis, preserved complement, metadata extents, and exact target hash.
Application rejects a mismatched profile before writing and verifies the
completed private candidate. This is format-aware transfer classification. Extension inspection itself does
not merge conflicts or treat different byte encodings as synchronized. A separate
opt-in [DNG scalar merge policy](dng-built-in-merge.md) uses a verified common
base and the normal candidate validation/publication lifecycle.

Register locally compiled modules on the owner before feature negotiation:

```ocaml
SemanticFormats.register ~capability:"example-format-v0" ~max_payload:1048576
  ~suffixes:[".example"]
  (module ExampleFormat)
```

Add this registration alongside the built-in DNG registration in
`semanticFormats.ml`, and include the new source module in the build. Enable
it with `semanticprofile = <versioned profile ID>`. No transfer or worker
dispatch changes are needed. `semanticdng = true` remains a shorthand for
the three built-in DNG profiles: XMP `/1`, XMP `/0`, then layout-only `/0`.
The layout profile preserves exact donor bytes while reporting uninterpreted
regions; it does not gain metadata-merge authority. An unavailable peer capability uses ordinary transfer.

The optional `max_payload` declaration bounds total editable bytes per proof.
It defaults to the 16 MiB core ceiling; DNG declares 1 MiB. The core rejects a
manifest exceeding the declaration before copying editable contents and uses
the bound for admission credits and request-specific RPC allocation limits.
An extension must still bound its own parser allocations and traversal.

The optional `suffixes` list supplies advisory UI hints; the default is empty.
It accepts at most 16 dot-prefixed suffixes, each 2..32 bytes without NUL or
path separators, and matches filenames case-insensitively for ASCII letters.
The DNG registration declares `.dng`. These hints do not filter transfer or
establish format eligibility. Explicit diff/details inspection probes enabled
profiles by content even when a file has been renamed. If a hinted file is
unsupported or its peer cannot report, the UI displays that result instead
of launching a binary diff. Ordinary unsupported text retains the existing
external diff path. See [SIR/0](semantic-report-v0.md) for report bounds and
the scope of current-pair observations.

Profile names and capabilities must be unique. The default capability is
`semantic-profile:` followed by the profile. `registered` returns handles in
registration order; `resolve` looks up a profile. Owner code applies user
selection and peer capability checks before dispatch. Workers receive the
resolved immutable handle through `SemanticWorkers.inspect` and `apply` and
never consult the registry. Standalone kernel tools and tests can use
`FormatExtension.register` directly, without preferences or peer features.
A plan for a different profile cannot be applied
with that handle.

The module is trusted code, not a sandboxed plugin. Its inspector must use
worker-local state and the supplied bounded file interface. It must not access
Unison preferences, archives, registries, Lwt, filesystem commit functions, or
external processes. `trusted` constructs a validated handle for a known
compiled module, including compatibility wrappers; it does not prove that the
module follows this contract. Review each extension and its dependencies for
domain safety and conservative classification before registering it.

The built-in profiles are conservative DNG XMP v0/v1 and
[JPEG standard XMP v0](jpeg-semantic-profile.md). Each requires explicit opt-in;
DNG shorthand selects only DNG. JPEG uses the same generic inspection, planning,
application, negotiation and receiving pipeline. Worker tests also register a
synthetic format and include a mismatched-profile no-write test. Real profile
qualification is recorded separately; generic dispatch alone does not validate
a new format or make its parser safe.

Receiving validation is a separate companion interface, not an inspector
eligibility result. Register `CandidateValidator.S` modules in
`CandidateValidators` during startup; core supplies the finalized candidate,
stable snapshot and shared worker/helper scheduling context. A pure
`FormatRecognition.S` handle recognizes content or records uncertainty, while
selection and validation execute on the owner. One DNG companion covers both
transfer profiles, including semantic-ineligible fallback and renamed DNGs.
See [candidate validators](candidate-validators.md) for the contract and
`dng-validation-v1` compatibility boundary.
