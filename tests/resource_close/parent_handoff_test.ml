module P=StagePublication
external mode : int -> unit = "owned_fixture_mode"
external closes : unit -> int = "owned_fixture_closes"
let require yes why=if not yes then failwith why
let write path data=let c=open_out_bin path in output_string c data;close_out c
let read path=let c=open_in_bin path in let s=really_input_string c(in_channel_length c) in close_in c;s
let unavailable fd=try ignore(Unix.fstat fd);false with Unix.Unix_error(Unix.EBADF,_,_)->true
let uncertain f=try f();failwith "expected native uncertainty" with P.Ownership_uncertain(Some owner) as e -> owner,e
let () =
 let phase=Sys.argv.(1) in mode 0;
 Unix.mkdir "in" 0o700;Unix.mkdir "out" 0o700;write "in/stage" "private original payload";
 let root=Sys.getcwd () in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let handoff=P.prepare_parent_handoff () in
 require(not(P.parent_consumed handoff)) "new acknowledgement already consumed";
 let owner=P.prepare_owned ~working_dir:root ~stage:"in/stage" ~temporary:"out/temp" in
 let parent=Unix.openfile "in" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let input=Unix.openfile "in/stage" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
 if phase="ordinary" then begin
  P.abort_owned owner;
  let failed=try P.adopt_owned_tracked owner handoff ~parent ~stage:input;false
    with Unix.Unix_error(Unix.EINVAL,_,_)->true in
  require(failed && P.parent_consumed handoff && unavailable parent) "ordinary failure lost parent consumption";
  Unix.close input
 end else if phase="preentry" then begin
  mode 4;
  let _,error=uncertain(fun()->P.adopt_owned owner ~parent ~stage:input) in
  let before=P.owned_evidence owner and count=closes () in
  let fresh=Unix.openfile "in" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let _,again=uncertain(fun()->P.adopt_owned_tracked owner handoff ~parent:fresh ~stage:input) in
  require(again==error && not(P.parent_consumed handoff)) "DESIGNATED rejected context falsely acknowledged parent";
  ignore(Unix.fstat fresh);
  require(P.owned_evidence owner=before && closes()=count) "preentry rejection performed native work";
  let refused=try P.adopt_owned_tracked owner handoff ~parent:fresh ~stage:input;false with Invalid_argument _->true in
  require(refused && not(P.parent_consumed handoff) && closes()=count) "rejected handoff was retried/reset";
  Unix.close fresh;Unix.close input
 end else if phase="after" || phase="before" then begin
  mode(if phase="after" then 4 else -2);
  let owner,_=uncertain(fun()->P.adopt_owned_tracked owner handoff ~parent ~stage:input) in
  require(P.parent_consumed handoff) "native postentry failure not acknowledged";
  ignore(Unix.fstat parent);
  let _,_,errors,known=P.owned_evidence owner in
  require(Array.length errors>0 && Array.length known>0) "native owner evidence missing";
  let snapshot=P.owned_evidence owner and count=closes () in
  Gc.full_major ();
  require(P.parent_consumed handoff && P.owned_evidence owner=snapshot && closes()=count) "ack/native evidence lost after GC";
  Unix.close input
 end else begin
  Gc.full_major ();
  P.adopt_owned_tracked owner handoff ~parent ~stage:input;
  require(P.parent_consumed handoff) "known adopt did not acknowledge";
  if phase="repeat" then begin
   let fresh=Unix.openfile "in" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
   let count=closes () in
   let refused=try P.adopt_owned_tracked owner handoff ~parent:fresh ~stage:input;false with Invalid_argument _->true in
   require(refused && closes()=count) "duplicate handoff reached native code";
   ignore(Unix.fstat fresh);Unix.close fresh;
   P.abort_owned owner
  end else if phase="post-call" then begin
   let failed=try raise Out_of_memory with Out_of_memory->true in
   require(failed && P.parent_consumed handoff) "post-call failure erased acknowledgement";
   P.abort_owned owner
  end else begin
   P.publish_owned owner;P.disarm_owned owner;
   require(read "out/temp"="private original payload") "normal data changed"
  end;
  Unix.close input;
  require(Array.length(Sys.readdir "/dev/fd")=baseline) "known parent handoff leaked FD"
 end;
 if List.mem phase ["normal";"ordinary";"repeat";"post-call"] then
  require(Array.length(Sys.readdir "/dev/fd")=baseline) "known handoff final FD census";
 Printf.printf "PASS tracked native parent %s; unknown native owners settle at process exit only\n%!" phase
