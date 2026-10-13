# Capped area-task host: source review

This review records implementation against the separately obtained Adobe DNG
SDK 1.7.1 build 2724. It establishes source interfaces and the Adobe-free
scheduler behavior. It does not establish SDK runtime correctness or authorize
an Adobe invocation, benchmark or preview publication.

The SDK's `dng_host.h` declares `PerformAreaTask(dng_area_task&, const dng_rect&,
dng_area_task_progress*)` and `PerformAreaTaskThreads()`. `dng_host.cpp` sends its
default area tasks to the single-thread `dng_area_task::Perform` and returns
one thread. The supplied adapter compiles against these actual declarations.
An explicitly one-thread adapter delegates back to that original method.

`dng_area_task.h/.cpp` defines task thread limits, profitability hints, unit
cells, tile-size selection, startup, processing and finalization. The original
`Perform` computes `FindTileSize`, calls `Start(1, ...)`, processes through
`ProcessOnThread`, and calls `Finish(1)` after successful startup, including a
processing error. A startup error has no `Finish`. The new generic scheduler
preserves these lifecycle distinctions with the actual selected count and
joins every created worker before finalization or return. Per-index strips are
disjoint, span the input exactly, and have interior edges on the unit-cell
lattice relative to the destination origin. SDK `ProcessOnThread` still performs
its own nested repeating-tile and final tile-size subdivision.

The separately obtained SDK here includes existing source corrections. The
qualification receipt pins the exact reviewed files rather than assuming the
upstream version string alone identifies their contents. No SDK source or
implementation has been copied into this repository.

The important codec interaction appears in `dng_read_image.cpp`: sufficiently
small compressed tiles can be decoded by an area task. Such a tile can itself
be JPEG XL. `dng_jxl.cpp` sets the native resizable runner's total thread count
from `host.PerformAreaTaskThreads()`, unless its own single-thread flag applies.
The bundled `resizable_parallel_runner.cc` subtracts one before creating worker
threads and uses the caller to process work. The new wrapper reports one while
inside startup, any area worker, nested area task or finalization; outside those
scopes it reports the requested total allowance. This prevents nested area and
codec pools from each taking the full allowance. Worker index zero is the
calling thread; only count minus one additional area threads are created.

`dng_abort_sniffer.h` explicitly permits parallel sniff calls only when a
delegate returns `ThreadSafe()`. The new shared cooperative sniffer serializes
other delegates and checks a shared stop flag before and after forwarding a
sniff. SDK `ProcessOnThread` checks the wrapper before each tile and passes it
to task processing. One worker's error records the original exception before
signaling stop. All workers join, then finalization runs; a secondary cleanup
error cannot replace the primary error. Tile-progress callbacks share one lock.
The default validator has no external sniffer or progress reporter. Protected
nested sniffer task/progress notification forwarding is outside this adapter's
contract and is explicitly not claimed.

Concurrent unrelated top-level area calls on a shared host are rejected. Nested
area calls within a worker are synchronous and use one existing thread. The
adapter does not maintain a permanent worker pool. Task creation and worker
creation errors unwind after worker settlement; tasks own partial startup
failure cleanup, consistent with the SDK's original path. The parent process
still owns timeout/process cancellation and must reserve the requested total
CPU credits before invocation. No worker can return borrowed task, sniffer,
progress or stop-state pointers after the synchronous call ends.

The generic scheduler controls run without any Adobe or codec linkage. They
exercise allowances 1/6/18/36/128, exact strip coverage, task limits, minimum-area
hints, unit-cell edges, empty/tiny and full signed-coordinate inputs, caller
participation, nested budgets, lifecycle failures and cooperative cancellation.
They also run under AddressSanitizer/UndefinedBehaviorSanitizer. A negative
variant deliberately returns the full allowance from nested scopes and is
rejected. Actual adapter code is compiled to object files in both modes against
the local SDK headers, without linking or running either object.

The experimental build has a distinct executable name, build ID and protocol
argument. The normal Unison v1 caller cannot request it. The default build still
requires `--threads 1` and retains the existing build ID. Source controls must
not be promoted into a runtime capability or a qualified endpoint pin.

Runtime requirements remain open: faithful results versus the one-thread
reference across actual SDK task and tile layouts; buffer/allocator/index safety;
actual peak total and nested codec thread counts; sniff/cancellation behavior;
worker-creation failures under real SDK tasks; all supported compression and
mask/depth/semantic-mask cases; endpoint capability/credit negotiation; and
performance measurement in a coordinated finite window. SDK initialization,
decoding, validation and Lightroom have not been invoked by this work.
