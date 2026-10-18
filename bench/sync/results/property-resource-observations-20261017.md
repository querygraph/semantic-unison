# Saved property-cohort resource observations

This is a metadata-only interpretation of a previously accepted functional run,
not a new synchronization or current-head performance benchmark. The saved
controller head is `a032e57039d89010610774863ff6cd9bfba6401d`; its exact binaries/source
manifests and actual owner41218/6e1b75/0 are retained in the separate
[property qualification](../../../tests/qualification/pr13-properties-actual-20261017.json).
The input SHA is `e62691e3e467416227a30a5c5c9ac84afa13b4e9730907672776471987f43a17`.

The cohort has18rows/54CLI, generated two2MiB files, property removal/old-reader
checks, workers1/2/3 per endpoint and no measured repetitions beyond one per row.
Fixture generation, seed synchronization and independent hashing warm the data;
cache state is uncontrolled. Transport is a private Unix-socket/pipes SSH
replacement, without encryption or physical-network measurement.

Worker1 examples below are individual saved update calls. They do not
provide a reliable latency/throughput ranking or a median over repetitions.

| Build / mode | Wall s | Client / server CPU s (separate) | Forwarded client→server / server→client B | Returned semantic writes B | Non-inherited output model B |
| --- | ---: | ---: | ---: | ---: | ---: |
| stock / ordinary | 0.346 | 0.098 / 0.081 | 15,527 / 19,222 | unavailable | 4,194,304 |
| stock / receiver-clone | 0.368 | 0.100 / 0.086 | 15,528 / 19,222 | unavailable | 16,384 |
| stock / semantic | 0.449 | 0.107 / 0.146 | 27,969 / 3,077 | 6,144 | 6,144 |
| ox / ordinary | 0.367 | 0.096 / 0.080 | 15,527 / 19,222 | unavailable | 4,194,304 |
| ox / receiver-clone | 0.373 | 0.094 / 0.082 | 15,562 / 19,227 | unavailable | 16,384 |
| ox / semantic | 0.448 | 0.102 / 0.144 | 28,003 / 3,082 | 6,144 | 6,144 |

The ordinary full-output and receiver-clone residual extents are explicitly
labeled models, not observed write syscalls or physical APFS writes. Semantic
6144B is a successful returned logical-write count; the transferred patch payload
is16384B. Ordinary synchronization already sends deltas, so less destination
materialization does not imply equivalent network-byte savings. The saved
semantic update wall observations are higher, not lower; full validation reads
and protocol work remain relevant, but this cohort does not isolate their costs.

Semantic primary-reader records total12583368B per row across six jobs. These
are delivered bytes, including repeated regions; nested verification and other
application reads are excluded. Ordinary/clone lack that counter, which means
unknown rather than zero. Total application reads, internal hash/parse/verify/
commit timings, descriptor/queue peaks and physical storage writes remain null.

Client and server CPU receipts may overlap through reaped descendants and must
not be summed as whole-tree CPU. RSS is normalized only for known Darwin/Linux
units and remains per-process lifetime high water, never simultaneous tree RSS.
Native block-operation counters are not converted to byte counts or block-sharing
claims. These limitations remain requirements to address, not inferred success.

[All18interpreted rows](property-resource-observations-20261017.json) retain
measured values, models and unknowns separately. The reporter follows no payload
or executable references. Its [eight controls and actual metadata owner](../../../tests/qualification/saved-sync-resource-report-actual-20261017.json)
closed without new native/SDK/Photo/IO work. Original failed/partial benchmark
samples and timing disclosures elsewhere remain unchanged; this is no replay.
