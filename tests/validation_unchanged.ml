open Lwt
let mode=ref "off" and calls=ref 0 and original=ref ""
module Recognition = struct
  let format="test/unchanged-private-validator"
  let identify file=if SemanticFile.size file>=4L && SemanticFile.read file 0L 4="TOY0"
    then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
  let recognition=FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
  let select ()=if !mode="off" then None else Some (fun (context:CandidateValidator.context) ->
    incr calls;
    if context.candidate= !original then failwith "validator received original";
    context.inspect context.candidate >>= fun snapshot ->
    if snapshot<>context.expected then failwith "private snapshot context differs";
    match !mode with
    | "reject" -> fail (Util.Transient "original fake validator finding")
    | "wrong-path" -> context.inspect !original >>= fun _ -> failwith "borrowed inspection opened original"
    | "wrong-alias" -> context.inspect (!original^".alias") >>= fun _ -> failwith "artifact inspection opened original alias"
    | "artifact" ->
        context.inspect (Filename.concat (Sys.getcwd ()) "driver-artifact") >>= fun actual ->
        if actual.sha256<>SemanticHash.hex (SemanticHash.string "GENERATED ARTIFACT") then failwith "artifact hash differs";
        return ()
    | "borrowed-inspect" ->
        let moved=context.candidate^".held-fixture" in
        Unix.rename context.candidate moved;
        Lwt.try_bind (fun () -> context.inspect context.candidate)
          (fun observed ->
            Unix.rename moved context.candidate;
            if observed.sha256<>context.expected.sha256 || observed.size<>context.expected.size then
              failwith "held output inspection differs";
            return ())
          (fun error -> Unix.rename moved context.candidate;fail error)
    | "execute" ->
        context.execute (fun () ->
          if (IoAdmission.usage (SemanticRuntime.get ()).io).active_jobs<>1 then
            failwith "borrowed output execution missing filesystem admission";
          return {HelperSupervisor.outcome=HelperSupervisor.Failed "original fake callback; no subprocess";
            status=None;child_pid=None;stdout="";stderr="";output_truncated=false;elapsed=0.})
        >>= fun _ -> return ()
    | "mutate" ->
        let output=open_out_bin context.candidate in output_string output "PRIVATE MUTATION";close_out output;return ()
    | _ -> return ())
end
let ()=CandidateValidators.register (module Validator)
let check condition reason=if not condition then failwith reason
let write path data=let output=open_out_bin path in output_string output data;close_out output
let read path=let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let () =
  Prefs.loadStrings ["semanticworkers = 2";"semanticmaxinflight = 1";
    "semanticpayloadbudget = 8";"semanticdescriptorbudget = 64";"log = false";"adobevalidate = off"];
  Features.setEnabled (Features.all ());Case.init false false;Props.init false;
  let root=Sys.getcwd () in
  let source=Filename.concat root "source" and directory=Filename.concat root "private" in
  let source_path=Fspath.canonize (Some source) in
  let staging_path=Fspath.canonize (Some directory) in
  let run max_bytes =CandidateValidation.unchanged_file ~staging_directory:staging_path ~source:source_path
      ~destination:(Path.fromString "actual.bin") ~max_bytes in
  Lwt_unix.run (run 1L);check (!calls=0 && not (Sys.file_exists source) && not (Sys.file_exists directory))
    "off opened inputs or created staging";
  Unix.mkdir directory 0o700;original:=source;mode:="pass";
  let runtime=SemanticRuntime.get () and read_bytes=ref 0L in
  SemanticWorkers.set_read_observer runtime.pool (Some (fun _ stats ->
    read_bytes:=Int64.add !read_bytes stats.SemanticFile.logical_bytes));
  let quiet ()=
    let a=SemanticRuntime.admission_usage () and w=SemanticWorkers.usage runtime.pool
    and i=IoAdmission.usage runtime.io in
    check (a.transactions=0 && a.pending=0 && a.payload_bytes=0 && a.descriptors=0)
      "global admission leak/nested reacquisition";
    check (w.pending=0 && w.running=0 && i.active_jobs=0 && i.pending=0 && HelperSupervisor.usage runtime.supervisor=(0,0))
      "worker/IO/CPU unsettled";
    check (Sys.readdir directory=[||]) "private staging residue" in
  let unrelated="NOT0"^String.make 131107 'p' in write source unrelated;
  Lwt_unix.run (run 1L);quiet ();
  check (!calls=0 && !read_bytes=4L && read source=unrelated)
    "nonmatch hashed/copied/validated or hit snapshot size cap";
  let data="TOY0 ORIGINAL GENERATED CONTENT" in write source data;
  let limited=try Lwt_unix.run (run 1L);false with Util.Transient _ -> true in
  check (limited && !calls=0 && read source=data) "matched size refusal";quiet ();
  write (Filename.concat root "driver-artifact") "GENERATED ARTIFACT";
  List.iter (fun selected ->
    mode:=selected;
    let before= !calls in
    if selected="wrong-alias" then Unix.link source (source^".alias");
    let passed=try Lwt_unix.run (run 1024L);true with Util.Transient _ -> false in
    if selected="wrong-alias" then Unix.unlink (source^".alias");
    check (passed=List.mem selected ["pass";"execute";"borrowed-inspect";"artifact"] && !calls=before+1 && read source=data) "selected private validation result";
    quiet ();
    Printf.printf "PASS unchanged %s original-exact/global-local-admission-settled\n%!" selected)
    ["pass";"reject";"wrong-path";"wrong-alias";"artifact";"borrowed-inspect";"execute";"mutate";"pass"];
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
  print_endline "PASS unchanged off/no-open and bounded nonmatch/size/private-companion controls; zero SDK"
