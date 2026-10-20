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
module S=SemanticRemoteForOwned
external mode : int -> unit = "owned_fixture_mode"
external closes : unit -> int = "owned_fixture_closes"
let marker=Failure "original producer callback failure"
let ()=
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 Prefs.loadStrings["semanticdng = true";"semanticworkers = 2";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let runtime=SemanticRuntime.get() in
 let path name=Filename.concat folder name in
 let original=fixture() and incoming=fixture ~xmp:"<x>two</x>      " () in
 write(path "basis") original;write(path "source") incoming;
 let directory=Fspath.canonize(Some folder) in
 let callbacks=ref 0 in
 mode(if phase="adopt-close" then 1 else 0);
 let producer fd=
  incr callbacks;
  require(read(path "normal")=incoming) "producer did not see exact promoted bytes";
  ignore(Unix.fstat fd);
  if phase="disarm-close" || phase="callback-close" then mode(-1);
  if phase="callback-close" then raise marker in
 let before=SemanticRuntime.admission_usage() in
 let pending=S.try_transfer_with_producer ~producer ~connection:(Obj.magic 0) ~source:(Fspath.resolve_existing(path "source"))
  ~basis:(Fspath.resolve_existing(path "basis")) ~directory ~staging:(Path.fromString "normal") ~expected_size:8192L in
 if phase="normal" then begin
  require(Lwt_unix.run pending) "normal receiver-unit owned publication declined";
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=before.transactions && after.descriptors=before.descriptors) "normal reservation leaked";
  require(!callbacks=1 && read(path "normal")=incoming) "normal output/callback count"
 end else begin
  let rec wait count=
   if S.retained_publications()=[] && count>0 then Lwt.bind(Lwt_unix.sleep 0.01)(fun()->wait(count-1)) else Lwt.return() in
  Lwt_unix.run(wait 300);
  require(Lwt.poll pending=None) "uncertain receiver-unit publication escaped reservation";
  let held=SemanticRuntime.admission_usage() in
  require(held.transactions=before.transactions+1 && held.descriptors>before.descriptors && held.payload_bytes>before.payload_bytes)
   "uncertainty released outer transaction credits";
  let owner=match S.retained_publications() with [owner]->owner|_->failwith "missing retained receiver-unit owner" in
  let native=match S.retained_publication_native owner with Some x->x|_->failwith "native carrier lost" in
  let evidence=StagePublication.owned_evidence native and count=closes() in
  let known=S.retained_publication_descriptors owner in
  let pair=match S.retained_publication_pair_ownership owner with Some x->x|None->failwith "raw pair ledger lost" in
  if phase="callback-close" then
   require(known=[] && NotificationPipe.settled pair) "known-closed pair reported as live after native abort uncertainty"
  else require(List.length known>=2 && not(NotificationPipe.settled pair)) "remaining transaction descriptors not retained";
  List.iter(fun fd->ignore(Unix.fstat fd))known;
  if phase="callback-close" then require(S.retained_publication_cause owner==marker) "original callback cause lost";
  require(!callbacks=(if phase="adopt-close" then 0 else 1)) "callback omitted/repeated after uncertainty";
  Remote.clientCloseRootConnection(Common.Local,directory);
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  List.iter(fun fd->ignore(Unix.fstat fd))known;
  require(Lwt.poll pending=None && StagePublication.owned_evidence native=evidence && closes()=count)
   "connection cleanup retried native ownership or released pending operation";
  let after=SemanticRuntime.admission_usage() in
  require(after.transactions=held.transactions && after.descriptors=held.descriptors && after.payload_bytes=held.payload_bytes)
   "connection cleanup released unknown admission";
  if phase="disarm-close" then require(read(path "normal")=incoming) "uncertain disarm unlinked published output"
 end;
 require(read(path "basis")=original && read(path "source")=incoming) "source/basis changed";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 require(HelperSupervisor.usage runtime.supervisor=(0,0)) "workers/helpers still active";
 Printf.printf "PASS bound receiver-unit owned publication %s; native/outer/FD retention and source preservation\n%!" phase
