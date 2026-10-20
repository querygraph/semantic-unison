"""Compile the exact Files diagnostic guard with original sink/control faults."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
PREFIX='''exception Control_marker
module Util = struct
  let failure : exn option ref = ref None
  let msg format = Printf.ksprintf (fun _ -> match !failure with
    | None -> () | Some error -> raise error) format
end
module Trace = struct
  let failure : exn option ref = ref None
  let debug _ f = match !failure with None -> f () | Some error -> raise error
end
let report seconds =
'''
SUFFIX='''
let () =
  let checks=ref 0 in
  List.iter(fun prefix ->
    let select value = if prefix then Trace.failure:=value else Util.failure:=value in
    List.iter(fun seconds ->
      List.iter(fun error -> select(Some error);report seconds;select None;incr checks)
        [Sys_error "sink";Unix.Unix_error(Unix.EIO,"sink","");Out_of_memory];
      List.iter(fun error ->
        select(Some error);
        let propagated=try report seconds;false with observed -> observed==error in
        select None;
        if not propagated then failwith "unknown exception swallowed";
        incr checks) [Sys.Break;Exit;Failure "marker";Control_marker]) [0.25;nan]) [false;true];
  Printf.printf "PASS %d exact-source reporting sink/control cases\\n%!" !checks
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ocamlopt',required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();source=(ROOT/'src/files.ml').read_text()
    anchor='             try Trace.debug "semantic-timings" (fun () ->'
    assert source.count(anchor)==1,'reporter seam changed'
    start=source.index(anchor);stop=source.index('\n           end);',start)
    expression=source[start:stop];records=[]
    guard='''             | Sys_error _ | Unix.Unix_error _ | Out_of_memory -> ()'''
    assert expression.count(guard)==1,'qualified diagnostic policy changed'
    for name,text in [('current',expression),('swallow-control-negative',expression.replace(guard,'             | _ -> ()'))]:
        work=Path(tempfile.mkdtemp(prefix='unison-publication-report-'+name+'-'))
        fixture=PREFIX+text+SUFFIX;(work/'test.ml').write_text(fixture)
        compiled=subprocess.run([args.ocamlopt,'-I','+unix','unix.cmxa','test.ml','-o','report-test'],
                                cwd=work,text=True,capture_output=True,timeout=20)
        compiled.check_returncode()
        child=subprocess.run([str(work/'report-test')],cwd=work,text=True,capture_output=True,timeout=5)
        if name=='current':
            child.check_returncode();assert child.stdout=='PASS 28 exact-source reporting sink/control cases\n'
        else:
            assert child.returncode!=0 and 'unknown exception swallowed' in child.stderr,'negative guard not detected'
        records.append(dict(kind=name,workspace=str(work),exit_code=child.returncode,
            stdout=child.stdout,stderr=child.stderr,compiled_fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest()))
    args.report.write_text(json.dumps(dict(state='REPORTING_POLICY_CONTROLS_PASS',
        files_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        expression_sha256=hashlib.sha256(expression.encode()).hexdigest(),records=records,
        scope='Exact Files diagnostic expression; original fake sinks, both normal and unavailable duration; no native publication or payload.'),indent=2)+'\n')
    print('PASS exact-source sink/control guard plus designated swallowed-control regression',flush=True)


if __name__=='__main__':main()
