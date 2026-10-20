open Lwt
module H=HelperSupervisor
module W=SemanticWorkers
let check condition reason=if not condition then failwith reason
let bytes path=let input=open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in input)
    (fun () -> really_input_string input (in_channel_length input))
let () =
  let data=String.init 131111 (fun i -> Char.chr ((i*73+17) land 255)) in
  let out=open_out_bin "source" in output_string out data;close_out out;
  let source=Unix.openfile "source" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let budget=H.create ~cpu_permits:2 ~max_children:2 ~max_pending:16 in
  let io=IoAdmission.create ~per_device:1 ~max_pending:16 in
  let pool=W.create_with_io ~io ~workers:2 ~max_pending:16 ~budget in
  let observed=ref [] in
  W.set_read_observer pool (Some (fun _ stats -> observed:=stats:: !observed));
  let next=ref 0 in
  let stage () = incr next;let path="stage-"^string_of_int !next in
    path,Unix.openfile path [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  for _=1 to 3 do
    let path,output=stage () in
    let result=Lwt_unix.run (W.snapshot pool (H.cancellation ())
      ~max_bytes:131111L ~source ~output) in
    Unix.close output;
    (match result with None -> failwith "snapshot unexpectedly cancelled"
     | Some report ->
       check (report.ValidationSnapshot.bytes=131111L && report.sha256=SemanticHash.hex (SemanticHash.string data))
         "worker snapshot result digest";
       Printf.printf "snapshot bytes=%Ld native=%b logical-written=%Ld\n%!"
         report.bytes report.native_clone report.logical_bytes_written);
    check (bytes path=data && bytes "source"=data) "worker snapshot source/output exact";
    Sys.remove path
  done;
  let path,output=stage () in
  let failed=try ignore (Lwt_unix.run (W.snapshot pool (H.cancellation ()) ~max_bytes:1L ~source ~output));false
    with W.Failed _ -> true in
  check (failed && bytes path="") "worker budget refusal";
  Unix.close output;Sys.remove path;
  check (!observed=[]) "snapshot emitted outer-reader zero accounting";
  ignore (Lwt_unix.run (W.digest pool (H.cancellation ()) source));
  check (match !observed with [stats] -> stats.SemanticFile.logical_bytes=131111L | _ -> false)
    "ordinary digest read observer changed";
  let module Header = struct
    let format="test/bounded-header-recognition"
    let identify file=ignore (SemanticFile.read file 0L 4);FormatRecognition.Recognized
  end in
  let recognizers=[FormatRecognition.trusted (module Header),false] in
  observed:=[];
  let selected=Lwt_unix.run (W.recognize pool (H.cancellation ()) ~recognizers source) in
  check (match selected with Some value -> value.W.formats=[Header.format] | None -> false)
    "bounded recognition lost match";
  check (match !observed with [stats] -> stats.SemanticFile.logical_bytes=4L | _ -> false)
    "recognition unexpectedly performed full hash";
  observed:=[];
  let identified=Lwt_unix.run (W.identify pool (H.cancellation ()) ~recognizers source) in
  check (match identified with Some {W.fingerprint=Some _;_} -> true | _ -> false)
    "existing identify stopped fingerprinting";
  check (match !observed with [stats] -> stats.SemanticFile.logical_bytes=131115L | _ -> false)
    "existing identify read scope changed";
  let alias=try ignore (Lwt_unix.run (W.snapshot pool (H.cancellation ())
      ~max_bytes:131111L ~source ~output:source));false with W.Failed _ -> true in
  check (alias && bytes "source"=data) "worker alias refusal";
  let path,output=stage () in
  let cancellation=H.cancellation () in
  let queued=Lwt_unix.run (H.with_cpu_permits budget ~weight:2 (H.cancellation ()) (fun () ->
    let job=W.snapshot pool cancellation ~max_bytes:131111L ~source ~output in
    H.cancel cancellation;job)) in
  check (queued=Some None && bytes path="") "CPU-queued snapshot cancellation";
  Unix.close output;Sys.remove path;
  Lwt_unix.run (W.shutdown pool);Unix.close source;
  check (H.usage budget=(0,0)) "snapshot CPU ledger leak";
  check ((W.usage pool).pending=0 && (W.usage pool).running=0) "snapshot worker ledger leak";
  check ((IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).pending=0)
    "snapshot IO ledger leak";
  check (bytes "source"=data) "snapshot final source changed";
  print_endline "PASS actual snapshot workers: exact3/budget/alias/queued-cancel/settled"
