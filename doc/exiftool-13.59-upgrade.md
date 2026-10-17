# Perl ExifTool 13.59 baseline

The user requested version13.59 to match the separate exiftool-rs/dng-compare
work. This upgrades the optional Perl integration, not the Rust backend.

Source is the official [ExifTool13.59 tag](https://github.com/exiftool/exiftool/tree/13.59),
commit `2200871d9cef988051d2a99d67df3bda6cbb30a8`.
[Installation provenance](exiftool-13.59-installation-v1.json) records the exact
download archive and upstream/installed script hashes. The only script change
replaces its environment-selected Perl shebang with `/usr/bin/perl5.34`; mode0700.
The private versioned installation leaves shared Homebrew13.10 untouched.

[InventoryV2](mixed-exiftool-package-inventory-v2.json) pins the installed script,
all246 library files and the system Perl executable. OS Perl modules/dylibs remain
an explicit trust boundary; this is not a hermetic runtime. The verifier requires
the exact version, executable path, package root, complete roster and file hashes.

[Actual final controls](../tests/qualification/exiftool-13.59-upgrade-v2-actual-20261017.json)
passed16 inventory/plan/audit tests and two direct tool invocations. Version
reports13.59; the unchanged mixed-probe read-only JSON argv returns exact source,
version, Rating3 and Unicode Label from an original generated XMP fixture.
The generated file's bytes/epoch and package pins remained unchanged; all children
and groups settled and Unison8 released. First successful controls are retained
separately, before the added executable-path substitution rejection.

Historical13.10 inventories, actual runs, frozen requests and private-MakN source
reviews stay unchanged. Existing lifecycle fixtures retain their historical fake
version; current plan/audit mutation controls use13.59. Future mixed native runs
need new source/build pins and fresh IO coordination; no SDK/media rerun or camera,
semantic, pixel, preservation-corpus or performance qualification is inferred.

exiftool-rs reuse stays deferred until the user's extensions and dng-compare
integration are ready.
