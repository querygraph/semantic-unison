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
module S=SemanticRemoteForPair
let () =
 let folder=Sys.argv.(1) and kind=Sys.argv.(2) and phase=Sys.argv.(3) in
 Prefs.loadStrings["semanticdng = true";"semanticworkers = 1";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let runtime=SemanticRuntime.get() in
 let path name=Filename.concat folder name in
 let original=fixture() and incoming=fixture ~xmp:"<x>two</x>      " () in
 write(path "basis") original;write(path "source") incoming;
 let directory=Fspath.canonize(Some folder) in
 RemotePairFault.mode:=phase;
 let callbacks=ref 0 in
 let producer fd=
  incr callbacks;ignore(Unix.fstat fd);
  require(read(path "normal")=incoming) "producer bytes changed";
  if phase="callback" then raise RemotePairFault.Original_error in
 let before=SemanticRuntime.admission_usage () in
 let pending=if kind="bound" then S.try_transfer_with_producer ~producer ~connection:(Obj.magic 0)
   ~source:(Fspath.resolve_existing(path "source")) ~basis:(Fspath.resolve_existing(path "basis"))
   ~directory ~staging:(Path.fromString "normal") ~expected_size:8192L
 else S.try_transfer ~connection:(Obj.magic 0) ~source:(Fspath.resolve_existing(path "source"))
   ~basis:(Fspath.resolve_existing(path "basis")) ~directory ~staging:(Path.fromString "normal") ~expected_size:8192L in
 if phase="known" then begin
  require(Lwt_unix.run pending) "known pair transfer declined";
  require(read(path "normal")=incoming) "known final bytes changed";
  require((SemanticRuntime.admission_usage ()).transactions=before.transactions) "known admission leaked"
 end else begin
  let rec await n=if S.retained_publications()<>[] then Lwt.return ()
    else if n=0 then Lwt.fail(Failure "retained remote pair deadline")
    else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
  Lwt_unix.run(await 1000);
  require(Lwt.poll pending=None) "DESIGNATED raw pair uncertainty escaped";
  let held=SemanticRuntime.admission_usage () in
  require(held.transactions=before.transactions+1 && held.descriptors>before.descriptors) "raw pair released admission";
  let scope=match S.retained_publications() with [x]->x|_->failwith "missing raw pair scope" in
  let owner=match S.retained_publication_pair_ownership scope with Some x->x|None->failwith "pair owner missing" in
  require(Option.is_some(NotificationPipe.read_cause owner)=(phase<>"write")) "read cause missing";
  require(Option.is_some(NotificationPipe.write_cause owner)=(phase<>"read")) "write cause missing";
  require(Option.is_some(NotificationPipe.read_identity owner) && Option.is_some(NotificationPipe.write_identity owner)) "pair identities missing";
  if phase="callback" || phase="record" || phase="register" then
   require(NotificationPipe.operation_cause owner=Some RemotePairFault.Original_error) "primary error lost";
  require(!(RemotePairFault.read_calls)=1 && !(RemotePairFault.write_calls)=1) "pair close count";
  let stage=if Sys.file_exists(path "normal") then path "normal" else
   let candidates=Array.to_list(Sys.readdir folder)|>List.filter(fun x->x<>"basis"&&x<>"source") in
   match candidates with [x]->path x|_->failwith "private stage not preserved" in
  require(Sys.file_exists stage) "private name removed after close uncertainty";
  let image=read stage in
  Remote.clientCloseRootConnection(Common.Local,directory);
  Lwt_unix.run(Lwt_unix.sleep 0.02);Gc.full_major ();
  require(Sys.file_exists stage && read stage=image && Lwt.poll pending=None) "connection cleanup deleted stage/released owner";
  require(!(RemotePairFault.read_calls)=1 && !(RemotePairFault.write_calls)=1) "numeric close retry";
  List.iter(fun fd -> ignore(Unix.fstat fd)) !(RemotePairFault.recycled);
  List.iter(fun fd -> ignore(Unix.fstat fd)) !(RemotePairFault.unclosed);
  let after=SemanticRuntime.admission_usage () in
  require(after.transactions=held.transactions && after.descriptors=held.descriptors) "connection cleanup retired unknown";
  require(S.retained_publication_descriptors scope=[]) "uncertain/closed FD misreported as known-held"
 end;
 require(read(path "basis")=original && read(path "source")=incoming) "source/basis changed";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 Printf.printf "PASS actual remote pair %s/%s; in-process planner, no transport/SDK\n%!" kind phase
