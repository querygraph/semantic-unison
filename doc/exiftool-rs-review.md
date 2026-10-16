# Optional Rust metadata backend: source review

This is a candidate review prompted by the user's exiftool-rs question, not a
replacement for the frozen [mixed V1 request](mixed-validation-request-v1.json).
No package was installed, dependency resolved, code built or tool executed. No
image input was opened. [Downloaded source pins](exiftool-rs-source-review-inputs-v1.json)
bind four files at commit `54a885f85692674f362e6256ba8609808d746d5d` of
[Le-Syl21/exiftool-rs](https://github.com/Le-Syl21/exiftool-rs/tree/54a885f85692674f362e6256ba8609808d746d5d).

## Fit and concrete differences

The [manifest](https://github.com/Le-Syl21/exiftool-rs/blob/54a885f85692674f362e6256ba8609808d746d5d/Cargo.toml)
declares crate0.10.0, Rust1.82 minimum, GPL-3.0-or-later and an empty default
feature set. The CLI/library are separate from optional GUI/parity programs.
This is a Rust implementation with Cargo dependencies, not a Perl wrapper or
a source-dependency-free build. A pinned CLI could remove our Perl installation
dependency; that does not establish smaller resource usage or faster execution.

The [CLI argument parser](https://github.com/Le-Syl21/exiftool-rs/blob/54a885f85692674f362e6256ba8609808d746d5d/src/main.rs#L183)
recognizes JSON/short output and consumes the config argument. Its fallback
for double-hyphen arguments treats `--` as an input filename; it does not stop
option parsing. The exact current Perl argv therefore cannot be reused
unchanged. This is source evidence, not an observed executable failure. A
successor adapter needs its own fixed argv and an absolute owned candidate path.

The [library version declarations](https://github.com/Le-Syl21/exiftool-rs/blob/54a885f85692674f362e6256ba8609808d746d5d/src/lib.rs)
distinguish crate version from the targeted ExifTool13.59 compatibility version.
Our prepared Perl baseline is13.10. Output version fields must identify the
actual backend/compatibility contract; replacing values to satisfy the existing
auditor would erase provenance. Project corpus-parity claims are useful leads,
not independent evidence for Unison's DNG/XMP preservation or resource model.

## Separate evaluation path

1. Keep the frozen Perl mixed request and all326 execution pins unchanged.
   Candidate adoption is not a new gate on that run.
2. Prepare a pinned CLI-only Cargo build using the selected commit/lockfile,
   compiler and dependency inventory, without GUI or parity executables. Build
   within standing Unison8/compiler jobs<=2; no tool installation into endpoints.
3. Start with original tiny XMP/JPEG/TIFF fixtures and readonly absolute paths.
   Compare source binding, Rating/Label values, missing/duplicate/group-qualified
   tags, Unicode, malformed input, exit codes and bounded output. Preserve raw
   output differences and exact version provenance rather than rewriting them.
4. Compare against a separately pinned Perl compatibility baseline if testing
   the project's13.59 parity claim. Comparing against current13.10 remains a
   distinct experiment; version differences need explicit classification.
5. Before generated DNG or retained-camera inputs, prepare a distinct source-
   pinned IO request. Use the same IO-before-CPU ownership, helper CPU charge,
   intent/outcome persistence, independent child/group audit, byte/epoch fences
   and unknown retention as other optional tools. Do not borrow earlier grants.

Initial integration should be an optional supervised process backend. A future
library/FFI integration would require its own ownership and foreign-boundary
review. The Rust parser is not a replacement for the exact-byte semantic kernel,
complete preservation partition, receiving commit checks or optional Adobe raw
validation. No implementation/adoption, semantic eligibility, pixels, resource
cap, throughput or production qualification is established by this review.
