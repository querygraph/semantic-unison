let require b s = if not b then failwith s
let ok = function Ok x -> x | Error s -> failwith s
let error = function Error _ -> () | Ok _ -> failwith "expected rejection"
let write path s = let c = open_out_bin path in output_string c s; close_out c
let read path = let c = open_in_bin path in
  let s = really_input_string c (in_channel_length c) in close_in c; s
let with_file path f =
  let fd = Unix.openfile path [Unix.O_RDONLY] 0 in
  match SemanticFile.with_fd fd f with
  | x -> Unix.close fd; x | exception e -> Unix.close fd; raise e
let proof path = with_file path (fun f -> ok (SemanticDelta.inspect ~span_semantics:FormatExtension.Known_metadata (module DngSemantic) f))
let put b little off width value =
  for j = 0 to width-1 do
    let i = if little then j else width-1-j in
    Bytes.set b (off+i) (Char.chr ((value lsr (8*j)) land 255))
  done
let fixture ?(little=true) ?(opaque='A') ?(xmp="<x>one</x>      ") () =
  let b = Bytes.make 8192 '\000' in
  Bytes.blit_string (if little then "II" else "MM") 0 b 0 2;
  let u16 o n = put b little o 2 n and u32 o n = put b little o 4 n in
  u16 2 42; u32 4 8; u16 8 4;
  let entry i tag typ count value = let p = 10+12*i in
    u16 p tag; u16 (p+2) typ; u32 (p+4) count; u32 (p+8) value in
  entry 0 273 4 1 4096; entry 1 279 4 1 1024;
  entry 2 700 1 (String.length xmp) 1024;
  entry 3 50706 1 4 0;
  Bytes.blit_string "\001\004\000\000" 0 b 54 4;
  Bytes.blit_string xmp 0 b 1024 (String.length xmp);
  Bytes.fill b 4096 1024 'R'; Bytes.set b 8191 opaque;
  Bytes.to_string b
module S=SemanticRemoteForParent
let () =
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 Prefs.loadStrings["semanticdng = true";"semanticworkers = 1";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let runtime=SemanticRuntime.get () in
 let path name=Filename.concat folder name in
 let original=fixture () and incoming=fixture ~xmp:"<x>two</x>      " () in
 write(path "basis") original;write(path "source") incoming;
 let directory=Fspath.canonize(Some folder) in
 RemoteParentFault.mode:=phase;RemoteParentFault.native_mode 0;
 let producer fd=ignore(Unix.fstat fd);require(read(path "normal")=incoming) "producer bytes changed" in
 let start=SemanticRuntime.admission_usage () in
 let pending=S.try_transfer_with_producer ~producer ~connection:(Obj.magic 0)
  ~source:(Fspath.resolve_existing(path "source")) ~basis:(Fspath.resolve_existing(path "basis"))
  ~directory ~staging:(Path.fromString "normal") ~expected_size:8192L in
 let ready ()=(try Lwt.poll pending<>None with _ -> true) || S.retained_publications()<>[] in
 let rec await n=if ready () then Lwt.return () else if n=0 then Lwt.fail(Failure "parent caller deadline")
  else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
 Lwt_unix.run(await 1000);
 let unknown=List.mem phase ["preentry";"interrupted";"parent-before";"parent-after";"combined"] in
 if unknown then begin
  require(Lwt.poll pending=None) "parent uncertainty escaped transaction";
  let scope=match S.retained_publications() with [x]->x|_->failwith "parent retained scope missing" in
  let parent=match S.retained_publication_parent_ownership scope with Some x->x|None->failwith "parent ledger missing" in
  require(not(NotificationPipe.read_transferred parent)) "DESIGNATED unconsumed parent falsely transferred";
  require((SemanticRuntime.admission_usage ()).transactions=start.transactions+1) "parent transaction released";
  if phase="preentry" || phase="interrupted" then begin
   require(NotificationPipe.read_held parent && !(RemoteParentFault.parent_calls)=0) "unconsumed held parent lost";
   require(List.length(S.retained_publication_descriptors scope)=3) "known pair/parent inventory lost";
   List.iter(fun fd->ignore(Unix.fstat fd))(S.retained_publication_descriptors scope);
   if phase="preentry" then require(RemoteParentFault.native_parent_closes ()=0 && RemoteParentFault.native_closes ()= !(RemoteParentFault.before_count)) "rejected native entry consumed parent"
   else require(not !(RemoteParentFault.entered)) "interrupted acquisition entered native adopt"
  end else begin
   require(Option.is_some(NotificationPipe.read_cause parent) && !(RemoteParentFault.parent_calls)=1) "parent close error lost/retried";
   require(NotificationPipe.operation_cause parent=Some RemoteParentFault.Original_error) "parent original failure lost";
   if phase="combined" then begin
    let pair=match S.retained_publication_pair_ownership scope with Some x->x|None->failwith "pair ledger missing" in
    require(Option.is_some(NotificationPipe.read_cause pair) && Option.is_some(NotificationPipe.write_cause pair)) "combined pair causes lost"
   end;
   require(RemoteParentFault.native_parent_closes ()=0) "native closed unconsumed parent"
  end;
  let stage=Array.to_list(Sys.readdir folder)|>List.filter(fun x->x<>"basis"&&x<>"source") in
  let stage=match stage with [x]->path x|_->failwith "private interrupted stage missing" in
  let bytes=read stage and count= !(RemoteParentFault.parent_calls) and native_count=RemoteParentFault.native_closes () in
  Remote.clientCloseRootConnection(Common.Local,directory);
  Lwt_unix.run(Lwt_unix.sleep 0.02);Gc.full_major ();
  require(Lwt.poll pending=None && read stage=bytes && !(RemoteParentFault.parent_calls)=count && RemoteParentFault.native_closes ()=native_count) "cleanup retried parent/deleted stage/released result";
  List.iter(fun fd->ignore(Unix.fstat fd)) !(RemoteParentFault.recycled);
  List.iter(fun fd->ignore(Unix.fstat fd)) !(RemoteParentFault.unclosed)
 end else begin
  if phase="known" then require(Lwt.poll pending=Some true && read(path "normal")=incoming) "known parent output changed"
  else (try ignore(Lwt.poll pending);failwith "expected original parent handoff failure" with RemoteParentFault.Original_error -> ());
  require((SemanticRuntime.admission_usage ()).transactions=start.transactions) "known parent caller leaked transaction";
  let consumed=match !(RemoteParentFault.handoff) with Some h->StagePublication.parent_consumed h|None->false in
  require(consumed=(phase<>"before-call")) "actual acknowledgement changed";
  require(!(RemoteParentFault.parent_calls)=(if phase="before-call" then 1 else 0)) "local close ignored native transfer";
  require(RemoteParentFault.native_parent_closes ()=(if phase="before-call" then 0 else 1)) "native parent close multiplicity"
 end;
 require(read(path "basis")=original && read(path "source")=incoming) "source/basis changed";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 Printf.printf "PASS actual remote parent caller %s; in-process planner/no transport or SDK\n%!" phase
