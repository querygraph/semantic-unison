"""Original control endpoint: tiny files only; never Unison or Adobe code."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'tests/camera_sdk_concurrency')]
from shared_child import invoke
from combined_test import frame
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    d=Path(os.environ['UNISON']).parent
    if not d.name in ('stock','ox') or not d.parent.name.startswith('u-smr-wire-'):
        raise ValueError('original disposable transport controls only')
    if '-server' in sys.argv[1:]:
        outcomes=[]
        for name in ('uncompressed.dng','jpeg.dng'):
            p=d/'left'/name;data=p.read_bytes()
            if not 0<len(data)<=128:raise ValueError('tiny original input only')
            out=invoke([sys.executable,'-B','-c',
                'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())',str(p)],
                dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+10)
            proof=out['client_cleanup'];digest=hashlib.sha256(data).hexdigest()
            if not(out['returncode']==0 and proof['reaped'] and proof['other_group_members_absent_before_reap']
                   and not out['capture_truncated'] and out['stdout'].strip()==digest):
                raise ValueError('original hash helper failed')
            outcomes.append(out)
            with (d/'right'/name).open('xb') as f:f.write(data)
            # These protocol/verdict bytes are synthetic, never an SDK result.
            print('\n'.join(line for line in frame(proof['pid'],digest,len(data),1,2).splitlines()
                            if 'validation-live' not in line),flush=True)
        (d/'ORIGINAL-HELPERS.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    else:
        out=invoke([sys.executable,'-B',str(d/'launcher.py'),os.environ['UNISON_SYNC_BENCH_BINARY'],'-server'],
                   dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+15)
        proof=out['client_cleanup']
        if not(out['returncode']==0 and proof['reaped'] and proof['other_group_members_absent_before_reap']
               and not out['capture_truncated']):raise ValueError('original launcher failed')
        (d/'ORIGINAL-LAUNCHER.json').write_text(json.dumps(out,indent=2)+'\n')
        print(out['stdout'],end='',flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
