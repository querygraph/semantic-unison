(* Each case runs in its own bounded subprocess with only disposable paths.
   Shared fixture helpers come from semantic/test.ml. *)
let contains value fragment =
  let rec scan i = i + String.length fragment <= String.length value &&
    (String.sub value i (String.length fragment) = fragment || scan (i+1)) in scan 0
let reject f =
  let rejected = try f (); false with
    | Util.Transient why | SemanticWorkers.Failed why | SemanticFile.Invalid why ->
      require (contains why "not a regular file") ("unexpected rejection: " ^ why); true in
  require rejected "FIFO input was accepted"
let descriptors () = Array.length (Sys.readdir "/dev/fd")
let () =
  let directory = Fspath.canonize (Some (Sys.getcwd ())) in
  let absolute name = Fspath.concat directory (Path.fromString name) in
  let string_path name = Fspath.toString (absolute name) in
  Prefs.loadStrings ["semanticdng = true";"semanticworkers = 2";"adobevalidate = require"];
  Features.setEnabled (Features.all ());
  write "basis" (fixture ());
  write "source" (fixture ~xmp:"<x>two</x>      " ());
  Unix.mkfifo "fifo" 0o600;
  let runtime = SemanticRuntime.get () in
  let inspect path = CandidateValidationForTest.snapshot runtime.pool
    (HelperSupervisor.cancellation ()) (string_path path) in
  ignore (Lwt_unix.run (inspect "basis"));
  let before = descriptors () in
  let usage () =
    let credits = SemanticAdmission.usage runtime.admission in
    require (credits.transactions=0 && credits.pending=0 && credits.payload_bytes=0 && credits.descriptors=0)
      "FIFO rejection retained transaction resource credits";
    require (HelperSupervisor.usage runtime.supervisor=(0,0)) "FIFO rejection retained CPU permits";
    require ((SemanticWorkers.usage runtime.pool).pending=0) "FIFO rejection left an active job" in
  let staging = Path.fromString "output" in
  let local source = SemanticSyncForTest.try_local ~source:(absolute source)
    ~basis:(absolute "basis") ~directory ~staging in
  let async source = SemanticSyncForTest.try_local_async ~source:(absolute source)
    ~basis:(absolute "basis") ~directory ~staging in
  let plan source =
    let base = proof "basis" in
    let request = SemanticDelta.encode_request ~nonce:(String.make 32 'f') base in
    SemanticRuntime.with_transaction ~role:SemanticAdmission.Source ~max_payload:1048576
      (fun _ -> SemanticPlanForTest.make_plan () (string_path source,request)) in
  let started = Unix.gettimeofday () in
  begin match Sys.argv.(1) with
  | "sync" -> reject (fun () -> ignore (local "fifo"));
      usage (); require (descriptors ()=before) "synchronous open leaked fd";
      require (local "source") "synchronous follow-up declined"
  | "async" -> reject (fun () -> ignore (Lwt_unix.run (async "fifo")));
      usage (); require (descriptors ()=before) "asynchronous open leaked fd";
      require (Lwt_unix.run (async "source")) "asynchronous follow-up declined"
  | "plan" -> reject (fun () -> ignore (Lwt_unix.run (plan "fifo")));
      usage (); require (descriptors ()=before) "source planning leaked fd";
      begin match Lwt_unix.run (plan "source") with
      | None -> failwith "source-planning follow-up declined"
      | Some encoded ->
          let decoded = ok (SemanticDelta.decode encoded) in
          require (SemanticDelta.binds_request ~nonce:(String.make 32 'f') ~base:(proof "basis") decoded)
            "source-planning follow-up returned wrong bytes" end
  | "candidate" -> reject (fun () -> ignore (Lwt_unix.run
      (CandidateValidationForTest.validate_file ~reservation:None
        ~validators:(CandidateValidators.selected ()) ~destination:"fifo.dng" (absolute "fifo"))));
      usage (); require (descriptors ()=before) "candidate hashing leaked fd";
      ignore (Lwt_unix.run (inspect "source"))
  | "tool" ->
      Prefs.loadStrings ["adobevalidator = " ^ string_path "fifo";
        "adobevalidatorhash = " ^ String.make 64 'a';"adobevalidatorbuild = fifo-test-1"];
      reject (fun () -> ignore (Lwt_unix.run
        (CandidateValidationForTest.validate_file ~reservation:None
          ~validators:(CandidateValidators.selected ()) ~destination:"source.dng" (absolute "source"))));
      usage (); require (descriptors ()=before) "tool pin hashing leaked fd";
      ignore (Lwt_unix.run (inspect "source"))
  | _ -> failwith "unknown FIFO open case"
  end;
  require (Unix.gettimeofday () -. started < 5.) "nonblocking FIFO rejection or follow-up stalled";
  usage (); require (descriptors ()=before) "follow-up work leaked fd";
  require (read "basis"=fixture ()) "FIFO rejection changed basis";
  if Sys.file_exists "output" then begin
    require (read "output"=read "source") "follow-up clone produced wrong bytes";
    Sys.remove "output"
  end;
  let names = List.sort String.compare (Array.to_list (Sys.readdir ".")) in
  require (names = ["basis";"fifo";"source";"state"])
    "FIFO rejection leaked a staging name";
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
  Printf.printf "PASS nonblocking %s FIFO rejection, exact follow-up and resource cleanup\n%!" Sys.argv.(1)
