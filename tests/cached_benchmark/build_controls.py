"""Current-object builds and original64B reader controls; never a bulk matrix."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cached_benchmark.contract import ROOT, document
from cached_benchmark.entry import write


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stock','ox','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();out=Path(args.output)
    command=[sys.executable,str(ROOT/'bench/semantic/run.py'),'--build-only','--keep-work',
             '--work-parent',str(out),'--workers','1,2,4,6','--jobs','6','--file-mib','32',
             '--repetitions','5','--warmups','1','--output',str(out/'BUILD.json')]
    for label in ('stock','ox'):
        build=document(getattr(args,label))
        command+=['--compiler',label+'='+str(Path(build['compiler']).resolve()),
                  '--build',label+'='+str((Path(build['workspace'])/'src').resolve())]
    subprocess.run(command,check=True,timeout=45)
    build=document(out/'BUILD.json')
    assert build['build_complete'] and not build['measurement_complete'] and not build['samples']
    assert not (Path(build['retained_workspace'])/'synthetic.bin').exists()
    fixture=out/'original64.bin';data=bytes(range(64));fixture.write_bytes(data)
    expected=hashlib.sha256(data).hexdigest();records=[]
    for label in ('stock','ox'):
        binary=build['compilers'][label]['benchmark_binary_path']
        child=subprocess.run([binary,str(fixture),expected,'64','1','1'],
                             capture_output=True,text=True,timeout=10)
        child.check_returncode();v=json.loads(child.stdout)
        assert (v['primary_logical_read_bytes'],v['primary_read_chunks'],
                v['primary_read_observations'],v['correct_digests'])==(64,1,1,1)
        assert v['final_cpu_permits']==0 and v['baseline_fd_count']==v['final_fd_count']
        records.append(dict(compiler=label,exit_code=child.returncode,raw_stdout=child.stdout,
                            stderr=child.stderr,observations=v))
    write(out/'RESULT.json',dict(state='BUILD_AND_DIRECTED64B_CONTROLS_PASS',
        build=build,controls=records,fixture_bytes_written=64,primary_logical_bytes_read=128,
        bulk_matrix_executed=False,scope='Two original tiny reader controls, no timing/scaling qualification, SDK, Adobe or Photo payload.'))
    print('PASS both current builds and two64B directed read-accounting controls',flush=True)


if __name__=='__main__':main()
