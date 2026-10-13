# DNG v1 negotiation and remote compatibility

Run against isolated Make snapshots with a compiler matching the current
snapshot. The second snapshot must be the frozen v0 feature fork, which already
knows `semanticprofile`; an unmodified Unison peer does not exercise the same
unknown-profile compatibility boundary.

```sh
python3 tests/dng_profile_v1_remote.py \
  --current-build /absolute/current/build \
  --v0-build /absolute/frozen/v0/build \
  --ocamlopt /absolute/compiler/bin/ocamlopt \
  --other-unison /absolute/other/compiler/build/src/unison \
  --report /private/tmp/dng-v1-routing.json
```

The runner independently writes classic TIFF and BigTIFF in both byte orders,
with and without a camera profile using a separate opposite-endian classic CR
header and relative value offsets. Its fixed-size XMP edits go through actual
Unison receive callers in both directions. Explicit v0 selection, shorthand
selection, mixed explicit versions and v1-only selection cover new and frozen
v0 peers. Two remote roots in both root orders must receive the existing CLI
rejection, preserving source bytes/inode and an empty target. These cases do
not qualify two-remote synchronization. Opaque changes and packet layout
changes require exact ordinary fallback. Every sync checks complete root
inventories, and the final no-op preserves live inodes.
The optional other-compiler peer adds two finite CR and BigTIFF+CR cases in
both receive directions and records its binary hash and reported version.

The linked `dng_profile_v1_preferences.ml` control uses real `Prefs`, `Features`
and profile registration. It decodes outgoing preferences with the original
wire schema, checks byte equality, observes explicit false shorthand
propagation clearing a stale receiver alias, and confirms local selections
remain available for subsequent connections. It also checks default Boolean
and string-list encoding, incoming old client shorthand, both
feature-intersection orders with a first server's capability superset, and typo
rejection. The feature-order cases qualify the wire boundary without bypassing
the CLI's one-remote-root guard.

The runner retains synthetic work, logs, compiler/object/binary/source pins and
owned-group cleanup observations. It uses the previously qualified process
ownership helper from `test_positional_sync.py`. One worker per endpoint and
two consumer/source transaction slots keep these functional controls separate
from performance qualification. No Adobe invocation, DNG validity, rendered
pixel equivalence or physical I/O savings is claimed.
