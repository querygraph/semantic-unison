open Lwt
let enabled=ref false and calls=ref 0
module Recognition = struct
  let format="test/scanned-scope-fixture"
  let identify file=if SemanticFile.size file>=4L && SemanticFile.read file 0L 4="TOY0"
    then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
  let recognition=FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
  let select ()=if not !enabled then None else Some (fun (context:CandidateValidator.context) ->
    incr calls;
    if not (Util.startswith (Filename.basename (Filename.dirname context.candidate)) "validation-scan-") then
      failwith "scope validator received original path";
    context.inspect context.candidate >>= fun actual ->
    if actual<>context.expected then failwith "scope snapshot differs";
    return ())
end
let ()=CandidateValidators.register (module Validator)
let check yes message=if not yes then failwith message
let write path value=let ch=open_out_bin path in output_string ch value;close_out ch
let () =
  let cwd=Sys.getcwd () in
  let names=["left";"right"] in
  List.iter (fun name ->
    let root=Filename.concat cwd name in Unix.mkdir root 0o700;
    Unix.mkdir (Filename.concat root "nested") 0o700;
    List.iter (fun (path,body) -> write (Filename.concat root path) body)
      ["plain","TOY0 plain";"nested/stable","TOY0 nested";"ignored","TOY0 ignored"];
    write (Filename.concat cwd "external") "TOY0 followed";
    Unix.symlink (Filename.concat cwd "external") (Filename.concat root "link")) names;
  let state=Sys.getenv "UNISON" in
  write (Filename.concat state "scope.prf")
    ("root = "^Filename.concat cwd "left"^"\nroot = "^Filename.concat cwd "right"^
     "\nbatch = true\nlog = false\nfastcheck = true\nignore = Path ignored\nfollow = Path link\n"^
     "semanticworkers = 2\nsemanticmaxinflight = 1\nsemanticpayloadbudget = 8\nsemanticdescriptorbudget = 64\n");
  Uicommon.initPrefs ~profileName:"scope" ~promptForRoots:(fun () -> None) ();
  Uicommon.connectRoots ~displayWaitMessage:(fun () -> ()) ();
  let initial=Update.findUpdates None in
  let left,right=List.hd initial in
  List.iter2 (fun (_,root) (_,ui,_) ->
    Update.replaceArchiveLocal root Path.empty (Update.makeArchive ui)) (Globals.rootsList ()) [left;right];
  Update.commitUpdates ();
  enabled:=true;
  let scan ()=Update.findUpdates ~wantWatcher:true (Some ([],[])) in
  let unchanged result=List.for_all (fun ((_,a,_),(_,b,_)) -> a=Common.NoUpdates && b=Common.NoUpdates) result in
  let quiet ()=
    check (Sys.getcwd ()=cwd) "scope changed process CWD";
    check (not (Array.exists (fun name -> Util.startswith name "validation-scan-") (Sys.readdir state))) "scope left staging directory";
    let runtime=SemanticRuntime.get () in
    check ((SemanticRuntime.admission_usage ()).transactions=0 &&
      (SemanticRuntime.admission_usage ()).pending=0 &&
      (SemanticWorkers.usage runtime.pool).pending=0 &&
      (IoAdmission.usage runtime.io).active_jobs=0 && HelperSupervisor.usage runtime.supervisor=(0,0) &&
      ValidationDescriptor.retained ()=[]) "scope returned before all endpoint resources settled" in
  check (unchanged (scan ()) && !calls=0) "default received/off no-op invoked validator";
  Prefs.loadStrings ["adobevalidate = require";"adobevalidatescope = all-scanned"];
  Features.validateEnabled ();
  let before= !calls in check (unchanged (scan ()) && !calls=before+6) "all-scanned unchanged coverage";quiet ();
  let before= !calls in check (unchanged (scan ()) && !calls=before+6) "all-scanned repeated no-op omitted validation";quiet ();
  Prefs.loadStrings ["adobevalidatescope = received"];
  let before= !calls in check (unchanged (scan ()) && !calls=before) "received no-op invoked validator";quiet ();
  Prefs.loadStrings ["adobevalidate = off";"adobevalidatescope = all-scanned"];
  let before= !calls in check (unchanged (scan ()) && !calls=before) "off all-scanned invoked validator";quiet ();
  Prefs.loadStrings ["adobevalidatescope = typo"];
  let invalid=try ignore (DngCandidateValidation.all_scanned ());false with Util.Fatal _ -> true in
  check invalid "invalid scope accepted";
  Prefs.loadStrings ["adobevalidate = require";"adobevalidatescope = all-scanned"];
  let features=Features.getEnabled () in
  Features.setEnabled (List.filter ((<>) "dng-validation-all-scanned-v1") features);
  let incompatible=try Features.validateEnabled ();false with Util.Fatal _ -> true in
  check incompatible "active scope accepted incapable peer";
  let late=try ignore (DngCandidateValidation.all_scanned ());false with Util.Fatal _ -> true in
  check late "late policy installation bypassed capability check";
  Prefs.loadStrings ["adobevalidate = off"];Features.validateEnabled ();
  check (not (DngCandidateValidation.all_scanned ())) "off unusable without scope capability";
  Features.setEnabled features;
  Prefs.loadStrings ["adobevalidate = require";"adobevalidatescanfiles = 1"];
  let refused=try ignore (scan ());false with Util.Transient _ -> true in
  check refused "scope silently truncated coverage";quiet ();
  Prefs.loadStrings ["adobevalidatescanfiles = 65536";"adobevalidatescanmaxmib = 0"];
  let invalid=try ignore (DngCandidateValidation.scan_limits ());false with Util.Fatal _ -> true in
  check invalid "invalid snapshot limit accepted";
  Prefs.loadStrings ["adobevalidatescanmaxmib = 4096"];
  List.iter (fun name -> write (Filename.concat (Filename.concat cwd name) "unavailable.dng") "TOY0 claimed DNG") names;
  let refused=try ignore (scan ());false with Util.Transient _ -> true in
  check refused "require accepted unavailable SDK";quiet ();
  let warnings=ref [] in Util.warnPrinter:=Some (fun warning -> warnings:=warning:: !warnings);
  Prefs.loadStrings ["adobevalidate = warn"];
  ignore (scan ());check (List.length !warnings=2) "warn did not explicitly report both endpoint findings";quiet ();
  check (List.for_all (fun warning -> Util.findsubstring "unavailable.dng" warning<>None &&
    Util.findsubstring "validation-scan-" warning=None) !warnings) "warning reports private implementation path instead of logical source";
  let driver=Sys.argv.(1) in
  let read path=let ch=open_in_bin path in
    Fun.protect ~finally:(fun () -> close_in ch) (fun () -> really_input_string ch (in_channel_length ch)) in
  write (driver^".control") "pass";
  Prefs.loadStrings ["adobevalidate = require";"adobevalidator = "^driver;
    "adobevalidatorhash = "^SemanticHash.hex (SemanticHash.string (read driver));
    "adobevalidatorbuild = validation-warning-synthetic-1";
    "debug = validation-process";"debug = validation-group"];
  ignore (scan ());quiet ();
  let helper_lines=String.split_on_char '\n' (String.trim (read (driver^".calls"))) in
  check (List.length helper_lines=2) "configured fake driver did not run once on each endpoint";
  List.iter (fun line -> match String.split_on_char '\t' line with
    | [_;"pass";_;_;candidate] ->
        check (Util.startswith (Filename.basename (Filename.dirname candidate)) "validation-scan-" &&
          not (Sys.file_exists candidate)) "fake driver received original or retained a stage"
    | _ -> failwith "malformed original fake driver log") helper_lines;
  Prefs.loadStrings ["adobevalidate = warn";"adobevalidator = "];
  Unix.symlink (Filename.concat cwd "absent-target") (Filename.concat (Filename.concat cwd "left") "dangling");
  Prefs.loadStrings ["follow = Path dangling"];
  let before= !calls in
  let failed=try ignore (scan ());false with Util.Transient _ -> true in
  check failed "incomplete scan claimed validation coverage";
  check (!calls=before+4) "failed endpoint did not drain the other endpoint's actual validators";quiet ();
  Lwt_unix.run (SemanticWorkers.shutdown (SemanticRuntime.get ()).pool);
  print_endline "PASS actual scan-RPC all-scanned/default-received/off/no-op/follow/ignore/peer/limits/require/warn/error-drain controls; zero SDK; two actual original fake driver helpers"
