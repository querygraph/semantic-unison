# Bounded private-data framing diagnostic

This developer tool reports an inactive TIFF IFD0 locator and Adobe/MakN framing
observation. It does not decide semantic eligibility, validate DNG or maker
references, compute a full-file SHA, decode pixels, run Adobe or publish anything.
Profiles0/1 and the normal inspector/transfer path remain unchanged.

Run the original fixed synthetic controls from the repository root:

```sh
SHARED_CPU_CREDITS=8 make -f tests/Makefile dng-private-diagnostic
```

Put the qualified CPython3.14 interpreter on PATH for this Make target (the
shared owner requires `waitid(WNOWAIT)`/`wait4`). The explicit local equivalent is:

```sh
SHARED_CPU_CREDITS=8 /Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14 tests/manual.py dng-private-diagnostic
```

One compiler job at a time, stock then Ox, plus two owner credits fits the
standing8-credit Unison lane. This target accepts no external input argument and
uses generated inert fixtures only. The [actual receipt](../../tests/qualification/private-framing-cli-controls-actual-20261016.json)
records both builds and22CLI controls, exact parent/group/token closure, and
Python's native-nanosecond FIVE/mode/nlink comparisons around those fixtures.
The initial strict-field-name compile failure is preserved; the final builds
retain warnings-as-errors. Manual target/budget/refusal mapping passed separately.

The executable itself accepts no pathname or command arguments. A future
admitting owner must open the exact permitted private file read-only, bind its
native identity/epoch, and pass that descriptor as stdin. The child requires a
single-link mode0400 regular file and issues only seeks, reads and stats on that
borrow. Its shared file position changes. It opens no source pathname, creates
no output file, performs no write on the borrow and emits one bounded JSON report
on stdout (operational errors use stderr/exit2). The child does not prove that
its supplied descriptor was opened O_RDONLY; that is the owner's responsibility.

Application read requests total at most331558bytes across773logical callbacks,
with exact requested ranges and delivered counts reported. There is no channel
prefetch. Kernel caching/read-ahead, physical disk IO, syscall scheduling, RSS and
OS thread limits are not measured or hard-capped by this tool. Recognized section
payloads are skipped, but untrusted directory pointers are only bounded and may
identify arbitrary bytes inside the admitted file: this is not proof that the
file conforms or that its claimed metadata is disjoint from all image data.

The child's Unix.stats check uses floating timestamp fields. It explicitly emits
`native_nanosecond_epoch_fence_performed_by_child=false`; the future owner must
compare the exact native nanosecond FIVE plus mode/nlink, held descriptor and
visible path before and after actual child settlement. Unknown process/FD/epoch
outcomes must retain that owner. Successful framing always reports
`semantic_eligibility=false`, `full_file_sha256_computed=false`, and
`sdk_validation=false`. No creator, section or file is added to any active profile.

The retained binaries in the synthetic receipt are not a camera-input admission.
A private-camera diagnostic still requires a separately pinned executor/plan,
source ancestry and exact identity, a finite owner lifecycle and coordinated IO
window. No original, Photo cache/Main or preserved clone has been opened by this
work. The qualified normal semantic inspector remains a separate tool with its
own full-file hashing behavior and receipts.
