# Opt-in built-in DNG scalar merge

Configure these rules before synchronizing the common version:

```text
backupcurrent = Name *.dng
merge = Name *.dng -> unison:dng-xmp-scalars/0
```

The exact command identifier selects the built-in policy instead of launching a
shell command. Other `merge` commands retain their existing behavior. This is
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
