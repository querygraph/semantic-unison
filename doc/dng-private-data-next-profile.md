# DNGPrivateData investigation and framing prerequisite

The first retained real-camera DA copy declined on TIFF tag50740. Both pinned
inspectors agreed; clone integrity passed. Existing profiles0/1 still decline
that tag and use ordinary exact transfer. This work does not relabel that result
as supported and does not read the retained clone again.

Adobe's [DNG1.7.1 specification, page41](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf)
defines tag50740 as BYTE data in IFD0. It requires a manufacturer-identifying
terminated ASCII prefix, internal relative references confined to the private
block, and byte-order independence. Those requirements describe conforming
files; recognizing a tag number or creator string does not verify them.

The locally installed SDK source `dng_info.cpp`, `ParseDNGPrivateData`, was read
without executing Adobe code. This locally patched source is pinned in the
qualification receipt, not represented as an unmodified upstream source release.
It recognizes an Adobe-prefixed section sequence with big-endian framing,
section lengths, alignment, maker byte-order markers and original-offset fields.
It has several vendor-specific branches. We have not inspected the retained
camera block's creator or sections and do not assume it uses this layout.

`src/dngPrivateData.ml` now provides an original bounded framing recognizer for
**only Adobe/MakN** sections. The supplied reader addresses the candidate block,
not the TIFF file. It checks all requested ranges and returned lengths, limits
block length to64MiB and section count to256, rejects other creator/section keys,
and requires zero alignment padding and complete framing. This is stricter than
the installed SDK's permissive final-padding handling. It reads only framing
bytes: a virtual64MiB one-section block needs20 header bytes. Section payloads
are neither read nor interpreted. Unknown creators/other Adobe sections decline.

Framing evidence is deliberately a different type from `FormatExtension.manifest`.
It is not an eligibility proof. The module is not linked into or called by the
production DNG profiles, registry, developer inspector or current transfer path.
Existing accepted/rejected layouts and negotiated IDs remain unchanged.

A future profile successor still needs:

- A qualified closed-reference policy for embedded maker structures, including
  old-offset rebasing, aliasing and malformed references. Envelope length checks
  alone cannot establish that policy.
- PrimaryIFD/BYTE placement, protected private extent, XMP disjointness and all
  existing full-file/complement checks in the actual locator.
- Separate capability/profile identity and mixed-peer negotiation tests; no
  silent widening of profiles0/1.
- Independent malformed/reference fixtures and exact transfer/materialization
  checks with both compilers, plus receiving/failure cases.
- A separately coordinated copy-only camera probe before any camera-support
  claim; no original or preserved-copy mutation or automatic follow-up run.

Run the fixed synthetic controls manually with:

```sh
SHARED_CPU_CREDITS=8 make -f tests/Makefile dng-private-framing
```

One compiler job at a time, stock thenOx, fits the standing Unison lane with two
owner credits. Compiler locations are the currently qualified local opam prefixes
listed in `tests/dng_private_data/run.py`. This target creates inert private
fixtures only and calls no SDK/Adobe/Photo code. It is a finite hand-written suite,
not a fuzz campaign. The [actual receipt](../tests/qualification/dng-private-framing-actual-20261016.json)
records47 checks/compiler and owned-group/token closure; broader format eligibility
remains unqualified.

## Inactive primary-directory diagnostic locator

`locate_ifd0_private` now locates one out-of-line BYTE tag50740 in a primary
directory bearing one BYTE[4] DNGVersion beginning with1. It handles classic
TIFF/BigTIFF, both byte orders, signed-domain integer checks, bounded directory
counts, exact reads, duplicate selected tags and selected extent bounds. It
rejects overlap with the TIFF header or primary directory. At most16384entries
and327712header/directory bytes are read; the private body is never read by
this locator. The caller's trusted reader remains responsible for held-file
identity, size and before/after epoch fencing.

Unknown other tags and other directories are deliberately not interpreted.
Locating an extent does not prove valid DNG, all-file graph closure, XMP
disjointness, self-contained private references, vendor identity, rendering
equivalence or transfer eligibility. It is a diagnostic prerequisite for a
future separately admitted bounded inspection, not profile0/1 activation.
No camera or preserved receiving clone was opened to develop or test it.

The [new actual stock/Ox receipt](../tests/qualification/dng-private-locator-actual-20261016.json)
records162fixedchecks/compiler and actual owning-tool/group/token closure.
These include the prior framing checks plus four layout/endian combinations,
malformed directory/selected-entry controls, trusted-reader error propagation,
short reads, and a virtual maximum directory with exact finite read count.
The earlier47-check receipt remains historical evidence for the earlier source.
The existing manual target runs the expanded fixed suite; no fuzz campaign,
SDK, Adobe or photographic payload is involved.

## Current Dune packaging check

[Current-source stock/Ox Dune builds](../tests/qualification/current-dune-diagnostic-packaging-actual-20261016.json)
both passed under the standing Unison8-credit grant, serially with2compiler jobs
each. The424-input source manifests match and were rechecked against the
checkout; the CLI hashes and diagnostic module's native object/interface artifacts
were verified. This checks Dune's automatic module discovery, distinct from the
standalone162-check suite. These were build-only runs: no final CLI/selftest,
receiving, SDK, Adobe or photographic payload operation. No profile activation
or general format/corpus qualification follows from successful packaging.
