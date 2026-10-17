let put bytes little at width value =
  for j=0 to width-1 do
    Bytes.set bytes (at+(if little then j else width-1-j))
      (Char.chr ((value lsr (8*j)) land 255))
  done
let fixture little big packet =
  let bytes=Bytes.make 8192 '\085' in
  let n at width value=put bytes little at width value in
  Bytes.blit_string (if little then "II" else "MM") 0 bytes 0 2;
  let primary,cw,ew,iw,va = if big then begin
    n 2 2 43;n 4 2 8;n 6 2 0;n 8 8 16;16,8,20,8,12
  end else (n 2 2 42;n 4 4 8;8,2,12,4,8) in
  n primary cw 6;
  let entry i tag typ count value =
    let at=primary+cw+ew*i in
    n at 2 tag;n (at+2) 2 typ;n (at+4) iw count;
    for j=0 to iw-1 do Bytes.set bytes (at+va+j) '\000' done;
    let bytes_count=count*(if typ=1 then 1 else 4) in
    n (at+va) (if bytes_count<=iw then bytes_count else iw) value in
  entry 0 50706 1 4 0;
  Bytes.blit_string "\001\004\000\000" 0 bytes (primary+cw+va) 4;
  entry 1 700 1 64 1024;
  entry 2 273 4 1 2048;
  entry 3 279 4 1 512;
  entry 4 50740 1 128 3072;
  (* Scalar-shaped unknown IFD pointer: do not infer pointer independence. *)
  entry 5 65000 13 1 1024;
  n (primary+cw+ew*6) iw 0;
  Bytes.blit_string packet 0 bytes 1024 64;
  n 3072 4 1024;
  Bytes.to_string bytes
(* Original tiny source fixture; production archive transaction and managed store. *)
let require yes why=if not yes then failwith why
let ()=
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 let state=Filename.concat folder "state" in
 require(Util.unisonDir=state) "private state required";
 Prefs.loadStrings ["componentcacheparent = "^Filename.concat state "managed";"componentownercache = true";"adobevalidate = off";
  "semanticdng = false";"semanticworkers = 2";"log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 Globals.setRawRoots [Filename.concat folder "left";Filename.concat folder "right"];
 Lwt_unix.run(Globals.installRoots None);Update.storeRootsName ();
 Lwt_unix.run(Globals.propagatePrefs ());
 let left=snd(fst(Globals.roots ())) in
 ignore(Update.findUpdates ~wantWatcher:false None);
 let storage=Filename.concat state "managed" in
 Unix.mkdir storage 0o700;
 let parent=Unix.openfile storage [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let budget=HelperSupervisor.create ~cpu_permits:2 ~max_children:2 ~max_pending:16 in
 let pool=SemanticWorkers.create ~workers:2 ~max_pending:16 ~budget in
 let decoders=match DngComponents.freeze_decoders [] with Ok x->x|Error e->failwith e in
 let bytes=fixture true false (String.make 64 'X') in
 let inspect name =
  let source=Filename.concat state name in
  let out=open_out_bin source in output_string out bytes;close_out out;
  let fd=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let result=Lwt_unix.run(Update.inspect_cached_components ~index_max_entries:1 left
   ~parent ~path:(Fspath.resolve_existing source)
   ~generation_sha256:(SemanticHash.string "capacity-generation") ~pool
   ~cancellation:(HelperSupervisor.cancellation()) ~decoders ~max_read_bytes:8192L fd) in
  Unix.close fd;
  match result with
  | Some {SemanticWorkers.components=Ok summary;_} ->
    require(summary.full_sha256=SemanticHash.string bytes) "report hash changed"; summary
  | _ -> failwith "valid report lost at capacity"
 in
 let summary=inspect "first.dng" in
 let checkpoint=Option.get summary.checkpoint in
 let entry path=DngComponents.make_owner_entry ~root_identity:"capacity-unit" ~path
  ~generation_sha256:(SemanticHash.string "unit") ~checkpoint ~outcomes:summary.refinements in
 let a=entry "a" and b=entry "b" in
 let index=DngComponents.empty_owner_index ~max_entries:1 ~max_bytes:524288 in
 let full=match DngComponents.replace_owner_entry index ~expected_entry_sha256:None a with
  | Ok x->x|Error e->failwith e in
 require(DngComponents.owner_index_has_capacity_for full a) "same-key replacement rejected at count limit";
 require(not(DngComponents.owner_index_has_capacity_for full b)) "new key admitted at count limit";
 let tiny=DngComponents.empty_owner_index ~max_entries:1 ~max_bytes:80 in
 require(not(DngComponents.owner_index_has_capacity_for tiny a)) "oversized entry admitted";
 let head=Update.component_owner_reference left in
 require(head<>None) "first report not captured";
 let snapshot () =
  let directory=Filename.concat storage "component-cache-v0" in
  Array.to_list(Sys.readdir directory)|>List.sort compare|>List.map(fun name->
   name,Unix.LargeFile.lstat(Filename.concat directory name)) in
 let before=snapshot() in
 ignore(inspect "second.dng");
 require(Update.component_owner_reference left=head) "capacity advanced head";
 require(snapshot()=before) "capacity created cache files or reservation";
 Lwt_unix.run(SemanticWorkers.shutdown pool);
 require(HelperSupervisor.usage budget=(0,0)) "capacity worker budget retained";
 Unix.close parent;
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS valid report preserved at owner-index capacity\n%!"
