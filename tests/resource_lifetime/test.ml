(* Real TargetBinding/FinalPublication/Runtime, isolated synthetic native files.
   Counts complete phase-boundary inventories, not hidden native transient peaks. *)
open Lwt
module A = SemanticAdmission
module R = SemanticRuntime
module T = TargetBinding
external fd_count : unit -> int = "resource_fixture_fd_count"
let assertions = ref 0
let check yes reason = incr assertions; if not yes then failwith reason
let run = Lwt_unix.run
let root = Fspath.canonize (Some (Sys.getcwd ()))
let p = Path.fromString
let phase label =
  let u = R.admission_usage () in
  Printf.printf "CENSUS %s fd=%d tx=%d pending=%d reserved=%d buffers=%d\n%!"
    label (fd_count ()) u.A.transactions u.A.pending u.A.descriptors u.A.payload_bytes
let settled base =
  ignore (run (Lwt_unix.yield ()));
  let u = R.admission_usage () in
  check (u.A.transactions=0 && u.A.pending=0 && u.A.descriptors=0 && u.A.payload_bytes=0)
    "resource owner did not retire";
  check (fd_count ()=base) "phase-boundary descriptors did not settle"
let ticket name =
  T.prepare_admitted ~require_producer:true ~logical_root:root ~local_path:(p name)
    ~working_dir:root ~candidate:(p ("." ^ name ^ ".tmp")) ~target:(p name)
    ~normalize:false ~check_apple_double:false ()
let token promise = match run promise with Some token -> token | None -> failwith "native unavailable"
let release token = T.release_ticket ~logical_root:root ~token ()
let produce name token f =
  T.with_producer ~token ~logical_root:root ~local_path:(p name) ~working_dir:root
    ~candidate:(p ("." ^ name ^ ".tmp")) ~target:(p name) f
let commit name token f =
  T.with_binding ~token ~logical_root:root ~local_path:(p name) ~working_dir:root
    ~candidate:(p ("." ^ name ^ ".tmp")) ~target:(p name) f
let write path contents =
  let ch = open_out_bin path in
  Fun.protect ~finally:(fun () -> close_out ch) (fun () -> output_string ch contents)
let read path =
  let ch = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in ch)
    (fun () -> really_input_string ch (in_channel_length ch))
let materialize name binding =
  let candidate = "." ^ name ^ ".tmp" in
  write candidate "new synthetic payload";
  let fd = Unix.openfile candidate [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    FinalPublication.adopt_mutable (T.native binding) ~candidate:fd;
    FinalPublication.freeze_producer (T.native binding);
    T.record_fingerprint binding (Os.fingerprint root (p candidate) `FILE))
let reservation binding = match T.reservation binding with
  | Some owner -> owner | None -> failwith "production owner absent"
let fails predicate f =
  let matched = try ignore (run (f ())); false with e -> predicate e in
  check matched "failure lost or replaced"
let transient = function Util.Transient _ -> true | _ -> false
let marker = function Failure message -> message="marker" | _ -> false
let cases = ref 0
let selected = if Array.length Sys.argv > 1 then Sys.argv.(1) else "baseline"
let test name f =
  let handoff = name = "handoff-sync" || name = "handoff-async" in
  if selected = name || selected = "baseline" && not handoff then begin
    f (); incr cases; Printf.printf "PASS %s\n%!" name
  end
let () =
  Unix.mkdir Util.unisonDir 0o700;
  Prefs.loadStrings ["semanticdng = true"; "rsrc = false"; "semanticworkers = 2";
    "semanticmaxinflight = 2"; "semanticdescriptorbudget = 32"; "semanticpayloadbudget = 17"];
  check (FinalPublication.available ()) "requires macOS native final publication";
  let base = fd_count () in
  test "prepare is admitted before four native handles and keeps a lazy pool" (fun () ->
    let first = token (ticket "first.raw") in
    phase "Ready";
    let u = R.admission_usage () in
    check (u.A.transactions=1 && u.A.descriptors=24 && fd_count ()=base+4)
      "prepared native handles escaped retained admission";
    let second = ticket "second.raw" in
    check (Lwt.poll second=None && fd_count ()=base+4 && (R.admission_usage ()).A.pending=1)
      "queued target opened before admission";
    let source_release = Lwt.wait () in
    let source = R.with_transaction ~role:A.Source ~max_payload:1048576 (fun _ -> source_release) in
    check ((R.admission_usage ()).A.transactions=2 && (R.admission_usage ()).A.descriptors=32)
      "prepared receiver stole peer source headroom";
    release first;
    (* Headroom remains conservatively reserved while a Source is active.
       Its independent callback settles before the next consumer is admitted. *)
    check (Lwt.poll second=None && fd_count ()=base) "source headroom policy changed";
    Lwt.wakeup source_release (); ignore (run source);
    let second = token second in
    check (fd_count ()=base+4 && (R.admission_usage ()).A.descriptors=24)
      "prepared handoff lost capacity or handles";
    release second;
    settled base);
  test "finalized producer keeps five native handles until successful commit" (fun () ->
    let name="commit.raw" in write name "old live bytes";
    let t=token (ticket name) in
    ignore (run (produce name t (fun binding -> materialize name binding; return ())));
    phase "Finalized";
    check (fd_count ()=base+5 && (R.admission_usage ()).A.descriptors=24)
      "owned proof FD outlives lease after producer return";
    ignore (run (commit name t (fun binding ->
      check ((R.admission_usage ()).A.descriptors=24) "commit lost retained owner";
      FinalPublication.observe_target (T.native binding);
      FinalPublication.publish (T.native binding); return ())));
    check (read name="new synthetic payload") "native publication bytes differ";
    release t; settled base);
  test "borrowed validation uses no second slot at the minimum budget" (fun () ->
    let name="validation.raw" in let t=token (ticket name) in
    ignore (run (produce name t (fun binding -> materialize name binding; return ())));
    let entered=ref false and done_=Lwt.wait () in
    let committing=commit name t (fun binding ->
      let owner=reservation binding in
      R.with_cancellation (fun cancel -> R.with_admission ~reservation:owner cancel
        ~payload_bytes:1048576 ~descriptors:9 (fun () ->
          entered:=true;
          let u=R.admission_usage () in
          check (u.A.transactions=1 && u.A.descriptors=24 && u.A.pending=0)
            "inherited validation reacquired consumer gate";
          done_))) in
    check !entered "inherited validation deadlocked under source headroom";
    release t; release t;
    check (fd_count ()=base+5 && (R.admission_usage ()).A.descriptors=24)
      "release closed borrowed validation proof early";
    phase "Committing-release-requested";
    Lwt.wakeup done_ (); fails transient (fun () -> committing);
    check (not (Sys.file_exists ("." ^ name ^ ".tmp"))) "aborted candidate survived";
    settled base);
  test "legacy handoff retains work admission until producer callback settles" (fun () ->
    let name="legacy.raw" in let t=token (ticket name) in
    let done_=Lwt.wait () in
    let running=produce name t (fun binding ->
      T.legacy_handoff binding;
      check (fd_count ()=base && (R.admission_usage ()).A.descriptors=24)
        "legacy handoff released work capacity early";
      let owner=reservation binding in
      A.with_borrow owner ~cost:{A.payload_bytes=1048576;descriptors=8} (fun () -> done_)) in
    phase "Legacy-handoff-borrowed";
    Lwt.wakeup done_ ();
    let _,kind=run running in check (kind=T.Legacy_backend) "legacy completion differs";
    release t; settled base);
  test "sync and async producer errors close proof before retirement" (fun () ->
    List.iteri (fun index f ->
      let name="failure" ^ string_of_int index ^ ".raw" in let t=token (ticket name) in
      fails marker (fun () -> produce name t (fun binding -> materialize name binding; f ()));
      release t; check (not (Sys.file_exists ("." ^ name ^ ".tmp"))) "failed candidate survived";
      settled base)
      [(fun () -> failwith "marker"); (fun () -> Lwt_unix.sleep 0.002 >>= fun () -> fail (Failure "marker"))]);
  test "failed native preparation retires before exact retry" (fun () ->
    fails (function Unix.Unix_error (Unix.ENOENT,_,_) -> true | _ -> false)
      (fun () -> T.prepare_admitted ~require_producer:true ~logical_root:root
        ~local_path:(p "bad.raw") ~working_dir:(Fspath.canonize (Some (Filename.concat (Sys.getcwd ()) "absent")))
        ~candidate:(p ".bad.tmp") ~target:(p "bad.raw") ~normalize:false ~check_apple_double:false ());
    settled base;
    let t=token (ticket "retry.raw") in release t; settled base);
  let handoff_fault name queued =
    let holder = if queued then Some (token (ticket "handoff-holder.raw")) else None in
    HandoffFault.arm (fun () ->
      let usage = R.admission_usage () in
      check (fd_count () = base + 4 && usage.A.transactions = 1 &&
             usage.A.descriptors = 24 && usage.A.pending = 0)
        "handoff fault ran before the actual native owner was Ready";
      phase (name ^ "-Ready-before-result"));
    let preparing = ticket (name ^ ".raw") in
    (match holder with
     | None -> ()
     | Some held ->
         check (Lwt.poll preparing = None && fd_count () = base + 4 &&
                (R.admission_usage ()).A.pending = 1)
           "queued handoff did not wait before native preparation";
         release held);
    fails (function Out_of_memory -> true | _ -> false) (fun () -> preparing);
    check (!(HandoffFault.hits) = 1) "success-continuation fault did not run exactly once";
    check (fd_count () = base)
      "DESIGNATED prepared native owner escaped failed token handoff";
    settled base;
    let retry = token (ticket (name ^ "-retry.raw")) in
    check (fd_count () = base + 4 && (R.admission_usage ()).A.descriptors = 24)
      "failed token handoff prevented admitted native retry";
    release retry; release retry; settled base in
  test "handoff-sync" (fun () -> handoff_fault "handoff-sync" false);
  test "handoff-async" (fun () -> handoff_fault "handoff-async" true);
  if !cases = 0 then failwith "no native lifecycle controls selected";
  Printf.printf "PASS %d lifecycle groups / %d assertions; phase-boundary census only\n%!" !cases !assertions
