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

## Borrowed-descriptor diagnostic CLI

[Developer tool](../tools/private-dng-framing/README.md) now combines the inactive
locator/framer with unbuffered exact-length reads on an owner-supplied regular
stdin descriptor. It opens no source path and accepts no input argument. The
fixed target `dng-private-diagnostic` builds stock/Ox and tests only generated
inert files. [22actual CLI controls](../tests/qualification/private-framing-cli-controls-actual-20261016.json)
passed with application read-range/count checks, declared maker payload skipped,
native owner FIVE/mode/nlink unchanged, both compilers and process groups closed.
Pipes, writable-mode/multi-link inputs and unexpected pathname arguments refuse
before child reads. One strict compile failure was preserved and corrected.

Limits are331558requested application bytes/773logical read callbacks; no full
SHA, decoder or vendor/closed-reference proof. The child reports its timestamp
fence lacks native nanosecond precision; an admitting owner must supply exact
FD/path epoch fencing and actual settlement. Untrusted pointers are bounded, not
proved to be genuine metadata. No camera/preserved clone/Photo data was read,
no current profile was widened, and no future diagnostic admission is inferred.


## First camera-derived receiving-clone framing observation

The [actual bounded v2 diagnostic](../tests/qualification/private-framing-input-actual-20261016.json)
ran once under fresh Root EX-global IO admission and Unison00..07. Stock and Ox
returned identical protocols after706requested bytes each (1412total), six
logical ranges each. The selected classic little-endian TIFF private extent is
6576bytes at10970; its Adobe/MakN framing declares one6556byte little-endian
maker body with original offset1404. No recorded read intersects the maker body.
The owner fenced the exact native nanosecond descriptor/path identity before and
after each child; audit lstat matched. Two program waits, containing worker/group
and actual parent terminal0 are retained; IO/CPU closed. No source full hash,
image decode, Adobe/SDK, production transfer or receiving ran.

This resolves only whether the observed50740 payload uses the bounded recognized
framing. It does not identify the camera vendor or interpret maker references,
prove private-byte self-containment, establish the complete TIFF graph or permit
relocation. Profiles0/1 remain unchanged and safely decline this clone. Broader
support requires a separate exact preservation/reference-closure policy and
independent conformance plus receiving qualification; recognition alone must not
remove the unknown-private-data refusal. Earlier statements of no camera data
read describe their original source/control runs, not this later admitted run.
# Candidate MakerNote directory geometry — source-only successor

The saved separately admitted framing V2 result identifies one Adobe/MakN
section with6556 payload bytes and original offset1404 inside a6576-byte private
block. That is framing evidence only; it does not identify the camera-specific
pointer grammar or establish XMP independence. This review reread saved JSON,
not camera or retained-clone payload bytes.

`tests/private_maker_shape.py` now provides a pure candidate classic-IFD shape
probe with an explicit payload-relative reader, byte order, original offset and
candidate directory offset. It checks a nonempty count<=256, known TIFF type
widths, duplicate tags and bounded directory reads (at most3078bytes). It reports
declared out-of-line extents relative to the proposed original base, including
extents outside the payload. It reads no pointed values and emits no inline
values; a LONG or IFD-typed inline value may still be a private pointer. A
nonzero next-directory field remains unresolved and is not traversed.

[Five original controls](../tests/qualification/private-maker-shape-source-actual-20261017.json)
pass both byte orders, in/out-of-payload extents, inline-pointer ambiguity,
unknown types, duplicate/oversized/truncated tables and exact typed metadata.
Actual10346 reaped0/group absent/Unison8 closed, owning85eed6/0/no session. No
SDK, filesystem media, camera/Photo data or canonicalIO access. All outputs keep
maker recognition, private-reference closure and semantic eligibility false.

This is a candidate-shape diagnostic, not a new format/profile contract. Before
using retained bytes, prepare a fresh exact payload-slice/epoch/read-budget/
sanitized-output executor and coordinated IO admission. Then use actual shape
evidence plus a vendor-specific reference grammar to decide whether a bounded
private profile can be justified. No current source-tag allowlist, receiving
behavior or consumed admission is changed by this source-only work.

The callable slice layer `tests/private_maker_slice.py` now binds this diagnostic
to an exact read-only owned regular inode and path epoch (eight native fields),
with NOFOLLOW, payload-relative `pread`, a 3078-byte requested-read ceiling and
qualified descriptor cleanup. Source changes and observation expiry propagate
as failures rather than unsupported-format results; uncertain close overrides
a successful result and retains descriptor identity without retry. Five tiny
generated-fixture controls passed with actual child/group settlement and CPU8
release; see `tests/qualification/private-maker-slice-source-actual-20261017.json`
(actual owning terminal2a33db/0). No retained payload was opened. This callable
is not a dispatcher or admission: the frozen executor and fresh IO coordination
remain to be implemented before any retained-input inspection.

`tests/private_maker_plan.py` now specifies the exact proposed one-source
contract: retained clone identity, payload offset10990/length6556/original
base1404, little-endian candidate directory offset0, requested-read ceiling3078,
worker10s, Unison8 and EXglobal. It rejects alternate source paths, changed
epoch/geometry, scope expansion and boolean numeric aliases. Four plan controls
and the five slice controls passed together (actual59b0b6/0; child12267 reaped0,
group absent, CPU8 closed). The specified executor path is a future implementation
contract, not an existing command, admission or payload-access grant. Dispatcher
binding, independent result audit and actual retained-input coordination remain
open before execution.

The independent result auditor `tests/private_maker_audit.py` validates exact
report schemas, count/table-only read ranges and totals, sanitized decline
reasons, TIFF type/extent arithmetic and false eligibility claims. It accepts
the exact 256-entry/3078-byte boundary and rejects tampered reports. Five audit
controls plus nine plan/reader controls passed (actuald927fb/0, child12640
reaped0/group absent, CPU8 closed); evidence is in
`tests/qualification/private-maker-audit-source-actual-20261017.json`. This is
metadata consistency only: no raw payload authentication, process-settlement
proof or descriptor-release authority is inferred. No retained payload read.
