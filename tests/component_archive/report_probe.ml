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
 let source=Filename.concat state "fixture.dng" in
 if phase="write" then begin
  Unix.mkdir storage 0o700;
  let out=open_out_bin source in output_string out (fixture true false (String.make 64 'X'));close_out out
 end;
 let parent=Unix.openfile storage [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let fd=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let budget=HelperSupervisor.create ~cpu_permits:2 ~max_children:2 ~max_pending:16 in
 let pool=SemanticWorkers.create ~workers:2 ~max_pending:16 ~budget in
 let decoders=match DngComponents.freeze_decoders [] with Ok x->x|Error e->failwith e in
 let inspect ()=match Lwt_unix.run(Update.inspect_configured_components left (Fspath.resolve_existing source)
  ~pool ~cancellation:(HelperSupervisor.cancellation()) ~decoders ~max_read_bytes:8192L fd) with
 | Some {SemanticWorkers.components=Ok summary;_}->summary
 | _->failwith "cached report failed" in
 let cancelled=HelperSupervisor.cancellation() in HelperSupervisor.cancel cancelled;
 require(Lwt_unix.run(Update.inspect_cached_components left ~parent:Unix.stdin
  ~path:(Fspath.resolve_existing source) ~generation_sha256:(SemanticHash.string "fixture-generation")
  ~pool ~cancellation:cancelled ~decoders ~max_read_bytes:8192L fd)=None)
  "pre-cancelled report touched invalid cache parent";
 let first=inspect () in
 require(first.full_sha256=SemanticHash.string(fixture true false (String.make 64 'X')))
  "report full hash differs";
 let head=Update.component_owner_reference left in
 require(head<>None && Update.component_owner_namespace left<>None) "report capture not adopted";
 let second=inspect () in
 require(second.full_sha256=first.full_sha256) "repeat report changed hash";
 require(Update.component_owner_reference left=head) "unchanged report republished manifest";
 let absolute=Fspath.resolve_existing source in
 let observed=Lwt_unix.run(SemanticRemote.observe_components_with_worker
  ~local_worker:(Update.inspect_configured_components left absolute)
  ~root:(Common.Local,left) ~path:absolute) in
 require((match observed.SemanticRemote.component_observation with
  | Ok value -> value.SemanticReport.full_sha256=first.full_sha256 | Error _ -> false))
  "local component report entry failed";
 Lwt_unix.run(SemanticWorkers.shutdown (SemanticRuntime.get()).pool);
 require(Update.component_owner_reference left=head) "UI entry republished unchanged capture";
 let request cancellation=Update.inspect_configured_components left (Fspath.resolve_existing source)
  ~pool ~cancellation ~decoders ~max_read_bytes:8192L fd in
 let late=HelperSupervisor.cancellation() in
 let pending=request late in HelperSupervisor.cancel late;
 require(Lwt_unix.run pending=None) "cancelled submitted report reported success";
 require(Update.component_owner_reference left=head) "cancelled report advanced head";
 if phase="read" then begin
  let pending=request(HelperSupervisor.cancellation()) in
  Update.clear_component_owner_reference left;
  let refused=try ignore(Lwt_unix.run pending);false with Util.Transient _ -> true in
  require refused "changed archive head accepted cached result";
  require(Update.component_owner_reference left=None) "stale report overwrote newer head"
 end;
 Lwt_unix.run(SemanticWorkers.shutdown pool);
 require(HelperSupervisor.usage budget=(0,0)) "report worker budget retained";
 Unix.close fd;Unix.close parent;
 if phase="write" then Update.commitUpdates ();
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS cached report %s; automatic capture/repeat reuse/archive reload\n%!" phase
