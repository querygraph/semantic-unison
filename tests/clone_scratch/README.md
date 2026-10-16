# Descriptor-relative native clone scratch qualification

This fixture compiles private snapshots of the actual three clone-stage ABIs
and the production Fs wrappers. Native C-only syscall wrappers inject faults;
released-runtime work makes no OCaml callback. The production tree has no fault
API, preference, environment switch or injected source. All filesystem fixtures
are disposable synthetic files under a retained /private/tmp directory.

Run both compiler-matched controls:

    python3 tests/clone_scratch/run.py --ocamlopt /usr/local/bin/ocamlopt
    python3 tests/clone_scratch/run.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt

The complete run executes 182 direct cases: 61 legacy, 61 strict two-descriptor
and 60 creation-parent-handle cases. Success checks exact independent cloned
bytes, read-only unlinked basis, writable output, access/CLOEXEC, normalization,
parent identity, source metadata and descriptor counts. The fixture obtains the
actual native filesystem type and requires APFS.

Controls include:

- Rename/rebind the destination parent immediately after its native open.
  Reservation creation, removal and both clone syscalls retain the original
  directory. Check actual reservation-parent device/inode, original/replacement
  inventories and unchanged replacement-directory mtime/ctime.
- Deterministic exclusive-open collisions with regular, symlink and directory
  sentinels, followed by success. Exhaust all 128 attempts with no deletion,
  exact bounded native counters and operational EEXIST.
- Replace or remove the reservation before its no-follow leaf lookup. Preserve
  regular/symlink/directory replacements, fail before any clone and close held
  resources. Fail native open/stat/unlink once or repeatedly and retain the first
  errno/phase. A missing cleanup name cannot mask a bad held witness.
- Distinguish basis-only ENOTSUP/EXDEV/ENOSYS declines from operational errors.
  Preserve source stability counters, source data/metadata and a replacement
  source name without using the new source as a basis.
- Fail initial basis/output open or first stat, and preserve unproven native
  artifacts. Replace admitted basis/output leaves and preserve foreign names;
  later cleanup failure preserves the original operational phase.
- Permit identity-bound cleanup after an extra hardlink or mode/mtime change,
  preserving the other alias. These mutable properties are not ownership proof.
- Native close-error controls really close the original FD, open a /dev/null
  sentinel at the same integer and return EIO. Reservation, source, read-witness
  and parent close paths must clear slots before any subsequent cleanup. Pure
  decline cannot hide a close failure; a later close failure preserves an
  earlier primary error.
- Valid 254/255-byte, Unicode and relative destination names work with the fixed
  short internal .unison.basis-<32 lowercase hex>.unison.tmp basename.

Two private source negatives each execute through all three ABIs. The first
restores actual absolute mkstemps/unlink reservation operations while leaving
subsequent clones relative; it must fail the held-parent rebind assertion. The
second removes only the reservation identity comparison, retaining the shared
basis/output guards; replacing the reservation then exposes actual wrong unlink
and unexpected successful cloning. Each negative must fail its designated
assertion, rather than compilation or an unrelated assertion.

The runner retains source, mutation, compiler, binary and complete terminal log
pins. Native artifact inventories distinguish preserved sentinels, displaced
owned artifacts and intentionally unproven first-admission files. Development
--fixed-only or --case runs are explicitly narrower than complete qualification.

The evidence does not establish hostile namespace compare-and-unlink, a
deadline on native I/O, arbitrary crash recovery or crash durability. The
clone syscall creates no descriptor: opening/admitting its result still has
a first-admission interval. When that interval fails, an unproven basis/output
name is preserved. A late parent-close error in a successful legacy/strict
two-FD operation similarly preserves its linked output after authority is lost.
Repeated witness/removal errors can preserve a private reservation/basis. These
remaining artifacts are inspected and recorded, never removed with a blind
absolute-path cleanup.

The existing pending-signal and source/transfer-counter integration controls
are run separately by the integration owner against the same frozen production
source. No Photo, photographic payload, Adobe SDK, Lightroom catalog/cache,
preview publisher or production-volume operation is performed by this fixture.
