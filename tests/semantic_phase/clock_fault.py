"""Original deterministic clock faults in private copies; never production mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCES=('src/semanticHash.mli','src/semanticHash.ml','src/semanticHash_stubs.c',
         'src/semanticHash_evp.h','src/semanticFile.mli','src/semanticFile.ml',
         'src/semanticFile_stubs.c','tests/semantic_phase/clock_fault.ml')


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ocamlopt',required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();records=[]
    original={name:(ROOT/name).read_bytes() for name in SOURCES}
    anchor='''#ifndef _WIN32
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0)
    seconds = (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
#endif'''
    replacements={'unavailable':'/* Keep NaN: monotonic backend unavailable. */',
                  'backwards':'static unsigned int calls = 0; seconds = (calls++ & 1U) ? 1.0 : 2.0;'}
    for fault,replacement in replacements.items():
        work=Path(tempfile.mkdtemp(prefix='unison-stage-clock-'+fault+'-'))
        for name,data in original.items():(work/Path(name).name).write_bytes(data)
        c=work/'semanticFile_stubs.c';text=c.read_text()
        assert text.count(anchor)==1,'clock fault anchor changed'
        c.write_text(text.replace(anchor,replacement))
        argv=[args.ocamlopt,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c',
              'semanticHash.mli','semanticHash.ml','semanticFile.mli','semanticFile.ml',
              'clock_fault.ml','-o','clock-fault']
        compiled=subprocess.run(argv,cwd=work,text=True,capture_output=True,timeout=30)
        (work/'build.log').write_text(compiled.stdout+compiled.stderr)
        compiled.check_returncode()
        child=subprocess.run([str(work/'clock-fault')],cwd=work,text=True,capture_output=True,timeout=5)
        child.check_returncode()
        records.append(dict(fault=fault,workspace=str(work),build_exit=compiled.returncode,
            exit_code=child.returncode,stdout=child.stdout,stderr=child.stderr,
            compiled_clock_sha256=sha(c.read_bytes()),binary_sha256=sha((work/'clock-fault').read_bytes())))
    assert all((ROOT/name).read_bytes()==data for name,data in original.items())
    args.report.write_text(json.dumps(dict(state='PRIVATE_CLOCK_FAULT_CONTROLS_PASS',
        source_pins={name:sha(data) for name,data in original.items()},controls=records,
        scope='Private deterministic unavailable/backwards monotonic backend only; no production mutation or clock fallback.'),indent=2)+'\n')
    print('PASS unavailable/backwards clock faults preserve results and reader ownership',flush=True)


if __name__=='__main__':main()
