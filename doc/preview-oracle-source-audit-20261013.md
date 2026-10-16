# Preview oracle source audit — 2026-10-13

This note records the initial source-only orientation finding and the accepted
source correction. The initial server revision enforced current Main
orientation through decode but only logged the ImageCacheEntry orientation.
The current revision adds a fresh raw post-decode current-mapping comparison,
closing that scoped source gap. Native behavior, current cache state, committed
persistence and cold recognition remain unverified. This note adds no
operational hold, admission prerequisite, or invitation to invoke a native
oracle. The existing photo parent owns admission and coordination.

The [canonical acknowledgment](/Users/alexy/src/photo/preview-unison-coordination-20261013/ORACLE-CONTRACT-CORRECTION-ACKNOWLEDGED.json:5)
records the original preview implementation owner's acknowledgment at
2026-10-13 12:14:41 UTC. Its
[orientation contract](/Users/alexy/src/photo/preview-unison-coordination-20261013/ORACLE-CONTRACT-CORRECTION-ACKNOWLEDGED.json:18)
records the fresh raw post-decode ImageCacheEntry relation, without an invented
PyramidLevel orientation column. Helper Accessibility is already granted and
verified. The desktop was last observed locked and was not rechecked by this
source review; the external oracle window remains unreleased. This audit
neither changes those states nor requests a further approval.

## Current source follow-up and verified pins

The current canonical acknowledgment pins the server to
`82c88b6612818c2f62fc22b42b840273ceaca1208813d8da7a755f7a771d8556`
(15,465 bytes). Fresh reads match that pin, the unchanged independent review
pin below, and the acknowledgment's
[validation receipt](/Users/alexy/src/photo/native-preview-image-mapping-source-20261013/VALIDATION.json)
and [independent mapping acceptance](/Users/alexy/src/photo/native-preview-image-mapping-source-20261013/INDEPENDENT-REVIEW.json)
pins. All five authored source pins in the validation receipt also match.
Those receipts report 23 mapping cases, 16 transport/ownership cases and nine
preserved-registration cases, plus unarmed syntax preparation. The
[photo root acceptance](/Users/alexy/src/photo/preview-orientation-source-review-20261013/ROOT-ACCEPTANCE.json)
records all 48 passing and the independently repeated 23 mapping cases, with
operational admission unchanged. This audit read source/results without
running those tests.

The [current server mapping function](/Users/alexy/src/photo/native_direct_preview_probe_server.lua.in:48)
uses the owning connection's raw image-ID-indexed ImageCacheEntry row. It
preserves raw values, binds image ID, UUID and digest to current Main identity,
and only then applies the installed native `orientation or 'AB'` policy. Nil
and false may default; numeric zero and empty string remain explicit truthy
values. Receipts distinguish `NATIVE_DEFAULT_AB` from direct stored equality.

Before-load and post-load observations are recorded, but only the
[fresh post-decode relation](/Users/alexy/src/photo/native_direct_preview_probe_server.lua.in:174)
participates in candidate qualification. The
[qualification expression](/Users/alexy/src/photo/native_direct_preview_probe_server.lua.in:181)
requires that mapping relation alongside the decoded-to-Main orientation
comparison. Absent, stale, wrong-image or mismatched current post-decode rows
cannot qualify. An absent or stale pre-load mapping does not block a valid
current post-decode mapping. A stale returned parent keeps its fallback status.

This is source acceptance only: native loading may refresh mapping from the
requested orientation, so equality does not prove preexisting registration,
continuous equality, committed state or cold persistence. The canonical
receipt explicitly records native mapping verification false and zero native
invocations for this coordination.

## Historical initial pins and review scope

The [preserved earlier acknowledgment](/Users/alexy/src/photo/preview-orientation-source-review-20261013/PREVIOUS-CANONICAL-ACKNOWLEDGMENT.json)
records the 2026-10-13 10:48:20 UTC contract and pins. Both values matched the
files read for the initial audit; the server has since changed:

| Authored source | SHA-256 |
| --- | --- |
| [Independent review](/Users/alexy/src/photo/NATIVE-DIRECT-PREVIEW-INDEPENDENT-REVIEW-20261013.md:1) | `9652bf888087d90288576508084bab97f7ca47dc6e898fb3fd8d0c01293da34f` |
| [Preserved original server template](/Users/alexy/src/photo/native-preview-image-mapping-source-20261013/history/native_direct_preview_probe_server.lua.in:1) | `733449316fa6d18a02c6fce31136c0933aa59ff86309c87f9e11bd76a0e00b34` |

The UI controller, Main observer, and file verifier were also read for the
initial trace. The earlier acknowledgment pinned the two files above without
pinning those three additional files. The newer validation receipt additionally
pins Main/UI source. No Adobe invocation, native probe, Main or preview database
access, Photo payload read, build, or test run occurred during either audit.
Only Unison documentation was authored.

## Main orientation is enforced

The [Main observer query](/Users/alexy/src/photo/native_direct_preview_probe_main.lua.in:12)
captures `Adobe_images.orientation` with image/root-file identity, file UUID,
the latest develop-settings row, and current digest. It checks the expected
identity and a present orientation. Its
[after-observation comparison](/Users/alexy/src/photo/native_direct_preview_probe_main.lua.in:24)
requires those values, including orientation, to match the captured before
observation.

The [UI controller](/Users/alexy/src/photo/native_direct_preview_probe_ui.lua.in:154)
assigns the captured Main orientation to `c.orientation`. The
[server load specification](/Users/alexy/src/photo/native_direct_preview_probe_server.lua.in:123)
uses that value. Before decoding, the server saves the selected native row's
width and height, current digest, and `c.orientation` as expectations. Its
[post-decode comparison](/Users/alexy/src/photo/native_direct_preview_probe_server.lua.in:172)
requires actual decoded width, height, digest, and orientation to match those
saved expectations. That result participates in candidate qualification.

These checks implement the orientation comparison illustrated by the
[independent review](/Users/alexy/src/photo/NATIVE-DIRECT-PREVIEW-INDEPENDENT-REVIEW-20261013.md:9).
The before/after Main comparison certifies those observations; it does not
certify every intermediate instant.

## Historical finding: ImageCacheEntry orientation was logged but unenforced

At the earlier `733449…` server revision, `lastCacheEntryForImage(c.image)`
returned UUID, digest and orientation were
[logged at line 67](/Users/alexy/src/photo/native-preview-image-mapping-source-20261013/history/native_direct_preview_probe_server.lua.in:67).
The identity was used for fallback preservation and busy checks. No comparison
against that mapping orientation appeared in the inspected server, Main
observer, UI controller or file verifier. The original
[qualification expression at line 146](/Users/alexy/src/photo/native-preview-image-mapping-source-20261013/history/native_direct_preview_probe_server.lua.in:146)
included decoded-to-Main orientation without the mapping relation. These links
refer to the preserved historical source; the current server contains the
corrected revision described above.

The [file verifier](/Users/alexy/src/photo/verify_native_preview_files.py:219)
selects `LEVEL` receipts, validates native row/current key binding, checks
stable file identity and positive registered byte counts, inspects JPEG
dimensions/framing, and checks the limited native/ICC profile evidence. It
does not read or compare the `IMAGE_CACHE_ROW` orientation receipt. Its
[declared limitations](/Users/alexy/src/photo/verify_native_preview_files.py:225)
explicitly leave native decode, current Main identity, and restart recognition
to native receipts.

The initial finding required distinguishing a row bound to the current image
UUID/digest from a stale fallback row. Blindly comparing the latter to current
Main would conflate fallback observation with current-mapping evidence. The
accepted raw post-decode comparison now makes that distinction. Neither audit
proposes cache/Main mutation or a new operational prerequisite.

## Other corrected guards and completion scope

The pinned server contains whole-pyramid UUID/current-digest binding, current
per-level digest and native-row geometry binding, saved expectations followed
by actual decoded geometry checks, positive native file-size equality, and
immediate deadline checks after load and decode. Absent, zero, or unknown
registered file size remains unqualified. It does not require or synthesize a
per-level UUID. The deadline checks cannot preempt a synchronous native call.

The [controller's completion receipt](/Users/alexy/src/photo/native_direct_preview_probe_ui.lua.in:144)
explicitly reports candidate observations and retains independent file/JPEG
validation and fresh post-restart loading as separate evidence. File identity
and byte checks in the verifier do not prove native registration or cold
recognition. No durable or restart success is claimed by this source audit.
