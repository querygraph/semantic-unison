module S=SemanticSyncForInputs
let require b s=if not b then failwith s
let () =
 let count=int_of_string Sys.argv.(1) and mode=Sys.argv.(2) and folder=Sys.argv.(3) in
 Prefs.loadStrings ["semanticworkers = 1";"semanticvolumejobs = 1"];
 InputOwnerFault.mode:=mode;
 let runtime=SemanticRuntime.get () in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let before=SemanticRuntime.admission_usage () in
 let active=ref None in
 let promise=SemanticRuntime.with_transaction ~max_payload:4096 (fun _ ->
  S.with_inputs count (fun owner ->
   active:=Some owner;
   for i=0 to count-1 do
    let name=if mode="open"^string_of_int i then "absent" else "input" in
    ignore(S.input_open owner i (Fspath.resolve_existing(Filename.concat folder name)) [Unix.O_RDONLY])
   done;
   if mode="error" || mode="error-all" then raise InputOwnerFault.Original_error;
   Lwt.return 17)) in
 let unknown=List.mem mode ["all";"before-all";"error-all";"slot0";"slot1";"slot2";"slot3"] in
 if unknown then begin
  require((try Lwt.poll promise=None with _->false)) "DESIGNATED input uncertainty escaped";
  require((SemanticRuntime.admission_usage()).transactions=before.transactions+1) "input admission released";
  let owner=match S.retained_inputs() with [x]->x|_->failwith "missing retained inputs" in
  require(S.retained_input_count owner=count) "slot inventory lost";
  for i=0 to count-1 do
   require(InputOwnerFault.calls.(i)=1) "independent close not attempted once";
   let slot=S.retained_input_slot owner i in
   let failed=mode="all" || mode="before-all" || mode="error-all" || mode="slot"^string_of_int i in
   require(Option.is_some(NotificationPipe.read_cause slot)=failed) "slot cause mismatch";
   require(Option.is_some(NotificationPipe.read_identity slot)) "preclose identity missing";
   if failed then ignore(Unix.fstat InputOwnerFault.fds.(i))
  done;
  if mode="error-all" then require(S.retained_input_failure owner=Some InputOwnerFault.Original_error) "original error lost";
  (try S.close_inputs owner with NotificationPipe.Uncertain _->());
  for i=0 to count-1 do require(InputOwnerFault.calls.(i)=1) "numeric descriptor retry" done
 end else begin
  let result=try Some(Lwt_unix.run promise) with _->None in
  require((result=Some 17)=(mode="known")) "ordinary outcome wrong";
  require(S.retained_inputs()=[]) "ordinary failure retained";
  require((SemanticRuntime.admission_usage()).transactions=before.transactions) "ordinary admission leaked";
  require(Array.length(Sys.readdir "/dev/fd")=baseline) "ordinary descriptor leaked";
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool)
 end;
 Printf.printf "PASS inputs%d %s\n%!" count mode
