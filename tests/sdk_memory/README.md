# Backend quota and Adobe allocator source qualification

```sh
python3 tests/sdk_memory/run.py \
  --sdk-root /private/path/dng_sdk_1_7_1 \
  --dependency-build-dir /private/path/existing-sdk-dependency-build \
  --receipt /private/tmp/memory-source.json
```

Runtime tests link only original Unison quota code and an independently authored
SDK-interface surrogate. Normal, AVX-shaped and ASan/UBSan runs cover quota
boundaries/overflow, zero allocations, padding/alignment, C callback null returns,
virtual deletion, failed construction, buffers outliving adapters, two adapters
sharing one injected quota, 1/6/18-lane contention and a held18-lane pressure wave.
Each run attempts50000 concurrent allocations. Private controls disable capacity
checks (must fail) and force malloc failure (1000 reservations must roll back).

Four actual SDK-header compilations use the separately obtained SDK1.7.1/2724
and existing generated JXL headers. They compile but do not link or execute
Adobe symbols. The SDK headers/implementation remain outside this repository.
No SDK initialization/driver/codec, Photo, Lightroom or benchmark is run.
Source and native artifacts are retained in private snapshots; failures stay
recorded. [Qualification](qualification.json) pins actual results and source.

The component enforces requested backing allocations through its adapter; it
does not bound all SDK heaps or RSS. Current core scheduling of backend resource
plans and actual SDK runtime parity remain unqualified. See the
[generic resource contract](../../doc/backend-resource-interop-v0.md).
