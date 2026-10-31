#!/bin/bash
# Fully cold Ten: unmount and mount it again before each measurement, dropping its
# catalog, attributes and data caches; the Quasar set is re-read warm by the harness.
set -e
R=$HOME/src/semantic-unison; S=/Volumes/Quasar/packdir-bench/leafset-v1; B=/Volumes/Ten/packdir-bench
A=(--unison "$R/build-semdiff/ox/unison" --packdir "$R/build-semdiff/.dune-5.2.0+ox/default/tools/packdir/main.exe")
cold() { cd /; diskutil unmount /Volumes/Ten >/dev/null && diskutil mount disk17s2 >/dev/null; test -d "$B"; }
walk() { python3 -c '
import os, sys, time
t, n = time.monotonic(), 0
for r, ds, fs in os.walk(sys.argv[1]):
    for f in ds + fs: os.lstat(os.path.join(r, f)); n += 1
print("{\"cold_walk\": \"%s\", \"seconds\": %.3f, \"entries\": %d}" % (sys.argv[1], time.monotonic() - t, n))' "$1"; }
# Warm Quasar first, outside the harness, so the harness's own warm-up costs nothing on Ten.
find "$S" -type f -exec cat {} + > /dev/null
cold; python3 "$R/tools/packdir/bench.py" incremental "$S" "$B/run1" --methods plain "${A[@]}"
cold; python3 "$R/tools/packdir/bench.py" incremental "$S" "$B/run2" --methods sqlar-w4 "${A[@]}"
cold; walk "$B/run1/plain"
cold; walk "$B/run2/sqlar-w4"
