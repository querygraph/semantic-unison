open Lwt
module H = HelperSupervisor
let helper = Sys.argv.(1)
let only = if Array.length Sys.argv > 2 then Some (int_of_string Sys.argv.(2)) else None
let checks = ref 0
let check yes text = incr checks; if not yes then failwith text
let descriptors () =
  let rec loop number found =
    if number = 256 then List.rev found else
    let open_ = try ignore (Unix.fstat (Obj.magic number : Unix.file_descr)); true
      with Unix.Unix_error (Unix.EBADF, _, _) -> false in
    loop (number + 1) (if open_ then number :: found else found) in
  loop 0 []
let cleanup_child () =
  let pid = Fixture.pid () in
  if pid > 0 then begin
    let owned = try ignore (Fixture.exited_unreaped pid); true
      with Unix.Unix_error (Unix.ECHILD, _, _) -> false in
    if owned then begin
      (try Unix.kill (-pid) Sys.sigkill with Unix.Unix_error _ -> ());
      let rec reap () = try ignore (Unix.waitpid [] pid) with
        | Unix.Unix_error (Unix.EINTR, _, _) -> reap ()
        | Unix.Unix_error (Unix.ECHILD, _, _) -> () in
      reap ()
    end
  end
let close_sentinel () = match !Fixture.sentinel with
  | None -> ()
  | Some fd -> Fixture.sentinel := None; (try Unix.close fd with Unix.Unix_error _ -> ())
let case code extra =
  let baseline = descriptors () in
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:1 in
  let cancellation = H.cancellation () in
  Fixture.reset code extra (fun () -> H.usage t = (2,1));
  let result =
    try Ok (Lwt_unix.run (H.run t ~weight:2 cancellation
      ~limits:{H.timeout=2.;terminate_grace=0.02;stdout_bytes=4096;stderr_bytes=4096}
      ~executable:helper ~arguments:[|(if code = 0 || code = 10 || code = 11 then "0.03" else "0.3")|]
      ~environment:[||])) with error -> Error error in
  try
    let child = Fixture.pid () in
    if code <> 0 && (code < 5 || code = 7 || code = 8 || code = 12 || code >= 19) then
      check (child < 0) "pre-spawn fault unexpectedly created a child";
    if child > 0 then begin
      let already_reaped = try ignore (Unix.waitpid [Unix.WNOHANG] child); false
        with Unix.Unix_error (Unix.ECHILD, _, _) -> true in
      check (already_reaped && !Fixture.waited = 1)
        "DESIGNATED child was not actually reaped before return";
      check (not !Fixture.prematurely_released)
        "DESIGNATED permits released before owned child wait"
    end;
    check (H.usage t = (0,0)) "CPU/child credits did not retire exactly once";
    if code = 0 then
      check (match result with Ok r -> r.H.outcome = H.Completed && r.status=Some (Unix.WEXITED 0)
        | Error _ -> false) "normal run failed"
    else begin
      check !Fixture.fired "injected primary fault did not execute";
      check (match result with
        | Error Out_of_memory -> true
        | Ok {H.outcome=H.Failed reason;_} -> reason = "Out of memory"
        | _ -> false) "primary allocation error was replaced";
      if extra <> 0 then check !Fixture.secondary_fired "secondary fault did not execute"
    end;
    (match !Fixture.sentinel with
     | None -> ()
     | Some fd ->
         check (try ignore (Unix.fstat fd); true with Unix.Unix_error _ -> false)
           "clear-before-close did not preserve recycled descriptor");
    close_sentinel ();
    check (descriptors () = baseline) "owned pipe descriptor inventory changed";
    H.cancel_and_cleanup cancellation; H.cancel_and_cleanup cancellation;
    check (H.usage t=(0,0) && descriptors ()=baseline) "repeat cleanup changed retired resources";
    Printf.printf "PASS phase=%d secondary=%d pid=%d waits=%d\n%!" code extra child !Fixture.waited
  with error -> cleanup_child (); close_sentinel (); raise error
let cpu_case code =
  let baseline = descriptors () in
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:4 in
  let cancellation = H.cancellation () in
  Fixture.reset code 0 (fun () -> true);
  let did_start = ref false and did_settle = ref false and early_retirement = ref false in
  let borrowed () =
    did_start := true;
    check (H.usage t = (2,0)) "CPU-only borrower was not admitted";
    Lwt_unix.sleep 0.03 >>= fun () ->
    if H.usage t <> (2,0) then early_retirement := true;
    did_settle := true;
    return 7 in
  let result = try Ok (Lwt_unix.run (H.with_cpu_permits t ~weight:2 cancellation borrowed))
    with error -> Error error in
  check (Fixture.pid () < 0) "CPU-only test unexpectedly spawned a child";
  check !Fixture.fired "CPU-only primary fault did not execute";
  check (match result with Error Out_of_memory -> true | _ -> false)
    "CPU-only primary error was replaced";
  check (H.usage t = (0,0)) "CPU-only admission did not retire";
  if code = 26 then begin
    check (not !early_retirement) "DESIGNATED CPU borrower released before settlement";
    check (!did_start && !did_settle) "CPU-only borrower was not settled" end;
  H.cancel_and_cleanup cancellation; H.cancel_and_cleanup cancellation;
  check (H.usage t = (0,0) && descriptors () = baseline)
    "CPU-only repeated cleanup changed resources";
  Printf.printf "PASS CPU phase=%d settled=%b\n%!" code !did_settle
let queue_case cancelled =
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:4 in
  let holder = H.cancellation () and outer = H.cancellation () and inner = H.cancellation () in
  Fixture.reset 0 0 (fun () -> true);
  let order = ref [] and nested = ref (Lwt.return None) in
  let holding = H.with_cpu_permits t ~weight:2 holder (fun () -> Lwt_unix.sleep 0.04) in
  let record number () = order := number :: !order; return number in
  Fixture.on_publish := (fun () ->
    Fixture.on_publish := (fun () -> ());
    if cancelled then H.cancel outer else
    nested := H.with_cpu_permits t ~weight:2 inner (record 2));
  let waiting = H.with_cpu_permits t ~weight:2 outer (record 1) in
  Lwt_unix.run (holding >>= fun _ -> waiting >>= fun value ->
    !nested >>= fun nested_value ->
    check (if cancelled then value=None && !order=[]
           else value=Some 1 && nested_value=Some 2 && List.rev !order=[2;1])
      "DESIGNATED reentrant publication lost or duplicated a queue ticket";
    return ());
  check (H.usage t=(0,0)) "queue control leaked permits";
  H.cancel_and_cleanup holder; H.cancel_and_cleanup outer; H.cancel_and_cleanup inner;
  check (H.usage t=(0,0)) "queue cleanup retired credits twice";
  Printf.printf "PASS queue cancelled=%b\n%!" cancelled
let registration_cancel_case () =
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:1 in
  let c = H.cancellation () in
  Fixture.reset 0 0 (fun () -> true);
  Fixture.on_registration := (fun () -> Fixture.on_registration := (fun () -> ()); H.cancel c);
  let result = Lwt_unix.run (H.run t ~weight:2 c
    ~limits:{H.timeout=2.;terminate_grace=0.02;stdout_bytes=4096;stderr_bytes=4096}
    ~executable:helper ~arguments:[|"0.03"|] ~environment:[||]) in
  check (result.H.outcome=H.Cancelled && Fixture.pid ()<0 && H.usage t=(0,0))
    "cancel during registration published or admitted a revoked ticket";
  let fresh = H.cancellation () in
  check (Lwt_unix.run (H.with_cpu_permits t ~weight:2 fresh (fun () -> return 7))=Some 7)
    "registration cancellation stranded the queue";
  H.cancel_and_cleanup c; H.cancel_and_cleanup fresh;
  check (H.usage t=(0,0)) "registration cancellation cleanup over-retired";
  Printf.printf "PASS registration cancellation\n%!"
let queue_capacity_case () =
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:1 in
  let holder = H.cancellation () and outer = H.cancellation () and inner = H.cancellation () in
  Fixture.reset 0 0 (fun () -> true);
  let nested = ref (Lwt.return None) in
  let holding = H.with_cpu_permits t ~weight:2 holder (fun () -> Lwt_unix.sleep 0.04) in
  Fixture.on_publish := (fun () -> Fixture.on_publish := (fun () -> ());
    nested := H.with_cpu_permits t ~weight:2 inner (fun () -> return 2));
  let rejected = try ignore (Lwt.poll (H.with_cpu_permits t ~weight:2 outer (fun () -> return 1))); false
    with Invalid_argument _ -> true in
  check rejected "reentrant publication exceeded pending capacity";
  Lwt_unix.run (holding >>= fun _ -> !nested >>= fun result ->
    check (result=Some 2) "reentrant capacity refusal lost existing queue owner"; return ());
  H.cancel_and_cleanup holder; H.cancel_and_cleanup outer; H.cancel_and_cleanup inner;
  check (H.usage t=(0,0)) "reentrant capacity cleanup over-retired";
  Printf.printf "PASS queue capacity\n%!"
let delayed_grant_case code =
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:1 in
  let holder = H.cancellation () and queued = H.cancellation () and fresh = H.cancellation () in
  Fixture.reset 0 0 (fun () -> true);
  let holding = H.with_cpu_permits t ~weight:2 holder (fun () -> Lwt_unix.sleep 0.03) in
  Fixture.selected := code;
  let waiting = H.with_cpu_permits t ~weight:2 queued (fun () -> return 1) in
  let rejected = Lwt_unix.run (holding >>= fun _ -> Lwt.catch
    (fun () -> waiting >>= fun _ -> return false)
    (function Out_of_memory -> return true | error -> fail error)) in
  check (rejected && !Fixture.fired) "delayed grant allocation fault did not propagate";
  check (H.usage t=(0,0)) "delayed grant fault changed CPU counters";
  check (Lwt_unix.run (H.with_cpu_permits t ~weight:2 fresh (fun () -> return 3))=Some 3)
    "delayed grant fault stranded a failed queue head";
  H.cancel_and_cleanup holder; H.cancel_and_cleanup queued; H.cancel_and_cleanup fresh;
  check (H.usage t=(0,0)) "delayed grant cleanup retired twice";
  Printf.printf "PASS delayed grant phase=%d\n%!" code
let queued_waiter_case code =
  let t = H.create ~cpu_permits:2 ~max_children:1 ~max_pending:1 in
  let holder = H.cancellation () and orphan = H.cancellation () and fresh = H.cancellation () in
  Fixture.reset 0 0 (fun () -> true);
  let holding = H.with_cpu_permits t ~weight:2 holder (fun () -> Lwt_unix.sleep 0.04) in
  Fixture.selected := code;
  let rejected = try
    if code=33 then ignore (H.with_cpu_permits t ~weight:2 orphan (fun () -> return 3))
    else ignore (H.run t ~weight:2 orphan
      ~limits:{H.timeout=2.;terminate_grace=0.02;stdout_bytes=4096;stderr_bytes=4096}
      ~executable:helper ~arguments:[|"0.03"|] ~environment:[||]);
    false with Out_of_memory -> true in
  check (rejected && !Fixture.fired) "queued outer waiter fault did not propagate";
  check (H.usage t=(2,0)) "queued outer fault retired another borrower";
  Lwt_unix.run (holding >>= fun _ -> Lwt_unix.sleep 0.04);
  check (H.usage t=(0,0) && Fixture.pid ()<0) "queued orphan later debited permits or spawned";
  check (Lwt_unix.run (H.with_cpu_permits t ~weight:2 fresh (fun () -> return 5))=Some 5)
    "queued outer waiter failure stranded admission";
  H.cancel_and_cleanup holder; H.cancel_and_cleanup orphan; H.cancel_and_cleanup fresh;
  check (H.usage t=(0,0)) "queued outer cleanup retired twice";
  Printf.printf "PASS queued outer waiter phase=%d\n%!" code
let () =
  let cases = [0,0;1,0;2,0;3,0;4,0;5,0;6,0;7,0;8,0;9,0;10,0;11,0;12,0;
               5,11;5,13;15,0;17,0;18,0;19,0;20,0;21,0;22,0;23,0;24,0;25,0] in
  List.iter (fun (code, extra) -> if only=None || only=Some code then case code extra) cases;
  if only=None || only=Some 26 then cpu_case 26;
  if only=None then begin List.iter cpu_case [27;28]; queue_case false; queue_case true;
    registration_cancel_case (); queue_capacity_case (); List.iter delayed_grant_case [31;32]; List.iter queued_waiter_case [33;34] end;
  Printf.printf "HELPER_OWNERSHIP checks=%d\n%!" !checks
