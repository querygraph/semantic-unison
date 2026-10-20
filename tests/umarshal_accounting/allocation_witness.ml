(* Private participant instrumentation only; never linked into Unison. *)
let watching=ref false and owed=ref false and payloads=ref 0
let arm ()=watching:=true;owed:=true;payloads:=0
let reserved ~bytes =if !watching && bytes=6 then owed:=false
let before_payload length =
 if !watching && length=3 then begin
  if !owed then failwith "DESIGNATED payload allocation preceded owner reservation";
  incr payloads
 end
let stop ()=watching:=false
