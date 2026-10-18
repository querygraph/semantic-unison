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
module S=SemanticSyncForOwner
let require_known fd=ignore(Unix.fstat fd)
let () =
 let folder=Sys.argv.(1) and kind=Sys.argv.(2) and phase=Sys.argv.(3) in
 Prefs.loadStrings ["semanticdng = true";"semanticworkers = 1";"adobevalidate = off";"log = false"];
 Features.setEnabled(Features.all());
 let initial=Array.length(Sys.readdir "/dev/fd") in
 let runtime=SemanticRuntime.get () in
 let path name=Filename.concat folder name in
 let original=fixture () and incoming=fixture ~xmp:"<x>two</x>      " () in
 write(path "basis") original;write(path "source") incoming;
 let directory=Fspath.canonize(Some folder) in
 LocalOwnerFault.mode:=phase;LocalOwnerFault.native_mode 0;
 let callbacks=ref 0 in
 let producer fd =
  incr callbacks;require_known fd;require(read(path "normal")=incoming) "producer bytes changed";
  if phase="callback" || phase="callback-close" then raise LocalOwnerFault.Original_error;
  if phase="borrowed-unknown" then begin
   let owner=NotificationPipe.prepare () in
   let nested=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
   NotificationPipe.adopt_read owner nested;
   LocalOwnerFault.nested_fd:=nested;LocalOwnerFault.nested_seen:=true;
   NotificationPipe.close_all owner
  end;
  if phase="callback-cancel" then begin
   Remote.clientCloseRootConnection(Common.Local,directory);
   require_known fd;
   require(!(LocalOwnerFault.read_calls)=0 && !(LocalOwnerFault.write_calls)=0 && !(LocalOwnerFault.source_calls)=0) "active producer descriptors closed"
  end in
 let before=SemanticRuntime.admission_usage () in
 let pending=if kind="bound" then S.try_local_async_with_producer ~producer
   ~source:(Fspath.resolve_existing(path "source")) ~basis:(Fspath.resolve_existing(path "basis")) ~directory ~staging:(Path.fromString "normal")
  else S.try_local_async ~source:(Fspath.resolve_existing(path "source"))
   ~basis:(Fspath.resolve_existing(path "basis")) ~directory ~staging:(Path.fromString "normal") in
 let ready ()=(try Lwt.poll pending<>None with _->true) || S.retained_publications()<>[] in
 let rec await n=if ready () then Lwt.return () else if n=0 then Lwt.fail(Failure "local owner deadline")
  else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
 Lwt_unix.run(await 1000);
 let unknown=List.mem phase ["read";"write";"source";"all";"before-read";"before-source";"register-close";"open-source-close";"callback-close";"interrupt-pair";"interrupt-source";"parent-before";"parent-after";"preentry";"borrowed-unknown"] in
 if unknown then begin
  require((try Lwt.poll pending=None with _->false)) "DESIGNATED local descriptor uncertainty escaped";
  require((SemanticRuntime.admission_usage()).transactions=before.transactions+1) "local admission released";
  let scope=match S.retained_publications() with [x]->x|_->failwith "retained local scope missing" in
  let pair=match S.retained_publication_pair_ownership scope with Some p->p|_->failwith "pair ledger missing" in
  let source=match S.retained_publication_source_ownership scope with Some p->p|_->failwith "source ledger missing" in
  if phase="interrupt-pair" || phase="interrupt-source" || phase="preentry" || phase="borrowed-unknown" then begin
   let known=S.retained_publication_descriptors scope in
   let expected=if phase="interrupt-source" || phase="borrowed-unknown" then 3 else if kind="bound" then 3 else 2 in
   require(List.length known=expected) "interrupted descriptor inventory lost";
   List.iter require_known known;
   require(!(LocalOwnerFault.read_calls)=0 && !(LocalOwnerFault.write_calls)=0 && !(LocalOwnerFault.source_calls)=0) "interrupted handles closed";
   if phase="borrowed-unknown" then require(!(LocalOwnerFault.nested_calls)=1) "nested close retry";
   if phase="preentry" then begin
    require(LocalOwnerFault.native_closes ()= !(LocalOwnerFault.before_native_count)) "preentry native cleanup retried";
    let parent=match S.retained_publication_parent_ownership scope with Some p->p|_->failwith "parent ledger missing" in
    require(not(NotificationPipe.read_transferred parent)) "unconsumed parent claimed transferred"
   end
  end else begin
   if List.mem phase ["read";"all";"before-read";"register-close";"open-source-close";"callback-close"] then
    require(Option.is_some(NotificationPipe.read_cause pair)) "pair read cause lost";
   if List.mem phase ["write";"all";"register-close";"open-source-close";"callback-close"] then
    require(Option.is_some(NotificationPipe.write_cause pair)) "pair write cause lost";
   if List.mem phase ["source";"all";"before-source";"callback-close"] then
    require(Option.is_some(NotificationPipe.read_cause source)) "source close cause lost";
   if phase="parent-before" || phase="parent-after" then begin
    let parent=match S.retained_publication_parent_ownership scope with Some p->p|_->failwith "parent cause missing" in
    require(Option.is_some(NotificationPipe.read_cause parent) && !(LocalOwnerFault.parent_calls)=1 && LocalOwnerFault.parent_closes()=0) "parent close ownership lost"
   end;
   if List.mem phase ["callback-close";"register-close";"open-source-close";"parent-before";"parent-after"] then
    require(S.retained_publication_cause scope==LocalOwnerFault.Original_error) "original local failure lost"
  end;
  let stage=Array.to_list(Sys.readdir folder)|>List.filter(fun n->n<>"basis" && n<>"source") in
  let stage=match stage with [x]->path x|_->failwith "uncertain local stage missing" in
  let bytes=read stage and closes=(!(LocalOwnerFault.read_calls),!(LocalOwnerFault.write_calls),!(LocalOwnerFault.source_calls),!(LocalOwnerFault.parent_calls),LocalOwnerFault.native_closes()) in
  Remote.clientCloseRootConnection(Common.Local,directory);Lwt_unix.run(Lwt_unix.sleep 0.01);Gc.full_major();
  require(read stage=bytes && (try Lwt.poll pending=None with _->false)) "connection cleanup unlinked/released local stage";
  require(closes=(!(LocalOwnerFault.read_calls),!(LocalOwnerFault.write_calls),!(LocalOwnerFault.source_calls),!(LocalOwnerFault.parent_calls),LocalOwnerFault.native_closes())) "connection cleanup retried local close";
  List.iter require_known !(LocalOwnerFault.recycled);List.iter require_known !(LocalOwnerFault.unclosed);
  if phase="borrowed-unknown" then require(!(LocalOwnerFault.nested_calls)=1) "nested cleanup retried"
 end else begin
  if phase="known" then require(Lwt.poll pending=Some true && read(path "normal")=incoming) "known local output changed"
  else begin
   let expected=try ignore(Lwt.poll pending);false with
    | LocalOwnerFault.Original_error -> List.mem phase ["prepare";"register";"open-source";"callback";"before-native";"after-native"]
    | Util.Transient _ -> phase="callback-cancel" in
   require expected "known local failure changed"
  end;
  require((SemanticRuntime.admission_usage()).transactions=before.transactions) "known local admission leaked";
  require(S.retained_publications()=[]) "known local case retained";
  (match !(LocalOwnerFault.handoff) with Some h->require(StagePublication.parent_consumed h=(phase<>"before-native")) "native parent acknowledgement changed" | None->());
  if kind="bound" && phase="callback-cancel" then require(!callbacks=1 && not(Sys.file_exists(path "normal"))) "producer interruption cleanup/name mismatch"
 end;
 require(read(path "basis")=original && read(path "source")=incoming) "source/basis changed";
 Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
 if not unknown then require(Array.length(Sys.readdir "/dev/fd")=initial) "known local descriptors leaked";
 Printf.printf "PASS actual local owner %s %s; uncertain resources settle at process exit only\n%!" kind phase
