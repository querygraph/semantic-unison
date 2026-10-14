# Capped SDK host comparison preparation

`plan.py` hashes existing executables and the three accepted generated codec
inputs, then writes an exclusive output plan. It never launches a validator,
fixture writer, Lightroom or Photo process. Production endpoint settings remain
unchanged. Example, from the repository root:

```sh
python3 tests/sdk_host_matrix/plan.py \
  --reference-manifest /private/path/reference/build-manifest.json \
  --experimental-manifest /private/path/experimental/build-manifest-area-memory-unqualified.json \
  --receive-ready /private/path/previous-receive-workspace/READY.json \
  --host-memory-bytes 1073741824 \
  --output /private/tmp/new-host-comparison-plan.json
python3 tests/sdk_host_matrix/test.py
```

For each uncompressed, JPEG and JPEG XL input, the plan compares one reference
call against experimental calls with 1, 6 and 18 total requested threads,
including the caller. Calls must run sequentially: twelve calls, three inputs,
twelve logical states, eighteen reserved CPU credits and one 300-second
aggregate. A future executor must revalidate every pin before dispatch, bind a
fresh Root admission/deadline, own and reap the entire aggregate, retain all
stdout/stderr and individual results, and prove parent terminal exit separately.
There is deliberately no native execution mode in this preparation tool.

`receipt` checks exact framing, input/build identity, valid structure, successful
decode, valid raw digest and zero errors. Compare its returned fields, including
warning counts, against that codec's reference. Different warning counts need
review rather than an automatic equivalence claim. Deterministic tests exercise
all twelve argv/positive-receipt combinations and malformed receipts and plans.

Even a future pass proves validation-result equivalence only. This protocol does
not expose decoded pixels, actual area-task/thread counts, allocator peak/live
statistics or thread cancellation behavior. Those remain separate required
gates before production integration or a scaling claim. One sample per setting
is not a throughput benchmark. The memory allowance bounds covered host backing
allocations, not process RSS. No existing consumed SDK admission authorizes this
matrix, and the preparer does not create or extend a native window.
