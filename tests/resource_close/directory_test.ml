open Lwt
let require yes why=if not yes then failwith why
module Recognition = struct
 let format="test/directory-owner-v0"
 let identify file=if SemanticFile.size file>=4L && SemanticFile.read file 0L 4="TOY0"
  then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
 let recognition=FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
 let select ()=Some(fun (_:CandidateValidator.context)->return ())
end
let ()=CandidateValidators.register (module Validator)
let () =
 let mode=Sys.argv.(1) in
 let legacy=mode="legacy-close" in
 Prefs.loadStrings ["semanticworkers = 1";"semanticmaxinflight = 4";
  "semanticpayloadbudget = 64";"semanticdescriptorbudget = 64";
  ("validationtreememory = "^(if legacy then "0" else "1"));"log = false"];
 Features.setEnabled(Features.all());Case.init false false;Props.init false;
 let initial=Array.length(Sys.readdir "/dev/fd") in
 Unix.mkdir "album" 0o700;
 let content="TOY0"^String.make 128 'p' in
 let channel=open_out_bin "album/file.toy" in output_string channel content;close_out channel;
 let identity=Unix.LargeFile.stat "album/file.toy" in
 let directory=Fspath.canonize(Some(Sys.getcwd())) in
 DirectoryFault.target_path:=System.extendedPath(Fspath.toString(Fspath.concat directory (Path.fromString "album")));
 let runtime=SemanticRuntime.get () in
 DirectoryFault.mode:=mode;DirectoryFault.cancel:=(fun ()->Abort.all());DirectoryFault.armed:=true;
 let result=try CandidateValidation.before_commit ~directory ~candidate:(Path.fromString "album")
  ~destination:(Path.fromString "destination") with error -> fail error in
 let rec await n =
  let ready=try Lwt.poll result<>None with _->true in
  if ready || DirectoryOwner.retained_count()>0 then return ()
  else if n=0 then fail(Failure "directory test deadline")
  else Lwt.bind(Lwt_unix.sleep 0.005)(fun()->await(n-1)) in
 Lwt_unix.run(await 1000);
 let unknown=List.mem mode ["close-before";"close-after";"read-before";"read-after";"cancel-before";"publish-after";"legacy-close"] in
 if unknown then begin
  let sleeping=try Lwt.poll result=None with _->false in
  require sleeping "DESIGNATED directory uncertainty escaped borrowed tree";
  let usage=SemanticRuntime.admission_usage () in
  require(usage.transactions=(if legacy then 0 else 1)) "uncertain directory released admission";
  require(DirectoryOwner.retained_count()=1 && !(DirectoryFault.closes)=1) "opaque close evidence lost/retried";
  let retained=ref None in DirectoryOwner.iter_retained(fun owner->retained:=Some owner);
  let owner=match !retained with Some owner->owner | None->failwith "missing directory owner" in
  require(DirectoryOwner.phase owner=DirectoryOwner.Close_uncertain && DirectoryOwner.path owner= !(DirectoryFault.target_path)) "opaque owner identity/path lost";
  require(Option.is_some(DirectoryOwner.close_cause owner)) "opaque close failure lost";
  let expected_original=List.mem mode ["read-before";"read-after";"publish-after"] in
  if expected_original then require(DirectoryOwner.operation_cause owner=Some DirectoryFault.Original_error) "original callback failure lost";
  if mode="cancel-before" then require(Option.is_some(DirectoryOwner.operation_cause owner)) "cancellation cause lost";
  for _=1 to 3 do (try DirectoryOwner.close owner with DirectoryOwner.Uncertain other->require(other==owner) "changed opaque owner") done;
  Abort.all();Gc.full_major();
  require(!(DirectoryFault.closes)=1 && (try Lwt.poll result=None with _->false)) "repeated close/cancel released/retried directory";
  (match !(DirectoryFault.target) with Some handle when List.mem mode ["close-before";"read-before";"cancel-before";"legacy-close"] ->
    require(DirectoryFault.readable handle) "preclose failure lost actual live handle" | _->());
  List.iter(fun handle->require(DirectoryFault.readable handle) "cleanup closed replacement directory") !(DirectoryFault.replacements)
 end else begin
  if mode="known" then require(Lwt.poll result=Some ()) "known tree changed"
  else begin
   let failed=try ignore(Lwt.poll result);false with
    | DirectoryFault.Original_error -> List.mem mode ["wrapper";"publish";"read-error"]
    | Util.Transient _ -> mode="cancel" || mode="open-error" in
   require failed "known tree failure changed"
  end;
  let expected_closes=if mode="known" then 2 else if mode="wrapper" || mode="open-error" then 0 else 1 in
  require(!(DirectoryFault.closes)=expected_closes && DirectoryOwner.retained_count()=0) "known directory close multiplicity";
  require((SemanticRuntime.admission_usage()).transactions=0) "known tree admission leaked";
  DirectoryFault.armed:=false;Abort.reset();
  let owner=DirectoryOwner.prepare () in
  (try ignore(DirectoryOwner.read owner);failwith "empty placeholder interpreted" with Invalid_argument _->());
  DirectoryOwner.close owner;
  DirectoryOwner.open_with owner "album" (fun ()->());DirectoryOwner.close owner;DirectoryOwner.close owner;
  (try DirectoryOwner.open_with owner "album" (fun ()->());failwith "directory owner reset" with Invalid_argument _->());
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
  require(Array.length(Sys.readdir "/dev/fd")=initial) "known directory descriptors leaked"
 end;
 Abort.reset();
 let now=Unix.LargeFile.stat "album/file.toy" in
 require({now with Unix.LargeFile.st_atime=identity.st_atime}=identity) "synthetic source identity changed";
 let channel=open_in_bin "album/file.toy" in let bytes=really_input_string channel (in_channel_length channel) in close_in channel;
 require(bytes=content) "synthetic source bytes changed";
 Printf.printf "PASS actual validation directory %s; unknowns settle at process exit only\n%!" mode
