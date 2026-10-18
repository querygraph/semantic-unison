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
module S=SemanticRemoteForProducer
let () =
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 Prefs.loadStrings ["semanticdng = true";"semanticworkers = 1";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let initial=Array.length(Sys.readdir "/dev/fd") in
 let runtime=SemanticRuntime.get () in
 let path name=Filename.concat folder name in
 let original=fixture () and incoming=fixture ~xmp:"<x>two</x>      " () in
 write(path "basis") original;write(path "source") incoming;Unix.mkdir(path "foreign") 0o700;
 let directory=Fspath.canonize(Some folder) in
 let callbacks=ref 0 and foreign=ref None and directory_owner=ref None in
 let producer fd =
  incr callbacks;
  require(read(path "normal")=incoming) "producer observed wrong bytes";
  if phase="cancel" then begin
   Remote.clientCloseRootConnection(Common.Local,directory);
   require((try ignore(Unix.fstat fd);true with _->false)) "DESIGNATED remote active producer closed";
   require(read(path "normal")=incoming) "active producer name removed"
  end;
  if phase="nested-file" then begin
   let owner=NotificationPipe.prepare () in
   let descriptor=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
   NotificationPipe.adopt_read owner descriptor;
   (* Original directed loss-of-authority fixture: the real closer reports
      EBADF, rather than manufacturing a carrier or assuming settlement. *)
   Unix.close descriptor;
   try NotificationPipe.close_all owner with error->foreign:=Some error;raise error
  end;
  if phase="nested-dir" then begin
   let owner=DirectoryOwner.prepare () in directory_owner:=Some owner;
   DirectoryOwner.open_with owner (path "foreign") (fun()->());
   RemoteProducerFault.armed:=true;
   try DirectoryOwner.close owner with error->foreign:=Some error;raise error
  end in
 let before=SemanticRuntime.admission_usage () in
 let pending=S.try_transfer_with_producer ~producer ~connection:(Obj.magic 0)
  ~source:(Fspath.resolve_existing(path "source")) ~basis:(Fspath.resolve_existing(path "basis"))
  ~directory ~staging:(Path.fromString "normal") ~expected_size:8192L in
 let unknown=phase="nested-file" || phase="nested-dir" in
 let ready ()=(try Lwt.poll pending<>None with _->true) || (unknown && !callbacks=1) in
 let rec await n=if ready () then Lwt.return () else if n=0 then Lwt.fail(Failure "remote producer deadline")
  else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
 Lwt_unix.run(await 1000);Lwt_unix.run(Lwt_unix.sleep 0.01);
 if unknown then begin
  require((try Lwt.poll pending=None with _->false)) "remote nested uncertainty escaped";
  require(S.retained_publications()<>[]) "DESIGNATED remote producer lost its stage borrower";
  let scope=match S.retained_publications() with [x]->x|_->failwith "remote producer scope count" in
  require((SemanticRuntime.admission_usage()).transactions=before.transactions+1 && !callbacks=1) "remote nested admission/callback lost";
  let pair=match S.retained_publication_pair_ownership scope with Some p->p|_->failwith "missing producer pair" in
  require(NotificationPipe.read_held pair && NotificationPipe.write_held pair) "nested uncertainty closed borrowed pair";
  let known=S.retained_publication_descriptors scope in
  require(List.length known=2) "remote producer known inventory lost";
  List.iter(fun fd->ignore(Unix.fstat fd)) known;
  (match !foreign with Some error->require(S.retained_publication_cause scope==error) "foreign carrier identity lost" | _->failwith "foreign error not observed");
  (match !directory_owner with Some owner->
    require(DirectoryOwner.phase owner=DirectoryOwner.Close_uncertain && Option.is_some(DirectoryOwner.close_cause owner)) "foreign directory cause lost";
    for _=1 to 3 do (try DirectoryOwner.close owner with DirectoryOwner.Uncertain _->()) done
   | None->());
  Remote.clientCloseRootConnection(Common.Local,directory);Gc.full_major ();
  List.iter(fun fd->ignore(Unix.fstat fd)) known;
  require(read(path "normal")=incoming && (try Lwt.poll pending=None with _->false)) "nested cleanup deleted/released producer";
  if phase="nested-dir" then require(!(RemoteProducerFault.attempts)=1) "foreign directory close retried"
 end else begin
  if phase="normal" then require(Lwt.poll pending=Some true && read(path "normal")=incoming) "normal producer failed"
  else begin
   let failed=try ignore(Lwt.poll pending);false with Util.Transient _->true in
   require(failed && !callbacks=1 && not(Sys.file_exists(path "normal"))) "cancelled producer did not close/abort after return"
  end;
  require((SemanticRuntime.admission_usage()).transactions=before.transactions && S.retained_publications()=[]) "known producer scope leaked"
 end;
 require(read(path "basis")=original && read(path "source")=incoming) "remote producer originals changed";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 if not unknown then require(Array.length(Sys.readdir "/dev/fd")=initial) "known remote producer descriptors leaked";
 Printf.printf "PASS remote producer %s; in-process planner/no transport; unknowns settle at process exit only\n%!" phase
