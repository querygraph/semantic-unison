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
  test "fixed baseline stays reserved outside workspace lifetime" (fun () ->
    let baseline=cost 10 2 in
    let t=A.create_with_baseline ~baseline ~source_headroom:None ~max_transactions:4
      ~max_payload_bytes:20 ~max_descriptors:6 ~max_pending:4 in
    let a=A.accounting t in
    check(a.baseline=baseline && a.workspace=cost 0 0 && a.total_reserved=baseline && a.capacity=cost 20 6)
      "baseline capacity was not declared before acquisition";
    let release=Lwt.wait () and started=ref false in
    let active=submit t (cost 10 4) (fun()->release) in
    let waiting=submit t (cost 1 1) (fun()->started:=true;return ()) in
    check(not !started && (A.usage t).pending=1 && (A.accounting t).total_reserved=cost 20 6)
      "DESIGNATED baseline allowed another resource borrower";
    Lwt.wakeup release ();ignore(Lwt_unix.run(active >>= fun _->waiting));settled t;
    let a=A.accounting t in
    check(a.total_reserved=baseline && a.peak_reserved=cost 20 6 && a.workspace_peak=cost 10 4)
      "baseline retired or peak double-counted");
  test "source headroom is partitioned after fixed baseline" (fun () ->
    let t=A.create_with_baseline ~baseline:(cost 2 2) ~source_headroom:(Some(cost 10 8))
      ~max_transactions:2 ~max_payload_bytes:22 ~max_descriptors:34 ~max_pending:4 in
    let consumer=A.make_reservation t ~role:A.Consumer ~cost:(cost 10 24) in
    check(Lwt_unix.run(A.acquire consumer(H.cancellation()))) "baseline consumer refused";
    let source=A.make_reservation t ~role:A.Source ~cost:(cost 10 8) in
    check(Lwt_unix.run(A.acquire source(H.cancellation()))) "baseline source headroom stolen";
    check((A.accounting t).total_reserved=cost 22 34) "baseline/source capacity not conserved";
    A.retire consumer;A.retire source;settled t;
    check((A.accounting t).total_reserved=cost 2 2) "source retirement freed baseline");
  test "fixed baseline rejects invalid costs and oversized headroom" (fun () ->
    List.iter(fun baseline->
      check((try ignore(A.create_with_baseline ~baseline ~source_headroom:None ~max_transactions:2
        ~max_payload_bytes:8 ~max_descriptors:8 ~max_pending:1);false with Invalid_argument _->true))
        "invalid baseline accepted") [cost (-1) 0;cost 0 (-1);cost 9 0;cost 0 9];
    check((try ignore(A.create_with_baseline ~baseline:(cost 3 3) ~source_headroom:(Some(cost 2 2))
      ~max_transactions:2 ~max_payload_bytes:6 ~max_descriptors:6 ~max_pending:1);false
      with Invalid_argument _->true)) "headroom consumed fixed infrastructure");
  test "fixed baseline and maximal budgets cannot wrap" (fun () ->
    let t=A.create_with_baseline ~baseline:(cost 1 1) ~source_headroom:None ~max_transactions:2
      ~max_payload_bytes:max_int ~max_descriptors:max_int ~max_pending:2 in
    let owner=A.make_reservation t ~role:A.Consumer ~cost:(cost (max_int-1) (max_int-1)) in
    check(Lwt_unix.run(A.acquire owner(H.cancellation()))) "maximal baseline-adjusted grant refused";
    check((A.accounting t).total_reserved=cost max_int max_int) "baseline total overflow";
    let cancellation=H.cancellation() in
    let waiting=submit ~cancel:cancellation t (cost 1 1) (fun()->failwith "overcommitted baseline") in
    H.cancel cancellation;check(Lwt_unix.run waiting=None) "baseline waiter cancellation failed";
    A.retire owner;settled t;check((A.accounting t).total_reserved=cost 1 1) "edge baseline released");
  test "machine-integer budget edges never wrap or debit rejected owners" (fun () ->
    let t = gate max_int max_int max_int in
    let full = A.make_reservation t ~role:A.Consumer ~cost:(cost max_int max_int) in
    check (Lwt_unix.run (A.acquire full (H.cancellation ()))) "maximal legal envelope refused";
    let waiting = A.make_reservation t ~role:A.Consumer ~cost:(cost 1 1) in
    let cancel = H.cancellation () in
    let reply = A.acquire waiting cancel in
    let u = A.usage t in
    check (u.transactions=1 && u.pending=1 && u.payload_bytes=max_int &&
           u.descriptors=max_int && Lwt.poll reply=None)
      "addition overflow admitted a sibling beyond the maximal budget";
    List.iter (fun invalid ->
      let failed = try ignore (A.make_reservation t ~role:A.Consumer ~cost:invalid); false
        with A.Failed _ -> true in
      check failed "negative machine-integer edge accepted")
      [cost min_int 0; cost 0 min_int];
    H.cancel cancel; check (Lwt_unix.run reply=false) "cancelled edge waiter granted";
    A.retire waiting; A.retire full; settled t;
    let u = A.usage t in
    check (u.peak_payload_bytes=max_int && u.peak_descriptors=max_int && u.peak_transactions=1)
      "machine-edge peak accounting changed");
  test "maximal source headroom retains exact consumer/source partition" (fun () ->
    let half = max_int / 2 in
    let t = gate ~headroom:(Some (cost half half)) 2 max_int max_int in
    let consumer_cost = cost (max_int-half) (max_int-half) in
    let consumer = A.make_reservation t ~role:A.Consumer ~cost:consumer_cost in
    check (Lwt_unix.run (A.acquire consumer (H.cancellation ()))) "edge consumer refused";
    let source = A.make_reservation t ~role:A.Source ~cost:(cost half half) in
    check (Lwt_unix.run (A.acquire source (H.cancellation ()))) "reserved edge source refused";
    let u = A.usage t in
    check (u.transactions=2 && u.payload_bytes=max_int && u.descriptors=max_int)
      "source headroom partition wrapped or leaked capacity";
    A.retire consumer; A.retire source; settled t;
    let rejected = try ignore (gate ~headroom:(Some (cost (half+1) half)) 2 max_int max_int); false
      with Invalid_argument _ -> true in
    check rejected "unrepresentable two-envelope headroom accepted");
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
  test "durable owners are allocated without debit and Fresh retirement is idempotent" (fun () ->
    let t = gate 2 20 32 and c = cost 10 24 in
    let r = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (A.reservation_cost r=c && A.reservation_role r=A.Consumer &&
           not (A.is_held r)) "fresh owner changed declared role or cost";
    settled t;
    A.retire r; A.retire r; settled t;
    let rejected = try ignore (A.acquire r (H.cancellation ())); false
      with Invalid_argument _ -> true in
    check rejected "retired owner acquired again"; settled t);
  test "durable owner rejects impossible costs before any debit or queue publication" (fun () ->
    let t = gate ~headroom:(Some (cost 10 8)) 2 20 32 in
    List.iter (fun c ->
      let failed = try ignore (A.make_reservation t ~role:A.Consumer ~cost:c); false
        with A.Failed _ -> true in
      check failed "invalid retained cost accepted"; settled t)
      [cost (-1) 0; cost 0 (-1); cost 11 24; cost 10 25]);
  test "source owners cannot exceed the declared service headroom" (fun () ->
    let t = gate ~headroom:(Some (cost 10 8)) 2 20 32 in
    List.iter (fun c ->
      let rejected = try ignore (A.make_reservation t ~role:A.Source ~cost:c); false
        with A.Failed _ -> true in
      check rejected "source could wait for more than its reserved service envelope";
      settled t) [cost 11 8; cost 10 9];
    let source = A.make_reservation t ~role:A.Source ~cost:(cost 10 8) in
    check (Lwt_unix.run (A.acquire source (H.cancellation ()))) "declared source envelope rejected";
    A.retire source; settled t;
    let unreserved = gate 1 20 32 in
    let source = A.make_reservation unreserved ~role:A.Source ~cost:(cost 20 32) in
    check (Lwt_unix.run (A.acquire source (H.cancellation ()))) "undeclared source envelope changed ordinary budget";
    A.retire source; settled unreserved);
  test "durable admission remains charged between sequential workspaces and after producer return" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner did not acquire";
    let sibling = A.make_reservation t ~role:A.Consumer ~cost:c in
    let waiting = A.acquire sibling (H.cancellation ()) in
    let invoked = ref false in
    let borrower () =
      invoked := true;
      let u = A.usage t in
      check (u.transactions=1 && u.payload_bytes=10 && u.descriptors=24 && u.pending=1)
        "workspace debited again or producer return released durable capacity";
      return 17 in
    List.iter (fun workspace ->
      check (Lwt_unix.run (A.with_borrow owner ~cost:workspace borrower)=17)
        "workspace result changed";
      check (A.is_held owner && Lwt.poll waiting=None) "idle finalized owner released capacity")
      [cost 10 24; cost 1 9];
    check !invoked "durable workspace did not run";
    A.retire owner;
    check (Lwt_unix.run waiting && A.is_held sibling) "retirement did not admit sibling";
    A.retire owner; A.retire sibling; A.retire sibling; settled t);
  test "overlapping, nested and oversized workspaces leave their durable owner intact" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    let callback = Lwt.wait () and invoked = ref false in
    let active = A.with_borrow owner ~cost:(cost 4 9) (fun () -> callback) in
    let failed = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:(cost 1 1)
      (fun () -> invoked:=true; return ()))); false with A.Failed _ -> true in
    check (failed && not !invoked && A.is_held owner) "overlapping workspace consumed owner";
    Lwt.wakeup callback (); ignore (Lwt_unix.run active);
    List.iter (fun oversized ->
      let failed = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:oversized
        (fun () -> invoked:=true; return ()))); false with A.Failed _ -> true in
      check (failed && not !invoked && A.is_held owner) "invalid workspace ran or retired owner")
      [cost 11 24; cost 10 25; cost (-1) 0; cost 0 (-1)];
    ignore (Lwt_unix.run (A.with_borrow owner ~cost:c (fun () ->
      let rejected = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:(cost 0 0)
        (fun () -> invoked:=true; return ()))); false with A.Failed _ -> true in
      check (rejected && not !invoked) "nested loan entered a second workspace"; return ())));
    let u = A.usage t in
    check (u.transactions=1 && u.payload_bytes=10 && u.descriptors=24)
      "failed workspace changed durable ledger";
    A.retire owner; settled t);
  test "retirement while borrowing revokes future loans but retains credits until settlement" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    let callback = Lwt.wait () in
    let active = A.with_borrow owner ~cost:(cost 4 9) (fun () -> callback) in
    let sibling = A.make_reservation t ~role:A.Consumer ~cost:c in
    let waiting = A.acquire sibling (H.cancellation ()) in
    A.retire owner; A.retire owner;
    let u = A.usage t in
    check (not (A.is_held owner) && u.transactions=1 && u.payload_bytes=10 &&
           u.descriptors=24 && u.pending=1 && Lwt.poll waiting=None)
      "retirement released credits under running workspace";
    let rejected = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:(cost 0 0)
      (fun () -> failwith "revoked loan dispatched"))); false with A.Failed _ -> true in
    check rejected "revoked owner allowed another loan";
    Lwt.wakeup callback 29;
    check (Lwt_unix.run active=29) "active result lost after retirement";
    check (Lwt_unix.run waiting) "sibling not admitted after actual settlement";
    A.retire owner; A.retire sibling; settled t);
  test "retired durable workspaces preserve synchronous OOM and failure identity exactly once" (fun () ->
    List.iter (fun error ->
      let t = gate 1 20 32 and c = cost 10 24 in
      let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
      check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
      let caught = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:c
        (fun () -> A.retire owner; raise error))); None with e -> Some e in
      check (match caught with Some e -> e==error | None -> false)
        "synchronous retired borrower replaced primary exception";
      A.retire owner; settled t) [Out_of_memory; Failure "private synchronous borrower"]);
  test "retired durable asynchronous failure keeps credits until failed promise settles" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    let callback = Lwt.wait () and error = Failure "private asynchronous borrower" in
    let active = A.with_borrow owner ~cost:c (fun () -> callback) in
    A.retire owner;
    check ((A.usage t).descriptors=24) "asynchronous retirement released active resources";
    Lwt.wakeup_exn callback error;
    let caught = try ignore (Lwt_unix.run active); None with e -> Some e in
    check (match caught with Some e -> e==error | None -> false)
      "asynchronous workspace replaced its primary exception";
    A.retire owner; settled t);
  test "failed workspace without retirement permits reuse of the same retained owner" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    List.iter (fun callback ->
      let failed = try ignore (Lwt_unix.run (A.with_borrow owner ~cost:c callback)); false
        with Failure _ -> true in
      check (failed && A.is_held owner && (A.usage t).descriptors=24)
        "failure unexpectedly retired durable owner";
      check (Lwt_unix.run (A.with_borrow owner ~cost:(cost 1 1) (fun () -> return 31))=31)
        "workspace remained busy after failure")
      [(fun () -> failwith "synchronous");(fun () -> fail (Failure "asynchronous"))];
    A.retire owner; settled t);
  test "queued retirement and cancellation remove durable waiters synchronously" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    List.iter (fun cancel_by_token ->
      let cancel = H.cancellation () in
      let queued = A.make_reservation t ~role:A.Consumer ~cost:c in
      let waiting = A.acquire queued cancel in
      check ((A.usage t).pending=1 && Lwt.poll waiting=None) "durable request was not queued";
      if cancel_by_token then H.cancel_and_cleanup cancel else A.retire queued;
      check ((A.usage t).pending=0 && Lwt.poll waiting=Some false && not (A.is_held queued))
        "durable queued revocation left a request or debit";
      A.retire queued; check ((A.usage t).descriptors=24) "queued retire released another owner's credits")
      [false;true];
    A.retire owner; settled t);
  test "already-cancelled acquire and acquire replays cannot debit retained capacity twice" (fun () ->
    let t = gate 2 20 48 and c = cost 10 24 in
    let cancelled = H.cancellation () in H.cancel cancelled;
    let unused = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (not (Lwt_unix.run (A.acquire unused cancelled)) && not (A.is_held unused))
      "cancelled owner acquired";
    settled t;
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner (H.cancellation ()))) "owner acquisition";
    let replay = try ignore (A.acquire owner (H.cancellation ())); false with Invalid_argument _ -> true in
    check (replay && A.is_held owner && (A.usage t).transactions=1 && (A.usage t).descriptors=24)
      "acquire replay damaged or duplicated owner";
    A.retire unused; A.retire owner; settled t);
  test "queue-full rejection preserves other durable owners and can retire its ungranted handle" (fun () ->
    let t = gate ~pending:1 1 20 32 and c = cost 10 24 in
    let active = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire active (H.cancellation ()))) "owner acquisition";
    let queued = A.make_reservation t ~role:A.Consumer ~cost:c in
    let waiting = A.acquire queued (H.cancellation ()) in
    let rejected = A.make_reservation t ~role:A.Consumer ~cost:c in
    let failed = try ignore (Lwt_unix.run (A.acquire rejected (H.cancellation ()))); false
      with A.Failed _ -> true in
    check (failed && not (A.is_held rejected) && (A.usage t).pending=1 && (A.usage t).descriptors=24)
      "queue rejection charged capacity or removed existing waiter";
    A.retire rejected; A.retire queued;
    check (Lwt_unix.run waiting=false) "retired queued acquire became admitted";
    A.retire active; settled t);
  test "durable grant observer sees a held owner and may retire it without stranding its sibling" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 in
    let first = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire first (H.cancellation ()))) "first acquisition";
    let second = A.make_reservation t ~role:A.Consumer ~cost:c in
    let observed = A.acquire second (H.cancellation ()) >>= fun granted ->
      check (granted && A.is_held second && (A.usage t).descriptors=24)
        "grant callback ran before ownership/debit was published";
      A.retire second; return () in
    let third = A.make_reservation t ~role:A.Consumer ~cost:c in
    let third_waiting = A.acquire third (H.cancellation ()) in
    A.retire first;
    check (Lwt.poll observed=None && Lwt.poll third_waiting=None)
      "retirement dispatched a late borrower inline";
    ignore (Lwt_unix.run observed);
    check (Lwt_unix.run third_waiting && A.is_held third) "reentrant retirement stranded next owner";
    A.retire first; A.retire second; A.retire third; settled t);
  test "durable consumers and source owners progress at the selected 24 plus 8 descriptor minimum" (fun () ->
    let make () = gate ~headroom:(Some (cost 10 8)) 2 20 32 in
    let left = make () and right = make () in
    List.iter (fun t ->
      let consumer = A.make_reservation t ~role:A.Consumer ~cost:(cost 10 24) in
      check (Lwt_unix.run (A.acquire consumer (H.cancellation ()))) "consumer acquisition";
      let queued = A.make_reservation t ~role:A.Consumer ~cost:(cost 1 1) in
      let blocked = A.acquire queued (H.cancellation ()) in
      let source = A.make_reservation t ~role:A.Source ~cost:(cost 10 8) in
      check (A.reservation_role source=A.Source && A.reservation_cost source=cost 10 8)
        "source owner changed declared role or cost";
      check (Lwt_unix.run (A.acquire source (H.cancellation ()))) "consumer stole source service headroom";
      check (Lwt_unix.run (A.with_borrow source ~cost:(cost 10 8) (fun () -> return 37))=37)
        "source workspace did not complete";
      let u = A.usage t in
      check (u.transactions=2 && u.descriptors=32 && u.payload_bytes=20 && u.pending=1)
        "source/consumer envelope exceeded shared minimum";
      A.retire source;
      check (A.is_held consumer && Lwt.poll blocked=None) "source completion released consumer's durable owner";
      A.retire queued; check (Lwt_unix.run blocked=false) "queued consumer ignored explicit retirement";
      A.retire consumer; settled t) [left;right]);
  test "cancelling acquisition token after grant cannot release an active durable workspace" (fun () ->
    let t = gate 1 20 32 and c = cost 10 24 and cancel = H.cancellation () in
    let owner = A.make_reservation t ~role:A.Consumer ~cost:c in
    check (Lwt_unix.run (A.acquire owner cancel)) "owner acquisition";
    let callback = Lwt.wait () in
    let active = A.with_borrow owner ~cost:c (fun () -> callback) in
    H.cancel_and_cleanup cancel;
    check (A.is_held owner && (A.usage t).descriptors=24) "acquisition cancellation stole active credits";
    A.retire owner;
    check ((A.usage t).descriptors=24) "explicit retirement stole borrowed credits";
    Lwt.wakeup callback (); ignore (Lwt_unix.run active);
    A.retire owner; settled t);
  print_endline "All owner-loop semantic admission tests passed."
