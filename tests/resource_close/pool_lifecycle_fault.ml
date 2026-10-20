exception Join_failed
exception Stop_failed
exception Publication_failed
let mode=ref "known"
let joins=ref 0 and stops=ref 0 and pipes=ref 0
let after_adopt read write =
 incr pipes;PipeFault.read_fd:=read;PipeFault.write_fd:=write
let before_wrapper () =
 if String.starts_with ~prefix:"creation-" !mode then raise Publication_failed
let before_stop () =
 incr stops;
 if !mode="creation-stop" || !mode="shutdown-stop" then raise Stop_failed
let join domain =
 incr joins;
 if !mode="creation-before" || !mode="shutdown-before" then raise Join_failed;
 Domain.join domain;
 if !mode="creation-after" || !mode="shutdown-after" then raise Join_failed
let before_publish () = if !mode="handoff" then raise Publication_failed

let after_publish index =
 if (!mode="publication-first" && index=0) || (!mode="publication-second" && index=1) then
   raise Publication_failed
