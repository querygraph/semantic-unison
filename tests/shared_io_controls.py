"""Finite IO source/mock controls: no canonical IO or media payload access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ('tests/shared_io_plan_test.py', 'tests/shared_io_dispatch_test.py',
           'tests/shared_io_dispatch_lifecycle_test.py', 'bench/sync/artifact_pins_test.py',
           'bench/sync/properties_test.py', 'bench/sync/invocation_journal_test.py',
           'bench/sync/journal_lifecycle_test.py')

def main():
    if len(sys.argv) != 1:
        raise ValueError('fixed source controls only')
    os.umask(0o077)
    work=Path(tempfile.mkdtemp(prefix='unison-io-source-controls-'))
    sources=(*SCRIPTS, 'tests/shared_dispatch.py', 'tests/shared_io_pool.py',
             'tests/shared_cpu_pool.py','tests/shared_process_owner.py','tests/manual.py',
             'tests/shared_io_plan.py','bench/sync/artifact_pins.py','bench/sync/run.py',
             'tests/shared_io_controls.py','bench/sync/properties.py','bench/sync/shared_audit.py',
             'bench/sync/invocation_journal.py','bench/sync/proxy.py',
             'bench/sync/measure.py','bench/sync/ownership.py')
    def pins():
        return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    before=pins();rows=[]
    for number,name in enumerate(SCRIPTS):
        log=work/(str(number)+'.log')
        with log.open('xb') as stream:
            child=subprocess.Popen([sys.executable,str(ROOT/name)],stdout=stream,stderr=subprocess.STDOUT)
            code=child.wait(timeout=20)
        row={'script':name,'pid':child.pid,'actual_wait_exit':code,'log':str(log),
             'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
        rows.append(row);print(json.dumps(row),flush=True)
        if code:
            raise RuntimeError(log.read_text(errors='replace'))
    if before!=pins():raise RuntimeError('control source changed')
    print(json.dumps({'schema':'unison-io-source-controls/1','complete':True,
                      'workspace':str(work),'sources':before,'calls':rows}),flush=True)

if __name__=='__main__':main()
