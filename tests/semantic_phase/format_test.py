"""Compile the exact owner reporter with original fake sinks; detect old grouping."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
from phase_stats import parse

PREFIX='''module SemanticFile = struct
  type stage = Hash | Parse | Verify | Write
  type sample = {stage:stage;calls:int;inclusive_seconds:float}
  type read_stats = {logical_bytes:int64;chunks:int64;saturated:bool;stages:sample list option}
end
module Trace = struct
  let enabled name = name="semantic-timings"
  let debug name f = if enabled name then begin Printf.printf "[%s] " name;f () end
end
module Util = struct let msg format = Printf.printf format end
let () =
  let measure_stages=true in
'''
SUFFIX='''
  let emit id stages = match read_observer with None -> failwith "observer missing"
    | Some f -> f id {SemanticFile.logical_bytes=0L;chunks=0L;saturated=false;stages} in
  let samples=List.map(fun stage -> {SemanticFile.stage;calls=1;inclusive_seconds=0.125})
    [SemanticFile.Hash;SemanticFile.Parse;SemanticFile.Verify;SemanticFile.Write] in
  emit 0 (Some samples);emit 1 None;
  if Array.length Sys.argv>1 then emit 2 (Some []);
  emit 3 (Some [{SemanticFile.stage=SemanticFile.Parse;calls=1;inclusive_seconds=0.}])
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('ocamlopt','baseline-source','baseline-sha256','report'):p.add_argument('--'+name,required=True)
    a=p.parse_args();baseline=Path(a.baseline_source).read_bytes()
    if hashlib.sha256(baseline).hexdigest()!=a.baseline_sha256:raise ValueError('baseline source pin differs')
    records=[]
    for label,raw in [('current',(ROOT/'src/semanticRuntime.ml').read_bytes()),('grouped-baseline',baseline)]:
        source=raw.decode();anchor='    let read_observer =';assert source.count(anchor)==1
        start=source.index(anchor);end=source.index('    let pool = SemanticWorkers.create_with_io',start)
        expression=source[start:end];fixture=PREFIX+expression+SUFFIX
        work=Path(tempfile.mkdtemp(prefix='unison-phase-format-'+label+'-'));(work/'test.ml').write_text(fixture)
        compiled=subprocess.run([a.ocamlopt,'test.ml','-o','format-test'],cwd=work,capture_output=True,text=True,timeout=20)
        (work/'build.log').write_text(compiled.stdout+compiled.stderr);compiled.check_returncode()
        cases=[]
        for empty in (False,True):
            child=subprocess.run([str(work/'format-test')]+(['empty'] if empty else []),cwd=work,capture_output=True,text=True,timeout=5)
            child.check_returncode();failure=None
            try:observations=parse(child.stdout,required_workers=True)
            except ValueError as error:failure=str(error);observations=None
            complete=observations is not None and observations['observed_worker_stages']==['hash','parse','verify','write'] and len(observations['records'])==6
            if label=='current':assert complete and observations['reported_worker_jobs']==3
            else:assert not complete,'old grouped reporter was not detected'
            cases.append(dict(empty_sample_included=empty,stdout=child.stdout,stderr=child.stderr,
                exit_code=child.returncode,strict_observations=observations,strict_error=failure,all_phases_parse=complete))
        records.append(dict(kind=label,source_sha256=hashlib.sha256(raw).hexdigest(),
            extracted_expression_sha256=hashlib.sha256(expression.encode()).hexdigest(),
            workspace=str(work),fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest(),cases=cases))
    Path(a.report).write_text(json.dumps(dict(state='CURRENT_PER_LINE_FORMAT_PASS_OLD_GROUPED_REGRESSION_DETECTED',records=records,
        scope='Exact owner-source expression with fixed fake Trace/Util/SemanticFile data, no real worker/SDK/sync.'),indent=2)+'\n')
    print('PASS current each-line prefixes/empty-list silence plus old grouped reporter regression',flush=True)

if __name__=='__main__':main()
