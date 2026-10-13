open Lwt
module I = IoAdmission
module H = HelperSupervisor
let assertions = ref 0 and groups = ref 0
let check value reason = incr assertions; if not value then failwith reason
let test name f = incr groups; f (); Printf.printf "PASS %s\n%!" name
let gate ?(pending=32) per_device = I.create ~per_device ~max_pending:pending
let submit ?(cancel=H.cancellation ()) t devices f = I.with_devices t cancel ~devices f
let tick () = ignore (Lwt_unix.run (Lwt_unix.yield ()))
let run promise = Lwt_unix.run promise
let settled t =
  let u = I.usage t in
  check (u.active_jobs=0 && u.pending=0 && u.devices=[]) "I/O credits or idle device ledger leaked"
let invalid f =
  let failed = try f (); false with Invalid_argument _ -> true in
  check failed "invalid configuration/key arity accepted"
let () =
  test "positive limits and one/two distinct device bounds" (fun () ->
    List.iter (fun (per_device,max_pending) -> invalid (fun () ->
      ignore (I.create ~per_device ~max_pending))) [0,1;1,0;-1,2;2,-1];
    let t = gate 2 in
    List.iter (fun devices -> invalid (fun () ->
      ignore (submit t devices (fun () -> failwith "invalid request started"))))
      [[];[1;2;3]];
    check (run (submit t [1;1;1] (fun () -> return 7))=Some 7) "duplicates rejected";
    settled t);
  test "duplicates use one credit and active keys are sorted" (fun () ->
    let t = gate 1 and release = Lwt.wait () in
    let first = submit t [2;1;2;1] (fun () -> release) in
    let u = I.usage t in
    check (u.devices=[1,1;2,1] && u.active_jobs=1 && u.peak_per_device=1)
      "duplicate device consumed extra credits";
    Lwt.wakeup release (); check (run first=Some ()) "duplicate result lost"; settled t);
  test "per-device limit is independent of disjoint job concurrency" (fun () ->
    let t = gate 2 and release = Lwt.wait () in
    let a = submit t [1] (fun () -> release)
    and b = submit t [1] (fun () -> release)
    and c = submit t [2] (fun () -> release) in
    let blocked = ref false in
    let d = submit t [1] (fun () -> blocked := true; return ()) in
    check ((I.usage t).devices=[1,2;2,1] && (I.usage t).active_jobs=3 && not !blocked)
      "per-device/global counts conflated";
    Lwt.wakeup release ();
    List.iter (fun promise -> ignore (run promise)) [a;b;c;d];
    check ((I.usage t).peak_jobs=3 && (I.usage t).peak_per_device=2) "aggregate peaks wrong";
    settled t);
  test "multi-device acquisition reserves atomically and avoids ABBA" (fun () ->
    let t = gate 1 and release_a = Lwt.wait () and release_b = Lwt.wait () in
    let a = submit t [1] (fun () -> release_a)
    and b = submit t [2] (fun () -> release_b) in
    let order = ref [] in
    let first = submit t [2;1] (fun () -> order := !order @ [1]; return ())
    and second = submit t [1;2] (fun () -> order := !order @ [2]; return ()) in
    Lwt.wakeup release_a (); tick ();
    check (!order=[] && (I.usage t).devices=[2,1]) "partial multi-device reservation acquired free A";
    Lwt.wakeup release_b ();
    List.iter (fun promise -> ignore (run promise)) [a;b;first;second];
    check (!order=[1;2]) "atomic AB/BA requests did not finish in conflict FIFO order";
    settled t);
  test "blocked multi-device request bars conflicting bypass but permits disjoint work" (fun () ->
    let t = gate 1 and release_b = Lwt.wait () and release_ab = Lwt.wait () in
    let b = submit t [2] (fun () -> release_b) in
    let ab_started = ref false and a_started = ref false and c_started = ref false in
    let ab = submit t [1;2] (fun () -> ab_started := true; release_ab)
    and a = submit t [1] (fun () -> a_started := true; return ())
    and c = submit t [3] (fun () -> c_started := true; return ()) in
    check (not !a_started) "conflicting request bypassed older multi-device waiter";
    check (!c_started && not !ab_started && (I.usage t).devices=[2,1])
      "disjoint device did not bypass blocked FIFO head";
    Lwt.wakeup release_b (); tick ();
    check (!ab_started && not !a_started && (I.usage t).devices=[1,1;2,1])
      "older atomic request lost available credit to younger conflict";
    Lwt.wakeup release_ab ();
    List.iter (fun promise -> ignore (run promise)) [b;ab;a;c]; settled t);
  test "queued disjoint requests bypass after release without conflicting leapfrog" (fun () ->
    let t = gate 1 and release_a = Lwt.wait () and release_c = Lwt.wait ()
    and release_ab = Lwt.wait () in
    let a = submit t [1] (fun () -> release_a)
    and c = submit t [3] (fun () -> release_c) in
    let order = ref [] in
    let ab = submit t [1;2] (fun () -> order := !order @ [1]; release_ab)
    and bc = submit t [2;3] (fun () -> order := !order @ [2]; return ())
    and cc = submit t [3] (fun () -> order := !order @ [3]; return ())
    and dd = submit t [4] (fun () -> order := !order @ [4]; return ()) in
    check (!order=[4]) "disjoint immediate request blocked by unrelated waiters";
    Lwt.wakeup release_c (); tick ();
    check (!order=[4]) "transitively conflicting waiter bypassed older key union";
    Lwt.wakeup release_a (); tick ();
    check (!order=[4;1]) "multi-device head not admitted when all its keys free";
    Lwt.wakeup release_ab ();
    List.iter (fun promise -> ignore (run promise)) [a;c;ab;bc;cc;dd];
    check (!order=[4;1;2;3]) "conflict FIFO completion order wrong"; settled t);
  test "queued cancellation removes synchronously and defers sibling starts" (fun () ->
    let t = gate 1 and release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit t [2] (fun () -> release) in
    let cancelled = submit ~cancel t [1;2] (fun () -> failwith "cancelled waiter started") in
    let started = ref false in
    let sibling = submit t [1] (fun () -> started := true; return ()) in
    H.cancel_and_cleanup cancel;
    check ((I.usage t).pending=1 && not !started) "cancel inline-started another borrower";
    check (run cancelled=None) "queued cancellation result wrong";
    ignore (run sibling); check !started "cancelled head stranded disjoint sibling";
    Lwt.wakeup release (); ignore (run active); settled t);
  test "release followed by fresh request during cleanup remains deferred" (fun () ->
    let t = gate 1 and release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit ~cancel t [1] (fun () -> release) in
    let unregister = H.on_cancel cancel (fun () -> Lwt.wakeup release ()) in
    H.cancel cancel;
    let started = ref false in
    let next = submit t [1] (fun () -> started := true; return ()) in
    check (not !started && (I.usage t).pending=1) "fresh borrower started during deferred cleanup window";
    unregister (); ignore (run active); ignore (run next); settled t);
  test "group cancellation releases no queued sibling inline" (fun () ->
    let t = gate 1 and release = Lwt.wait () in
    let active_cancel = H.cancellation () and queued_cancel = H.cancellation () in
    let active = submit ~cancel:active_cancel t [1] (fun () -> release) in
    let called = ref false in
    let waiting = submit ~cancel:queued_cancel t [1] (fun () -> called := true; return ()) in
    let unregister = H.on_cancel active_cancel (fun () -> Lwt.wakeup release ()) in
    H.cancel active_cancel;
    check (not !called) "group cancellation started late borrower";
    H.cancel queued_cancel; unregister ();
    check (run waiting=None && not !called) "cancelled sibling started";
    ignore (run active); settled t);
  test "active cancellation retains lease until callback settlement" (fun () ->
    let t = gate 1 and release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit ~cancel t [1;2] (fun () -> release) in
    H.cancel_and_cleanup cancel;
    check ((I.usage t).active_jobs=1 && (I.usage t).devices=[1,1;2,1])
      "active cancellation released credit before borrower stopped";
    Lwt.wakeup release (); check (run active=Some ()) "active result discarded"; settled t);
  test "already-cancelled request never consumes credits" (fun () ->
    let t = gate 1 and cancel = H.cancellation () in
    H.cancel cancel;
    check (run (submit ~cancel t [1] (fun () -> failwith "already cancelled started"))=None)
      "already cancelled request admitted";
    check ((I.usage t).peak_jobs=0) "already cancelled request changed peak"; settled t);
  test "synchronous asynchronous and immediate callbacks release exactly once" (fun () ->
    let t = gate 1 in
    List.iter (fun f ->
      let rejected = try ignore (run (submit t [1;2] f)); false with Failure _ -> true in
      check rejected "callback failure lost"; settled t)
      [(fun () -> failwith "synchronous");(fun () -> fail (Failure "asynchronous"))];
    for index = 1 to 20 do
      check (run (submit t [1] (fun () -> return index))=Some index) "immediate result lost";
      settled t
    done);
  test "callback cancellation reentrancy and subsequent exact admission" (fun () ->
    let t = gate 1 and cancel = H.cancellation () in
    check (run (submit ~cancel t [1;2] (fun () -> H.cancel cancel; return 42))=Some 42)
      "callback reentrant cancellation result lost";
    settled t;
    check (run (submit t [2;1] (fun () -> return 43))=Some 43) "reentrant cancellation poisoned gate";
    settled t);
  test "bounded pending queue does not bound independent active devices" (fun () ->
    let t = gate ~pending:1 1 and release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit t [1] (fun () -> release) in
    let waiting = submit ~cancel t [1] (fun () -> return ()) in
    let rejected = try ignore (run (submit t [1] (fun () -> failwith "overflow started"))); false
      with I.Failed _ -> true in
    check rejected "pending queue limit ignored";
    let independent = submit t [2] (fun () -> return 17) in
    check (run independent=Some 17) "full queue blocked disjoint immediate work";
    H.cancel cancel; check (run waiting=None) "queue overflow/cancel result wrong";
    Lwt.wakeup release (); ignore (run active); settled t);
  test "throwing cancelled observer does not strand admissible sibling" (fun () ->
    let t = gate 1 and release = Lwt.wait () and cancel = H.cancellation () in
    let active = submit t [2] (fun () -> release) in
    let cancelled = submit ~cancel t [1;2] (fun () -> failwith "cancelled observer started") in
    let started = ref false in
    let sibling = submit t [1] (fun () -> started := true; return ()) in
    Lwt.ignore_result (cancelled >>= fun _ -> fail (Failure "cancel observer"));
    H.cancel cancel;
    ignore (run sibling); check !started "throwing cancel observer stranded sibling";
    Lwt.wakeup release (); ignore (run active); settled t);
  test "admission observer error preserves siblings and rearmed dispatch" (fun () ->
    let t = gate 1 and release = Lwt.wait () in
    let active = submit t [1] (fun () -> release) in
    let first = submit t [1] (fun () -> return ()) in
    let second_started = ref false in
    let second = submit t [1] (fun () -> second_started := true; return ()) in
    Lwt.ignore_result (first >>= fun _ -> fail (Failure "admitted observer"));
    Lwt.wakeup release ();
    (* The first unhandled observer remains visible on an owner yield. *)
    let seen = try for _ = 1 to 4 do tick () done; false with Failure s -> s="admitted observer" in
    check seen "unhandled admission observer failure hidden";
    check (run second=Some () && !second_started) "admission observer stranded sibling";
    ignore (run active); settled t;
    check (run (submit t [1] (fun () -> return 9))=Some 9) "observer failure poisoned dispatch";
    settled t);
  test "native descriptor keys use fresh fstat and leave descriptors untouched" (fun () ->
    let first = Filename.temp_file "unison-io-key-" ".tmp"
    and second = Filename.temp_file "unison-io-key-" ".tmp" in
    let a = Unix.openfile first [Unix.O_RDWR;Unix.O_CLOEXEC] 0
    and b = Unix.openfile second [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    let duplicate = Unix.dup ~cloexec:true a in
    let bytes = Bytes.of_string "abcdef" in
    ignore (Unix.write a bytes 0 6); ignore (Unix.lseek a 3 Unix.SEEK_SET);
    let expected = List.sort_uniq Int.compare
      [(Unix.LargeFile.fstat a).Unix.LargeFile.st_dev;(Unix.LargeFile.fstat b).Unix.LargeFile.st_dev] in
    check (I.devices_of_fds [a;b]=expected) "device keys do not match native fstat";
    check (I.devices_of_fds [a;duplicate]=[List.hd expected]) "duplicate FD consumed duplicate key";
    check (Unix.lseek a 0 Unix.SEEK_CUR=3 && Unix.lseek duplicate 0 Unix.SEEK_CUR=3)
      "device lookup changed shared descriptor offsets";
    List.iter (fun fds -> invalid (fun () -> ignore (I.devices_of_fds fds))) [[];[a;b;duplicate]];
    Unix.close duplicate;
    let native_error = try ignore (I.devices_of_fds [duplicate]); false
      with Unix.Unix_error (Unix.EBADF,_,_) -> true in
    check native_error "closed FD error suppressed";
    check (I.devices_of_fds [a]=[(Unix.LargeFile.fstat a).Unix.LargeFile.st_dev])
      "failed key lookup closed a borrowed valid descriptor";
    Unix.close a; Unix.close b; Sys.remove first; Sys.remove second);
  test "signed ephemeral keys have no invented UUID identity restrictions" (fun () ->
    let t = gate 1 and release = Lwt.wait () in
    let active = submit t [min_int;max_int] (fun () -> release) in
    check ((I.usage t).devices=[min_int,1;max_int,1]) "integer device representation narrowed";
    Lwt.wakeup release (); ignore (run active); settled t);
  test "idle ledger does not retain distinct device history" (fun () ->
    let t = gate 1 in
    for device = 1 to 128 do
      ignore (run (submit t [device] (fun () -> return ()))); settled t
    done;
    check ((I.usage t).peak_per_device=1) "removed idle keys changed aggregate peak");
  test "CPU waiting retains IO lease and releases on cancellation settlement" (fun () ->
    let t = gate 1 and cpu = H.create ~cpu_permits:1 ~max_children:1 ~max_pending:8 in
    let release_cpu = Lwt.wait () in
    let occupied = H.with_cpu_permits cpu ~weight:1 (H.cancellation ()) (fun () -> release_cpu) in
    let cancellation = H.cancellation () and entered = ref false in
    let waiting = submit ~cancel:cancellation t [1] (fun () ->
      H.with_cpu_permits cpu ~weight:1 cancellation (fun () -> entered := true; return ())) in
    check ((I.usage t).devices=[1,1] && H.usage cpu=(1,0) && not !entered)
      "CPU and IO admission conflated";
    H.cancel cancellation;
    check ((I.usage t).active_jobs=1) "IO lease released before CPU wait settled";
    check (run waiting=Some None && not !entered) "cancelled CPU admission executed";
    settled t;
    Lwt.wakeup release_cpu (); ignore (run occupied);
    check (H.usage cpu=(0,0)) "CPU permit leaked");
  Printf.printf "All owner-loop I/O admission tests passed (%d groups, %d assertions).\n%!"
    !groups !assertions
