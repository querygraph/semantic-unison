"""One original child plus bounded real OS-probe children; no SDK or payload."""
import json
import os
from pathlib import Path
import sys
import time
from probe import Probe,invoke
from retained import RetainedSamples

artifact=Path('/private/tmp/unison-os-process-observation-20261016a/controls/probe')
probe=Probe(artifact,'fc122e591ef1b5e2c943675c4193ac19b43870ba4e08597e7f894f7a91a1b017',limit=3)
out=invoke([sys.executable,'-c','import time;time.sleep(.4)'],dict(os.environ),time.monotonic()+10,
           observation_factory=lambda owner:RetainedSamples(owner,probe,limit=3),observation_interval=.05)
samples=out['process_observations']['samples']
assert len(samples)==3 and len(probe.outcomes)==3
assert all(s['observation']['available'] and s['observation']['threads']>=1 and s['observation']['resident_bytes']>0 for s in samples)
for outcome in [out]+probe.outcomes:
    assert outcome['returncode']==0 and outcome['client_cleanup']['reaped'] and outcome['client_cleanup']['other_group_members_absent_before_reap']
    try:os.waitpid(outcome['client_cleanup']['pid'],os.WNOHANG)
    except ChildProcessError:pass
    else:raise AssertionError('child not reaped')
print(json.dumps(dict(observed_child=out,probe_children=probe.outcomes,probe_sha256=probe.sha256,
                     sdk_calls=0,scope='three sampled per-process observations; not peak/tree RSS, thread cap or SDK qualification')))
