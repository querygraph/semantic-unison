open Lwt
module A = SemanticAdmission
module H = HelperSupervisor
let check value reason = if not value then failwith reason
let cost payload_bytes descriptors : A.cost = {payload_bytes;descriptors}
let gate ?(headroom=None) ?(pending=16) count bytes fds =
  A.create ~source_headroom:headroom ~max_transactions:count
    ~max_payload_bytes:bytes ~max_descriptors:fds ~max_pending:pending
let submit ?(role=A.Consumer) ?(cancel=H.cancellation ()) t c f =
  A.with_lease t cancel ~role ~cost:c f
let settled t =
  let u = A.usage t in
  check (u.transactions=0 && u.pending=0 && u.payload_bytes=0 && u.descriptors=0)
    "resource credits leaked"
let test name f = f (); Printf.printf "PASS %s\n%!" name
let () =
  test "transaction, payload and descriptor limits independently block" (fun () ->
    List.iter (fun (count,bytes,fds,c) ->
      let t = gate count bytes fds in
      let release = Lwt.wait () and started = ref false in
      let first = submit t c (fun () -> release) in
      let second = submit t c (fun () -> started := true; return ()) in
      check (not !started && (A.usage t).pending=1) "resource limit ignored";
      Lwt.wakeup release ();
      ignore (Lwt_unix.run (first >>= fun _ -> second));
      check !started "resource waiter never resumed"; settled t)
      [1,100,100,cost 1 1; 8,10,100,cost 6 1; 8,100,3,cost 1 2]);
  test "consumer FIFO prevents small requests bypassing the waiting head" (fun () ->
    let t = gate 8 10 100 in
    let release = Lwt.wait () and release_large = Lwt.wait () in
    let order = ref [] in
    let first = submit t (cost 6 1) (fun () -> release) in
    let large = submit t (cost 8 1) (fun () -> order := !order @ [1]; release_large) in
    let small = submit t (cost 1 1) (fun () -> order := !order @ [2]; return ()) in
    check (!order=[] && (A.usage t).pending=2) "FIFO bypass";
    Lwt.wakeup release ();
    ignore (Lwt_unix.run (Lwt_unix.yield ()));
    check (!order=[1;2]) "FIFO dispatch order changed";
    Lwt.wakeup release_large ();
    ignore (Lwt_unix.run (first >>= fun _ -> large >>= fun _ -> small)); settled t);
  test "queued cancellation removes admission immediately" (fun () ->
    let t = gate 1 10 10 and cancel = H.cancellation () in
    let release = Lwt.wait () and called = ref false in
    let active = submit t (cost 1 1) (fun () -> release) in
    let waiting = submit ~cancel t (cost 1 1) (fun () -> called := true; return ()) in
    H.cancel_and_cleanup cancel;
    check ((A.usage t).pending=0 && not !called) "queued cancellation did not remove ticket";
    check (Lwt_unix.run waiting=None) "cancelled admission started";
    Lwt.wakeup release (); ignore (Lwt_unix.run active); settled t);
  test "group cancellation starts no late borrowers during connection cleanup" (fun () ->
    let t = gate 1 10 10 in
    let active_cancel = H.cancellation () and queued_cancel = H.cancellation () in
    let release = Lwt.wait () and called = ref false in
    let active = submit ~cancel:active_cancel t (cost 1 1) (fun () -> release) in
    let waiting = submit ~cancel:queued_cancel t (cost 1 1)
      (fun () -> called := true; return ()) in
    let unregister = H.on_cancel active_cancel (fun () -> Lwt.wakeup release ()) in
    (* A close sweep can settle an active callback before cancelling its queued
       sibling. Admission must not run that sibling inside the first cancel. *)
    H.cancel active_cancel;
    check (not !called) "cancel callback started a late borrower";
    H.cancel queued_cancel; unregister ();
    ignore (Lwt_unix.run active);
    check (Lwt_unix.run waiting=None && not !called) "group cancellation lost queued token";
    settled t);
  test "throwing cancelled observer cannot strand an admissible sibling" (fun () ->
    let t = gate 4 10 10 and cancel = H.cancellation () in
    let release = Lwt.wait () and started = ref false in
    let active = submit t (cost 6 1) (fun () -> release) in
    let head = submit ~cancel t (cost 8 1) (fun () -> failwith "cancelled head started") in
    let tail = submit t (cost 4 1) (fun () -> started := true; return ()) in
    Lwt.ignore_result (head >>= fun _ -> fail (Failure "throwing observer"));
    H.cancel cancel;
    ignore (Lwt_unix.run tail);
    check !started "cancelled observer suppressed queued dispatch";
    Lwt.wakeup release (); ignore (Lwt_unix.run active); settled t);
  test "active cancellation retains resources until borrower settles" (fun () ->
    let t = gate 1 10 10 and cancel = H.cancellation () in
    let release = Lwt.wait () in
    let active = submit ~cancel t (cost 6 4) (fun () -> release) in
    H.cancel_and_cleanup cancel;
    let u = A.usage t in
    check (u.transactions=1 && u.payload_bytes=6 && u.descriptors=4)
      "released resources while active borrower still owned them";
    Lwt.wakeup release ();
    check (Lwt_unix.run active=Some ()) "active callback completion lost";
    settled t);
  test "synchronous and asynchronous failures release exactly once" (fun () ->
    let t = gate 2 20 20 in
    List.iter (fun f ->
      let failed = try ignore (Lwt_unix.run (submit t (cost 4 3) f)); false
        with Failure _ -> true in
      check failed "callback failure lost"; settled t)
      [(fun () -> failwith "synchronous"); (fun () -> fail (Failure "asynchronous"))]);
  test "pending queue and oversized reservations fail before work" (fun () ->
    let t = gate ~pending:1 1 10 10 in
    let release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit t (cost 1 1) (fun () -> release) in
    let waiting = submit ~cancel t (cost 1 1) (fun () -> return ()) in
    List.iter (fun c ->
      let failed = try ignore (Lwt_unix.run (submit t c (fun () -> failwith "started"))); false
        with A.Failed _ -> true in
      check failed "queue/size bound ignored") [cost 1 1; cost 11 1; cost 1 11];
    check ((A.usage t).pending=1 && (A.usage t).transactions=1) "rejection consumed resources";
    H.cancel cancel; ignore (Lwt_unix.run waiting);
    Lwt.wakeup release (); ignore (Lwt_unix.run active); settled t);
  test "two saturated endpoints retain source headroom for bidirectional progress" (fun () ->
    let make () = gate ~headroom:(Some (cost 10 2)) 3 30 6 in
    let left = make () and right = make () in
    let release_left = Lwt.wait () and release_right = Lwt.wait () in
    let consumers t release = List.init 2 (fun _ -> submit t (cost 10 2) (fun () -> release)) in
    let l = consumers left release_left and r = consumers right release_right in
    let blocked_left = H.cancellation () and blocked_right = H.cancellation () in
    let extra t cancel = submit ~cancel t (cost 1 1) (fun () -> failwith "consumer stole source headroom") in
    let waiting_left = extra left blocked_left and waiting_right = extra right blocked_right in
    let release_source_left = Lwt.wait () and release_source_right = Lwt.wait () in
    let started = ref 0 in
    let source t release = submit ~role:A.Source t (cost 10 2)
      (fun () -> incr started; release) in
    let sl = source left release_source_left and sr = source right release_source_right in
    check (!started=2) "waiting consumers blocked peer source progress";
    List.iter (fun t -> let u = A.usage t in
      check (u.transactions=3 && u.payload_bytes=30 && u.descriptors=6)
        "source exceeded shared global limits") [left;right];
    H.cancel blocked_left; H.cancel blocked_right;
    Lwt.wakeup release_source_left (); Lwt.wakeup release_source_right ();
    Lwt.wakeup release_left (); Lwt.wakeup release_right ();
    List.iter (fun job -> ignore (Lwt_unix.run job)) (sl::sr::waiting_left::waiting_right::l@r);
    settled left; settled right);
  test "too-small source headroom configuration fails clearly" (fun () ->
    List.iter (fun (count,bytes,fds) ->
      let failed = try ignore (gate ~headroom:(Some (cost 10 2)) count bytes fds); false
        with Invalid_argument _ -> true in
      check failed "impossible source/consumer budget accepted") [1,20,4;2,19,4;2,20,3]);
  test "resource admission does not recursively hold CPU permits" (fun () ->
    let t = gate 8 100 100 and cpu = H.create ~cpu_permits:4 ~max_children:4 ~max_pending:16 in
    let release = Lwt.wait () in
    let child = submit t (cost 1 1) (fun () ->
      H.with_cpu_permits cpu ~weight:2 (H.cancellation ()) (fun () -> release)) in
    let a = submit t (cost 1 1) (fun () ->
      H.with_cpu_permits cpu ~weight:1 (H.cancellation ()) (fun () -> release)) in
    let b = submit t (cost 1 1) (fun () ->
      H.with_cpu_permits cpu ~weight:1 (H.cancellation ()) (fun () -> release)) in
    let c = submit t (cost 1 1) (fun () ->
      H.with_cpu_permits cpu ~weight:1 (H.cancellation ()) (fun () -> return ())) in
    check (H.usage cpu=(4,0) && (A.usage t).transactions=4) "CPU and resource budgets conflated";
    Lwt.wakeup release ();
    List.iter (fun job -> ignore (Lwt_unix.run job)) [child;a;b;c];
    check (H.usage cpu=(0,0)) "CPU credits leaked"; settled t);
  print_endline "All owner-loop semantic admission tests passed."
