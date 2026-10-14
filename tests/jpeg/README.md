# JPEG profile qualification

`run.py --ocamlopt PATH --receipt FILE` builds the production locator and
semantic kernel in a retained private tree. Independent Python fixtures check
exact offsets, maximum packet, every truncated pre-scan prefix, progressive
framing, duplicate/extended/empty packets, marker/fill/header limits, exact
apply/no-op and refusal of entropy/EXIF/ICC/trailer/growth/relocation edits.
Structural fixtures do not claim decodable JPEG pixels.

`sync.py --client BINARY --server BINARY --receipt FILE` exercises actual
negotiated receiving paths via a loopback exec launcher. Both receiving
directions must use semantic clone for eligible packet edits. Opaque/growth
edits and no-op retain exact behavior. `--legacy` expects ordinary fallback;
`--disabled` selects only semanticdng, proving it does not enable JPEG.

`decoded.py --kernel JPEG_TEST --receipt FILE` generates a private gradient BMP,
encodes JPEG through macOS sips/ImageIO, inserts a standard APP1 packet, applies
an exact edit, and compares decoded BMP geometry/bits/raster. This is one OS
codec control, not Lightroom/Adobe or broad color/profile qualification. BMP
negative height denotes top-down rows and is preserved in the comparison.
The first fixture incorrectly assumed bottom-up decode; its failed output tree
is retained. Initial clean Dune snapshots omitted the dummy unison-gui.opam;
failed build receipts are retained separately, followed by complete snapshots.

The source has no production Photo inputs, external native cache or publisher
calls. Retained local artifacts are pinned by qualification.json. Root performed
the source/evidence audit; no independent-agent implementation approval is
claimed. Future broader JPEG policies require separately versioned profiles.
