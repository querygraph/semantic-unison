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
 let storage=Filename.concat state "uncertain-parent" in Unix.mkdir storage 0o700;
 let owner=DngComponents.open_cache_parent storage in
 let descriptor=DngComponents.cache_parent_descriptor owner in
 Unix.close descriptor;
 let uncertain=try DngComponents.settle_cache_parent owner None;failwith "expected uncertain close"
  with DngComponents.Cache_ownership_uncertain _ as error -> error in
 let path=Filename.concat state "tiny-input" in
 let out=open_out_bin path in output_string out "original";close_out out;
 let before=SemanticRuntime.admission_usage () in
 let cancellation=ref None in
 let pending=SemanticRemote.observe_components_with_worker
  ~local_worker:(fun ~pool:_ ~cancellation:cancel ~decoders:_ ~max_read_bytes:_ _ ->
   cancellation:=Some cancel;Lwt.fail uncertain)
  ~root:(Common.Local,left) ~path:(Fspath.resolve_existing path) in
 Lwt_unix.run(Lwt_unix.sleep 0.01);
 require(Lwt.poll pending=None) "uncertain report escaped admission";
 let held=SemanticRuntime.admission_usage () in
 require(held.transactions=before.transactions+1 && held.descriptors>before.descriptors &&
  held.payload_bytes>before.payload_bytes) "uncertainty released outer resource credits";
 require(List.length(SemanticRemote.component_retained_ownership())=1) "uncertainty carrier lost";
 (match !cancellation with Some cancel -> HelperSupervisor.cancel cancel
  | None -> failwith "local worker not entered");
 Lwt_unix.run(Lwt_unix.sleep 0.01);
 let after=SemanticRuntime.admission_usage () in
 require(Lwt.poll pending=None && after.transactions=held.transactions &&
  after.descriptors=held.descriptors && after.payload_bytes=held.payload_bytes)
  "cancellation retired unknown report admission";
 require(Update.component_owner_reference left=None) "uncertain report advanced archive hint";
 (* This disposable process intentionally retains the application reservation
    until exit. OS child/group closure is checked externally, not called native
    close settlement. The stale uncertain numeric FD is never retried. *)
 Lwt_unix.run(SemanticWorkers.shutdown (SemanticRuntime.get()).pool);
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS retained component report admission; actual uncertain close, cancel retains, no head change\n%!"
