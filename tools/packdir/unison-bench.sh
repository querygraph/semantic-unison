#!/bin/bash
# Real Unison packing onto Ten: the 50 GiB leaf set into a new folder under
# /Volumes/Ten/packdir-bench, first run then a quiet rerun, each with a time limit.
set -e
U=$HOME/src/semantic-unison/build-semdiff/.dune-5.2.0+ox/default/src/linktext.exe
S=/Volumes/Quasar/packdir-bench/leafset-v1; O=${OUT:-/Volumes/Ten/packdir-bench/run4-unison}
W=$(mktemp -d /tmp/unison-bench-home.XXXX)
mkdir "$O"
find "$S" -type f -exec cat {} + > /dev/null      # warm Quasar, as the harness does
run() { UNISON=$W perl -e 'alarm shift; exec @ARGV' 1800 "$U" "$S" "$O" -batch -force "$S" -nodeletion "$O" \
          -perms 0 -times -packdepth 2 -packroot "$O" -packworkers 4 -logfile "$W/unison.log" > "$W/$1.out" 2>&1; }
for phase in first rerun; do
  io0=$(iostat -Id disk17 | tail -1 | awk '{print $2, $3}'); t0=$(python3 -c 'import time;print(time.monotonic())')
  run $phase; rc=$?; sync
  t1=$(python3 -c 'import time;print(time.monotonic())'); io1=$(iostat -Id disk17 | tail -1 | awk '{print $2, $3}')
  python3 -c "
x0,m0=map(float,'$io0'.split()); x1,m1=map(float,'$io1'.split()); dt=$t1-$t0
print('%s rc=%s %.1f s, %.1f MiB/s of 50 GiB, Ten %.0f MiB, %d ops' % ('$phase', '$rc', dt, 51200/dt if '$phase'=='first' else 0, m1-m0, x1-x0))"
  tail -1 "$W/$phase.out"
done
ls "$O" | head -20 | tr '\n' ' '; echo; ls "$O"/*/*.sqlar | wc -l
