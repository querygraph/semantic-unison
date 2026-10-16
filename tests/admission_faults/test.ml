open Lwt
module A = SemanticAdmission
module H = HelperSupervisor
let check value reason = if not value then failwith reason
let cost : A.cost = {payload_bytes=10; descriptors=24}
let gate ?(pending=16) () = A.create ~source_headroom:None
  ~max_transactions:1 ~max_payload_bytes:20 ~max_descriptors:32 ~max_pending:pending
let owner t = A.make_reservation t ~role:A.Consumer ~cost
let acquire r = A.acquire r (H.cancellation ())
let held t =
  let r = owner t in check (Lwt_unix.run (acquire r)) "initial acquire"; r
let drive () = Lwt_unix.run (Lwt_unix.sleep 0.03)
let usage t ~transactions ~pending =
  let u = A.usage t in
  check (u.transactions=transactions && u.pending=pending &&
         u.payload_bytes=transactions*10 && u.descriptors=transactions*24)
    "ledger is inconsistent, negative or charged twice"
let settled t = usage t ~transactions:0 ~pending:0
let is_oom f = try f (); false with Out_of_memory -> true
let test name f =
  let requested = if Array.length Sys.argv > 1 then Sys.argv.(1) else "all" in
  if requested="all" || requested=name then begin
    f (); Printf.printf "PASS %s\n%!" name
  end
let () =
  test "preallocated-success-and-failure" (fun () ->
    let value = ref 17 in
    let source = Lwt.return value and destination = Lwt.wait () in
    Lwt.wakeup_from destination source;
    check (match Lwt.poll destination with Some v -> v==value | None -> false)
      "preallocated success changed payload identity";
    let second = Lwt.wait () in Lwt.wakeup_from second source;
    check (match Lwt.poll second with Some v -> v==value | None -> false)
      "completed source was consumed";
    let error = Failure "private completed source" in
    let failed = Lwt.fail error and destination = Lwt.wait () in
    Lwt.wakeup_from destination failed;
    let caught = try ignore (Lwt.poll destination); None with e -> Some e in
    check (match caught with Some e -> e==error | None -> false)
      "preallocated failure changed exception identity");
  test "preallocated-observer-failure" (fun () ->
    let destination = Lwt.wait () and source = Lwt.return 19 in
    let marker = Failure "private raw observer" and called = ref 0 in
    Lwt.test_raw_observer destination (fun () -> incr called; raise marker);
    let caught = try Lwt.wakeup_from destination source; None with e -> Some e in
    check (match caught with Some e -> e==marker | None -> false) "observer failure identity";
    check (!called=1 && Lwt.poll destination=Some 19 && Lwt.test_waiter_count destination=0)
      "observer failure left an unsettled result or retained waiter";
    let rejected = try Lwt.wakeup_from destination source; false with Invalid_argument _ -> true in
    check (rejected && !called=1) "completed destination replayed observer");
  test "preallocated-invalid-bindings" (fun () ->
    let sleeping = Lwt.wait () and completed = Lwt.return 23 in
    let rejected = try Lwt.wakeup_from sleeping sleeping; false with Invalid_argument _ -> true in
    check (rejected && Lwt.poll sleeping=None) "sleeping source mutated destination";
    let rejected = try Lwt.wakeup_from completed (Lwt.return 29); false with Invalid_argument _ -> true in
    check (rejected && Lwt.poll completed=Some 23) "completed destination was replaced";
    let marker = Failure "private failed destination" in
    let failed = Lwt.fail marker in
    let rejected = try Lwt.wakeup_from failed completed; false with Invalid_argument _ -> true in
    let unchanged = try ignore (Lwt.poll failed); false with e -> e==marker in
    check (rejected && unchanged) "failed destination was replaced");
  test "throwing-grant-observer-drains-ready-sibling" (fun () ->
    let t = A.create ~source_headroom:None ~max_transactions:2
      ~max_payload_bytes:20 ~max_descriptors:48 ~max_pending:4 in
    let first = held t and second = held t in
    let third = owner t and fourth = owner t in
    let waiting = acquire third and sibling = acquire fourth in
    let marker = Failure "private throwing grant observer" and called = ref 0 in
    Lwt.test_raw_observer waiting (fun () -> incr called; raise marker);
    A.retire first; A.retire second;
    let caught = try drive (); None with error -> Some error in
    check (match caught with Some error -> error == marker | None -> false)
      "grant observer exception was lost or replaced";
    check (!called=1 && Lwt.poll waiting=Some true && A.is_held third)
      "throwing observer revoked or replayed its granted owner";
    check (Lwt.poll sibling=Some true && A.is_held fourth)
      "throwing grant observer stranded a ready sibling";
    A.retire third; A.retire fourth; drive (); settled t);
  test "grant-unregister-oom" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let waiting = acquire second in usage t ~transactions:1 ~pending:1;
    H.test_fail_unregister 1;
    A.retire first; ignore (is_oom drive);
    check (H.test_unregister_hits ()=1) "unregister allocation fault was not entered";
    check (Lwt.poll waiting=Some true && A.is_held second) "grant was lost at unregister failure";
    usage t ~transactions:1 ~pending:0;
    A.retire second; drive (); settled t);
  test "retired-head-unregister-oom" (fun () ->
    let t = gate ~pending:1 () in let first = held t and retired = owner t in
    let rejected = acquire retired in
    H.test_fail_unregister 1;
    A.retire retired;
    check (H.test_unregister_hits ()=1 && Lwt.poll rejected=Some false)
      "retired pending owner lost its false reply";
    usage t ~transactions:1 ~pending:0;
    let second = owner t in let waiting = acquire second in
    usage t ~transactions:1 ~pending:1;
    A.retire first; drive ();
    check (not (A.is_held retired) && Lwt.poll rejected=Some false &&
           Lwt.poll waiting=Some true && A.is_held second)
      "retired head was granted or blocked sibling compaction";
    A.retire retired; A.retire second; drive (); settled t);
  test "cancel-unregister-oom" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let cancellation = H.cancellation () in
    let waiting = A.acquire second cancellation in
    H.test_fail_unregister 1; H.cancel_and_cleanup cancellation;
    check (H.test_unregister_hits ()=1 && Lwt.poll waiting=Some false)
      "cancellation failed to revoke pending owner";
    usage t ~transactions:1 ~pending:0;
    A.retire first; drive (); A.retire second; settled t);
  let schedule name arm hits = test name (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let waiting = acquire second in
    arm 1;
    check (is_oom (fun () -> A.retire first)) "scheduling fault did not preserve original OOM";
    check (hits ()=1) "scheduling allocation fault was not entered";
    usage t ~transactions:0 ~pending:1;
    drive ();
    check (Lwt.poll waiting=Some true && A.is_held second) "one-shot scheduling fault stranded sibling";
    usage t ~transactions:1 ~pending:0;
    A.retire second; drive (); settled t) in
  schedule "schedule-yield-oom" Lwt_unix.test_fail_yields Lwt_unix.test_yield_hits;
  schedule "schedule-waiter-oom" Lwt.test_fail_waiters Lwt.test_waiter_hits;
  test "pending-reply-before-schedule-oom" (fun () ->
    let t = gate () in let first = held t and retired = owner t and second = owner t in
    let rejected = acquire retired and waiting = acquire second in
    Lwt_unix.test_fail_yields 1;
    check (is_oom (fun () -> A.retire retired)) "pending retirement schedule fault missing";
    check (Lwt.poll rejected=Some false && not (A.is_held retired))
      "scheduling exception stranded retired reply";
    usage t ~transactions:1 ~pending:1;
    A.retire first; drive ();
    check (Lwt.poll waiting=Some true) "retired head blocked surviving sibling";
    A.retire retired; A.retire second; drive (); settled t);
  test "pending-observer-error-still-schedules-sibling" (fun () ->
    let t = gate () in let first = held t and retired = owner t and second = owner t in
    let rejected = acquire retired and waiting = acquire second in
    let marker = Failure "private pending reply observer" and called = ref 0 in
    Lwt.test_raw_observer rejected (fun () ->
      incr called; check (Lwt.poll rejected=Some false) "retirement observer ran before false reply";
      raise marker);
    Lwt_unix.test_fail_yields 1;
    let caught = try A.retire retired; None with e -> Some e in
    check (match caught with Some e -> e==marker | None -> false)
      "scheduling fault replaced pending observer error";
    check (!called=1 && Lwt.test_waiter_count rejected=0 && Lwt_unix.test_yield_hits ()=1)
      "pending observer or dispatcher fault did not enter exactly once";
    usage t ~transactions:1 ~pending:1;
    A.retire first; drive ();
    check (Lwt.poll waiting=Some true && !called=1) "throwing retired observer stranded sibling";
    A.retire retired; A.retire second; drive (); settled t);
  test "primary-error-before-schedule-oom" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let waiting = acquire second and marker = Failure "private primary borrower" in
    let caught = try ignore (Lwt_unix.run (A.with_borrow first ~cost (fun () ->
      A.retire first; Lwt.test_fail_waiters 1; raise marker))); None with e -> Some e in
    check (match caught with Some e -> e==marker | None -> false)
      "dispatcher allocation failure replaced primary borrower error";
    check (Lwt.test_waiter_hits ()=1) "primary error did not exercise scheduling fault";
    drive (); check (Lwt.poll waiting=Some true) "primary error stranded sibling";
    A.retire second; drive (); settled t);
  test "borrow-waiter-oom-retains-unsettled-work" (fun () ->
    let t = gate () in let first = held t and callback = Lwt.wait () in
    Lwt.test_fail_waiters 1;
    let active = A.with_borrow first ~cost (fun () -> callback) in
    check (Lwt.test_waiter_hits ()=1 && Lwt.poll active=None) "borrow handoff fault not active";
    A.retire first;
    let second = owner t in let waiting = acquire second in
    usage t ~transactions:1 ~pending:1; drive ();
    check (Lwt.poll active=None && Lwt.poll waiting=None) "unsettled callback lost its credits";
    Lwt.wakeup callback 31;
    check (is_oom (fun () -> ignore (Lwt_unix.run active))) "borrow waiter OOM was replaced";
    drive (); check (Lwt.poll waiting=Some true) "settled exceptional callback stranded sibling";
    A.retire first; A.retire second; drive (); settled t);
  test "registration-oom-no-publication" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    H.test_fail_registration 1;
    check (is_oom (fun () -> ignore (acquire second))) "registration constructor fault missing";
    check (H.test_registration_hits ()=1 && not (A.is_held second)) "failed registration became held";
    usage t ~transactions:1 ~pending:0;
    A.retire second; A.retire first; drive (); settled t);
  test "cancellation-during-registration" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    H.test_cancel_during_registration ();
    let waiting = acquire second in
    check (Lwt.poll waiting=Some false && not (A.is_held second)) "cancelled registration was published";
    usage t ~transactions:1 ~pending:0;
    A.retire second; A.retire first; drive (); settled t);
  test "grant-bypasses-result-constructor" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let waiting = acquire second in
    Lwt.test_fail_wakeup waiting 1;
    A.retire first; let failed = is_oom drive in
    check (not failed && Lwt.test_wakeup_hits ()=0) "queued grant entered allocating result constructor";
    check (Lwt.poll waiting=Some true && A.is_held second) "preallocated queued grant was lost";
    Lwt.test_clear_wakeup ();
    A.retire second; drive (); settled t);
  test "retire-bypasses-result-constructor" (fun () ->
    let t = gate () in let first = held t and second = owner t in
    let waiting = acquire second in
    Lwt.test_fail_wakeup waiting 1;
    let failed = is_oom (fun () -> A.retire second) in
    check (not failed && Lwt.test_wakeup_hits ()=0 && Lwt.poll waiting=Some false)
      "queued retirement entered allocating result constructor or lost false reply";
    Lwt.test_clear_wakeup ();
    A.retire second; A.retire first; drive (); settled t);
  Printf.printf "Admission finite-fault controls complete\n%!"
