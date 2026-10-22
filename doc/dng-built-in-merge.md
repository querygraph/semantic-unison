# Opt-in built-in DNG scalar merge

Configure these rules before synchronizing the common version:

```text
backupcurrent = Name *.dng
merge = Name *.dng -> unison:dng-xmp-scalars/0
```

The exact command identifier selects the built-in policy instead of launching a
shell command. Any other command beginning with `unison:` is a reserved
built-in name: it fails the merge with "Unknown built-in merge policy" and
preserves both replicas, without starting a shell. Other `merge` commands retain
their existing behavior. This is
independent of `semanticdng` transfer optimization and defaults to disabled.
Compact metadata bases are an alternative to full saved merge bases; see
[compact capture](dng-compact-merge-base.md) before choosing backup retention.
Both current replicas must otherwise qualify for Unison's ordinary file-merge
path; filesystem property selection and user/batch acceptance remain unchanged.

The common base comes from the previous archive entries supplied to `Files.merge`.
Both entries must agree. The existing Stasher searches retained versions by that
full fingerprint, and the merge owner makes a private base copy. The built-in
then independently checks the private copy against the non-pseudo previous
fingerprint, including name/held-descriptor identity and stability before and
after hashing. The existing archive supplies the generation/path authority;
there is no new independently authoritative sidecar. An old saved version that
matches another generation but not these previous entries cannot be selected.
No base is inferred from either changed replica. Missing, stale or pseudo bases
fail the merge and preserve both live inputs.

Saved bases are full files through the existing optional backup mechanism,
possibly cloned by the ordinary local-copy implementation. The opt-in [compact base cache](dng-compact-merge-base.md) can retain just the
lossless packet and protected/content identities instead; full saved files remain
a verified fallback. No archive serialization change
is required. Raw saved packets are freshly parsed with the selected built-in
profile, parser and explicit scalar policy versions; stored parsed results are
never reused across policy changes.

The [scalar packet policy](xmp-three-way-policy-v0.md) permits only the supported
Rating/Label attribute forms. Base, left and right must have matching fixed
DNG XMP layout and identical protected bytes. Resource forks are currently
unsupported. Packet growth, competing values, deletion, rendering or unknown
field changes and changed image payloads fail conservatively. JPEG merging is
not enabled by this identifier.

A camera MakerNote (Exif tag 37500) is accepted as an opaque blob through the
merge-only profile `org.firstpair.dng-xmp/2`. Its bytes are never interpreted.
They must be identical in base, left and right, and must not overlap the XMP
packet. The merged packet keeps its exact length and position, so nothing a
MakerNote might point to moves. This profile is registered only for the local
merge. It is not selectable with `semanticprofile` and is not offered to peers,
so transfer negotiation is unchanged. `DNGPrivateData` (50740, BYTE, primary
IFD only) gets the same opaque treatment, as do single-LONG `ImageNumber`
(37393) and `CacheVersion` (51114). Other private tags still decline.

Shared workers inspect all three private files, construct the exact target plan,
and verify/materialize it in one private output already containing the left
bytes. The runtime reserves descriptors/payload before opening and uses the
same CPU/I/O/cancellation budget as semantic transfer and validation. All borrowed
jobs settle before descriptors close. Existing legacy archive fingerprinting
still runs on the owner thread under one shared CPU credit and its own base I/O
lease, released before worker inspection. Cancellation is checked around that
legacy call; it is not an interruptible or fully parallel archive pipeline.

The normal merge machinery copies that single output into its two result files
and the common-result file, then performs guarded `copyBack` for each replica.
Each configured receiving validation gate applies to its own finalized candidate.
There is no distributed atomic rename: second-receiver rejection can leave the
first committed. The conflict remains, and retry recaptures current inputs,
finds the original saved base among retained versions, generates the same exact
result and validates both receivers again. If required saved versions have been
removed/rotated away, retry declines rather than guessing. Original preservation
and backup retention use the existing backup preferences and merge lifecycle.

Disable/remove the `merge` rule to restore ordinary conflict handling. Baseline
Unison can read the unchanged archives and backups, but does not implement this
reserved built-in command identifier; remove it before running a baseline binary.
No remote extension code or command path is sent. A peer receiving the result
uses ordinary file transfer; independently configured validation still requires
its negotiated receiving capability.

[Actual CLI qualification](../tests/dng_merge/qualification.json) covers
stock/OxCaml loopback replicas with synthetic DNG-shaped containers, exact byte
convergence, both receiver gates, stale/missing bases and partial-commit recovery.
These containers qualify the sync/merge contract, not Adobe decoding or real
photographic rendering. No source photos, Lightroom caches or preview publisher
are accessed. General XMP structures, relocated/grown packets, broader M5/M6 qualification remain separate work. Compact-cache evidence has its
own [scope](dng-compact-merge-base.md).


Filesystem failures at the asynchronous merge boundary are reported as
recoverable per-file errors after owned descriptors and transaction resources
settle. Missing common bases remain an explicit refusal; other missing paths,
non-directory parents and directory outputs do not become uncaught Unix errors.
The [direct production-object controls](../tests/merge_io_errors/README.md) check
six acquisition failures and unchanged sentinels. This is error classification,
not authorization to retry with a guessed base or publish an incomplete result.
Cancellation, programming errors and allocation exceptions keep their original
identity through the existing Unix-error conversion utility.

## Checking a photo library: `unison-dngscan`

`unison-dngscan [-j WORKERS] [-o REPORT.jsonl] PATH...` walks the paths (no
symlinks followed) and checks every `*.dng` file against the merge, read-only.
Only the TIFF directories and the XMP packet are read. The scanned trees are
never written, and neither are Lightroom catalogs, caches or anything else.

Each file runs through the same inspectors the merge uses: dng-xmp `/0`, `/1`
and the merge-only `/2`. Files that pass `/2` then get an identity XmpMerge of
their packet at its fixed length. The verdicts are:

- `mergeable`: both checks pass, so a Rating/Label conflict can be merged.
- `xmp-unsupported`: the container passes, but the packet shape does not.
- `declined`: the container fails, with the inspector's first stop as the
  reason.
- `error`: the file could not be read.

For each declined file, `/2` is walked once more to list every field outside
it, by IFD, tag, type and count. That way one pass over a library shows all
the allow-list entries that would be missing. The extra findings are advisory:
the verdict always comes from the real inspector.

Files are sharded over forked worker processes, 8 by default. The summary
counts verdicts, reasons and unknown fields, each with an example path, and
`-o` writes one JSON line per file. The exit status is:

| Status | Meaning |
| --- | --- |
| 0 | every DNG is mergeable |
| 1 | some DNG is not mergeable |
| 2 | the scan is incomplete (unreadable paths or a failed worker) |

The command builds with `make -C src dngscan` or `dune build
./src/dngscan.exe`. Its findings say which files the built-in merge would
accept. They are not a DNG validity check, and they do not show what Lightroom
writes when it saves an edit.
