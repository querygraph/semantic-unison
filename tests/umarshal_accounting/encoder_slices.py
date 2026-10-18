"""Original tiny malformed encoder controls; no invalid slice reaches C."""
import argparse, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[2];w=Path(tempfile.mkdtemp(prefix='unison-encoder-slices-'));w.chmod(0o700)
s=(r/'src/ubase/umarshal.ml').read_text()
s = """
let measuring_payloads = ref false
let before_buffer = ref (fun (_:int) -> ())
module OriginalBytes = Bytes
module Bytes = struct
 include OriginalBytes
 let create n = if !measuring_payloads then failwith "sizing allocated bytes" else ((!before_buffer) n; create n)
 let of_string x = if !measuring_payloads then failwith "sizing copied string" else ((!before_buffer) (String.length x); of_string x)
end
""" + s
s=s.replace('let result = Bigarray.(Array1.create char c_layout total_size) in',
 'let result = ((!before_buffer) total_size; Bigarray.(Array1.create char c_layout total_size)) in')
s+="""
let () =
 let calls = ref 0 in
 let b = Bytes.of_string "abc" in
 let reject write =
   let m = {read=(fun _ -> ());write} in
   match marshal_to_bytearray m () with
   | _ -> failwith "malformed writer accepted"
   | exception Error _ -> ()
 in
 List.iter (fun (off,len) -> reject (fun send () -> send.send b off len))
   [(-1,1);(0,-1);(4,0);(2,2);(max_int,1);(1,max_int)];
 reject (fun send () -> incr calls; if !calls=1 then send.send b 0 1 else send.send b 0 2);
 reject (fun output () -> match output.measure with
   | Some count -> count (max_int-header_size+1)
   | None -> failwith "overflow entered actual encoding");
 let m = {read=(fun _ -> ());write=(fun send () -> send.send b 1 2)} in
 let out = marshal_to_bytearray m () in
 assert (Bigarray.Array1.dim out = 10);
 assert (out.{8}='b' && out.{9}='c');
 let payload = Bigarray.(Array1.create char c_layout 17) in
 Bigarray.Array1.fill payload 'x';
 let codec = prod3 (list string) bytearray (list int64) (fun x -> x) (fun x -> x) in
 let value = (["";"abc";"payload"],payload,[0L;1L;128L;32768L;Int64.max_int]) in
 let n = ref 0 in
 measuring_payloads := true;
 codec.write {reserve_output=None;measure=Some (fun k -> n := !n+k);
              send=(fun _ _ _ -> failwith "sizing invoked byte sink")} value;
 measuring_payloads := false;
 let encoded = marshal_to_bytearray codec value in
 assert (Bigarray.Array1.dim encoded = !n+8);
 let legacy = to_string codec value in
 assert (String.length legacy = Bigarray.Array1.dim encoded);
 String.iteri (fun i c -> assert (encoded.{i}=c)) legacy;
 let credit = ref 0 and claims = ref 0 and published = ref None in
 let reserve ~bytes = incr claims; credit := !credit+bytes in
 before_buffer := (fun n -> if n > !credit then failwith "allocation before reservation";
                            credit := !credit-n);
 let owned = marshal_to_bytearray_accounted ~max_alloc_bytes:4096 ~reserve
   ~publish:(fun b -> assert (!published=None);published:=Some b) codec value in
 assert (!credit=0 && !claims>2);
 assert (match !published with Some b -> b==owned | None -> false);
 assert (Bigarray.Array1.dim owned = String.length legacy);
 String.iteri (fun i c -> assert (owned.{i}=c)) legacy;
 before_buffer := (fun _ -> ());
 let marker = Failure "original reservation refusal" in
 let refused f = match f () with _ -> failwith "reservation accepted"
   | exception e when e==marker -> () in
 claims:=0;published:=None;
 refused (fun () -> marshal_to_bytearray_accounted ~max_alloc_bytes:4096
   ~reserve:(fun ~bytes:_ -> incr claims;raise marker)
   ~publish:(fun b -> published:=Some b) codec value);
 assert (!claims=1 && !published=None);
 claims:=0;
 (match marshal_to_bytearray_accounted ~max_alloc_bytes:0 ~reserve
   ~publish:(fun b -> published:=Some b) codec value with
   | _ -> failwith "local zero budget accepted" | exception Error _ -> ());
 assert (!claims=0 && !published=None);
 let passes=ref 0 in
 let changing = prod3 string string string
   (fun x -> incr passes;
     if !passes=2 then (assert (!published<>None);raise marker);x) (fun x -> x) in
 refused (fun () -> marshal_to_bytearray_accounted ~max_alloc_bytes:4096 ~reserve
   ~publish:(fun b -> published:=Some b) changing ("a","b","c"));
 assert (!passes=2 && !published<>None);
 passes:=0;published:=None;
 (match marshal_to_bytearray_accounted ~max_alloc_bytes:(-1) ~reserve
   ~publish:(fun b -> published:=Some b) changing ("a","b","c") with
   | _ -> failwith "negative budget accepted" | exception Invalid_argument _ -> ());
 assert (!passes=0 && !published=None);
 claims:=0;published:=None;
 refused (fun () -> marshal_to_bytearray_accounted ~max_alloc_bytes:4096
   ~reserve:(fun ~bytes:_ -> incr claims;if !claims=3 then raise marker)
   ~publish:(fun b -> published:=Some b) codec value);
 assert (!claims=3 && !published<>None);
 published:=None;passes:=0;
 refused (fun () -> marshal_to_bytearray_accounted ~max_alloc_bytes:4096 ~reserve
   ~publish:(fun b -> published:=Some b;raise marker) changing ("a","b","c"));
 assert (!passes=1 && !published<>None);
 print_endline "encoder slice, sizing, parity, reservation ordering and partial-root controls passed"
"""
variants=[('positive',s,0,None),
 ('measurement-omitted',s.replace('| Some count -> count length', '| Some _ -> produce output.send'),2,'sizing allocated bytes'),
 ('scratch-reservation-omitted',s.replace('Some reserve -> reserve length','Some _ -> ()'),2,'allocation before reservation')]
for label,source,expected,witness in variants:
 d=w/label;d.mkdir(mode=0o700)
 (d/'umarshal.ml').write_text(source)
 (d/'umarshal.mli').write_bytes((r/'src/ubase/umarshal.mli').read_bytes())
 (d/'bytearray_stubs.c').write_bytes((r/'src/bytearray_stubs.c').read_bytes())
 commands=[[a.compiler,'-c','bytearray_stubs.c'],[a.compiler,'-c','umarshal.mli'],[a.compiler,'umarshal.ml','bytearray_stubs.o','-o','probe'],[str(d/'probe')]]
 for i,cmd in enumerate(commands):
  c=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=25)
  print(c.stdout,end='');print(c.stderr,end='')
  assert c.returncode == (expected if i==3 else 0)
  if i==3 and expected: assert witness in c.stderr
print('workspace',w)
