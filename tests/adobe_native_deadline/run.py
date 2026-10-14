#!/usr/bin/env python3
"""Original synthetic process controls; no SDK or photographic inputs."""
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'bench/adobe'))
from deadline import NativeDeadline
work = Path(tempfile.mkdtemp(prefix='unison-native-deadline-', dir='/private/tmp'))
cases = []
def owner(name, **args):
    path = work/name
    path.mkdir()
    return NativeDeadline(path, **args)
normal = owner('normal', max_calls=1)
assert normal.invoke([sys.executable, '-c', 'print("original")'], timeout=1).stdout == 'original\n'
try:
    normal.invoke([sys.executable, '-c', 'raise Exception("must not enter")'], timeout=1)
except RuntimeError:
    pass
else:
    raise AssertionError('call cap failed')
assert normal.close()['closed'] and not normal.marker.exists()
cases.append('normal-exit-reap-and-call-cap')
expired = owner('expired')
expired.end = time.monotonic()+8
try:
    expired.invoke([sys.executable, '-c', 'raise Exception("must not enter")'], timeout=1)
except TimeoutError:
    pass
else:
    raise AssertionError('expired slot started native work')
assert expired.calls == [] and expired.marker.exists()
cases.append('aggregate-expiry-before-dispatch')
hung = owner('hung')
hung.end = time.monotonic()+8.2
try:
    hung.invoke([sys.executable, '-c', 'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)'], timeout=30)
except TimeoutError:
    pass
else:
    raise AssertionError('hung child returned success')
assert hung.calls[0]['client_cleanup']['reaped'] and hung.calls[0]['client_cleanup']['hard_kill_required']
assert hung.marker.exists()
cases.append('aggregate-expiry-kill-reap-unresolved-marker')
missing = owner('missing')
try:
    missing.invoke([sys.executable, '-c', 'pass'], timeout=1, settlement=work/'absent-proof')
except RuntimeError:
    pass
else:
    raise AssertionError('missing helper proof accepted')
assert missing.marker.exists()
cases.append('missing-helper-proof-retains-ownership')
(work/'RESULT.json').write_text(json.dumps({'cases':cases,'scope':'synthetic only; whole-wrapper lifetime not qualified'},indent=2)+'\n')
print(work/'RESULT.json')
