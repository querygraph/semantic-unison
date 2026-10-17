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
external mode : int -> unit = "unison_cache_control_mode"
external closes : unit -> int = "unison_cache_control_closes"
let ()=
 let folder=Sys.argv.(1) and phase=Sys.argv.(2) in
 let state=Filename.concat folder "state" in
 require(Util.unisonDir=state) "private state required";
 Prefs.loadStrings ["componentcacheparent = "^Filename.concat state "managed";"componentownercache = true";"adobevalidate = off";
  "semanticdng = true";"semanticworkers = 2";"log = false"];
 Case.init true Osx.isMacOSX;Props.init false;Osx.init Osx.isMacOSX;Fileinfo.init false;
 Globals.setRawRoots [Filename.concat folder "left";Filename.concat folder "right"];
 Lwt_unix.run(Globals.installRoots None);Update.storeRootsName ();
 Lwt_unix.run(Globals.propagatePrefs ());
 let left=snd(fst(Globals.roots ())) in
 ignore(Update.findUpdates ~wantWatcher:false None);
 let path=Filename.concat state "tiny-source.dng" in
 let out=open_out_bin path in output_string out (fixture true false (String.make 64 'X'));close_out out;
 let extension=List.find(fun x->FormatExtension.profile x=DngLayout.profile)
  (SemanticFormats.local_enabled()) in
 let before=SemanticRuntime.admission_usage () in
 mode (if phase="hold" then 1 else 0);
 let pending=SemanticRemote.observe ~root:(Common.Local,left)
  ~path:(Fspath.resolve_existing path) ~extension in
 if phase="normal" then begin
  let result=Lwt_unix.run pending in
  require((match result.SemanticRemote.observation with SemanticReport.Supported _->true|_->false))
   "normal semantic source report failed";
  let after=SemanticRuntime.admission_usage () in
  require(after.transactions=before.transactions && after.descriptors=before.descriptors)
   "normal source report leaked admission";
  require(closes()=1) "normal source close not exactly once"
 end else begin
  let rec wait count =
   if SemanticRemote.component_retained_ownership()=[] && count>0 then
    Lwt.bind (Lwt_unix.sleep 0.01) (fun ()->wait(count-1)) else Lwt.return () in
  Lwt_unix.run(wait 200);
  require(Lwt.poll pending=None) "uncertain ordinary report escaped admission";
  let held=SemanticRuntime.admission_usage () in
  require(held.transactions=before.transactions+1 && held.descriptors>before.descriptors &&
   held.payload_bytes>before.payload_bytes) "uncertain ordinary source released credits";
  require(closes()=1) "uncertain source close numerically retried";
  let owners=SemanticRemote.component_retained_ownership() in
  require(List.length owners=1) "ordinary source uncertainty carrier lost";
  require(List.length(DngComponents.cache_uncertain_descriptors(List.hd owners))=1)
   "uncertain source identity lost";
  Lwt_unix.run(Lwt_unix.sleep 0.02);
  require(Lwt.poll pending=None && closes()=1) "pending ordinary source retried/released"
 end;
 Lwt_unix.run(SemanticWorkers.shutdown(SemanticRuntime.get()).pool);
 Lwt_unix.run(Update.unlockArchives ());Globals.uninstallRoots ();
 Printf.printf "PASS ordinary semantic source %s; close-once and outer admission ownership\n%!" phase
