The synthetic binary exercises original Unison C++ scheduler code only. It
includes no Adobe or codec headers, links no Adobe or codec libraries, reads no
photographs, and performs no benchmark. The runner also compiles the real SDK
adapter to unlinked object files when SDK paths are provided.

```
python3 tests/area_scheduler/run.py
python3 tests/area_scheduler/run.py \
  --sdk-root /private/tmp/unison-adobe-sdk/dng_sdk_1_7_1 \
  --dependency-build-dir /private/tmp/unison-adobe-driver-build
```

Each invocation creates a private artifact directory. `SOURCE-QUALIFICATION.json`
pins the exact local adapter/test and reviewed SDK source inputs, compiler
commands and logs. Successful source tests leave SDK runtime and multithread
production qualification false. No full Unison build is required.

For deterministic ordinary controls without sanitizer build/execution:

```sh
python3 tests/area_scheduler/run.py --plain-only
```

This also runs `activity.cpp`: bounded simultaneous 1/6/18 callback waves and
start/process/launch/finish failure observations. It checks joined callback
retirement, partition counts and actual maximum simultaneous callback frames.
Frames are not OS thread counts: nested callbacks can occupy the same thread.
The SDK-header option now compiles all four single/area/memory/combined driver
configurations, without linking or executing them. Sanitizer campaigns remain
an explicit user-run workflow; no fuzzing is part of the ordinary controls.
