open Lwt
let mode = ref "pass"
let active = ref 0
let peak = ref 0
let nested = Array.length Sys.argv > 1 && Sys.argv.(1)="nested"
module Recognition = struct
  let format = "test/tree-settlement-v0"
  let identify file = if SemanticFile.size file >= 4L && SemanticFile.read file 0L 4="TOY0"
    then FormatRecognition.Recognized else FormatRecognition.Not_matched
end
module Validator = struct
  let recognition = FormatRecognition.trusted ~suffixes:[".toy"] (module Recognition)
  let select () =
    let selected = !mode in
    Some (fun (context:CandidateValidator.context) ->
      HelperSupervisor.with_cpu_permits context.supervisor ~weight:(if nested then 2 else 1) context.cancellation (fun () ->
        assert (not nested || fst (HelperSupervisor.usage context.supervisor)=2);
        incr active; peak := max !peak !active;
        if selected="cancel" then Abort.all ();
        Lwt.try_bind (fun () -> Lwt_unix.sleep 0.05)
          (fun () -> decr active;
            if selected="pass" then return () else fail (Util.Transient "private tree finding"))
          (fun error -> decr active; fail error)) >>= function
      | Some () -> return () | None -> fail (Util.Transient "private tree cancelled"))
end
let resources () = if not nested then BackendResources.none else
  BackendResources.make ~backend:"test/nested-tree-v0" ~cpu_lanes:2 ~covered_bytes:0
    ~uncovered_estimate:4194304 ~descriptor_credits:2 ~coverage:BackendResources.Accounting_only
let () = CandidateValidators.register ~resources (module Validator)
let write path data = let c=open_out_bin path in output_string c data;close_out c
let read path = let c=open_in_bin path in let s=really_input_string c (in_channel_length c) in close_in c;s
let main () =
  Prefs.loadStrings ["semanticworkers = 2";"semanticmaxinflight = 1";
    "semanticpayloadbudget = 8";"semanticdescriptorbudget = 64";
    "validationtreememory = 1";"log = false"];
  Features.setEnabled (Features.all ()); Case.init false false; Props.init false;
  let cwd=Sys.getcwd () in let album=Filename.concat cwd "album" in Unix.mkdir album 0o700;
  let data="TOY0" ^ String.make 8192 'p' in
  let files=List.init 3 (fun n -> Filename.concat album (Printf.sprintf "item-%d.toy" n)) in
  List.iter (fun path -> write path data) files;
  let directory=Fspath.canonize (Some cwd) and candidate=Path.fromString "album" in
  let runtime=SemanticRuntime.get () in
  let missing = Path.fromString "absent-staging" in
  (try
    Lwt_unix.run (CandidateValidation.before_commit ~directory ~candidate:missing
      ~destination:(Path.fromString "destination"));
    failwith "DESIGNATED absent staging unexpectedly validated"
  with Util.Transient _ -> ());
  let usage = SemanticRuntime.admission_usage () in
  assert (usage.transactions=0 && usage.pending=0 && usage.payload_bytes=0 && usage.descriptors=0);
  assert (HelperSupervisor.usage runtime.supervisor=(0,0) && !active=0);
  print_endline "PASS missing staging: transient failure before admission";
  List.iter (fun selected ->
    Abort.reset ();mode:=selected;peak:=0;
    let diagnostic = ref "" in
    let succeeded = try Lwt_unix.run (CandidateValidation.before_commit ~directory
      ~candidate ~destination:(Path.fromString "destination"));true
      with Util.Transient reason -> diagnostic := reason;false in
    if nested && selected="pass" && not succeeded &&
      !diagnostic="semantic reservation exceeds the configured resource budget" then
      failwith "DESIGNATED nested CPU backend workspace overreserved";
    assert (succeeded=(selected="pass"));
    Abort.reset ();
    let a=SemanticRuntime.admission_usage () and i=IoAdmission.usage runtime.io
    and w=SemanticWorkers.usage runtime.pool in
    assert (a.transactions=0 && a.pending=0 && a.payload_bytes=0 && a.descriptors=0);
    assert (w.pending=0 && w.running=0 && i.active_jobs=0 && i.pending=0);
    assert (HelperSupervisor.usage runtime.supervisor=(0,0) && !active=0);
    if selected="pass" then assert (!peak=(if nested then 1 else 2));
    List.iter (fun path -> assert (read path=data)) files;
    Printf.printf "PASS tree %s: credits/CPU/IO settled, peak=%d, originals exact\n%!" selected !peak)
    ["pass";"reject";"cancel";"pass"];
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool)
let () = main ()
