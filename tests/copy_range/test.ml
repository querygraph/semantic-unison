module C = CopyRange
let check value message = if not value then failwith message
let test name f = f (); Printf.printf "PASS %s\n%!" name
let error errno = Unix.Unix_error (errno, "injected-copy", "fixture")
let progress value completed requested =
  check (value.C.completed = completed && value.requested = requested)
    "incorrect completed-prefix receipt"
let no_notify _ = ()
let run ?(notify=no_notify) ?check_cancel ?(offset=7L) ?(length=17L) step =
  C.run ?check_cancel ~max_chunk:8 ~source_offset:offset ~length ~step ~notify ()
let scripted prefix errno =
  let calls = ref 0 in
  let step ~source_offset:_ ~length:_ =
    incr calls;
    if !calls = 1 && prefix > 0 then prefix else raise (error errno) in
  calls,step
exception Cancelled
let () =
  test "empty range makes no calls and extreme valid offsets are checked" (fun () ->
    let unexpected () = failwith "empty range performed work" in
    (match run ~offset:Int64.max_int ~length:0L ~check_cancel:unexpected
       ~notify:(fun _ -> unexpected ()) (fun ~source_offset:_ ~length:_ -> unexpected ()) with
     | C.Copied p -> progress p 0L 0L | _ -> failwith "empty copy failed");
    let offsets = ref [] in
    let initial = Int64.sub Int64.max_int 3L in
    (match run ~offset:initial ~length:3L (fun ~source_offset ~length ->
       offsets := source_offset :: !offsets; min 2 length) with
     | C.Copied p -> progress p 3L 3L | _ -> failwith "extreme valid range failed");
    check (List.rev !offsets = [initial; Int64.sub Int64.max_int 1L]) "offset overflow");
  test "short progress advances exact offsets and notifies once" (fun () ->
    let returns = ref [3;2;8;4] and calls = ref [] and notices = ref [] in
    let step ~source_offset ~length =
      calls := (source_offset,length) :: !calls;
      match !returns with n::rest -> returns := rest; n | [] -> failwith "extra call" in
    (match run ~notify:(fun n -> notices := n :: !notices) step with
     | C.Copied p -> progress p 17L 17L | _ -> failwith "short successful copies failed");
    check (List.rev !calls = [7L,8;10L,8;12L,8;20L,4]) "wrong native request bounds";
    check (List.rev !notices = [3;2;8;4]) "progress lost or duplicated");
  test "legacy unsupported cases preserve a known prefix" (fun () ->
    List.iter (fun errno -> List.iter (fun prefix ->
      let calls,step = scripted prefix errno in
      let notices = ref 0 in
      (match run ~notify:(fun n -> notices := !notices+n) step with
       | C.Unsupported (p,e) ->
           progress p (Int64.of_int prefix) 17L;
           check (e.errno=errno && e.operation="injected-copy" && e.argument="fixture")
             "native error context changed"
       | _ -> failwith "legacy unsupported error did not permit fallback");
      check (!calls=(if prefix=0 then 1 else 2) && !notices=prefix)
        "unsupported operation retried or counted failed bytes") [0;3])
      [Unix.EINVAL;Unix.ENOSYS;Unix.EXDEV;Unix.ESPIPE;Unix.ENOTSOCK;
       Unix.EOPNOTSUPP;Unix.EUNKNOWNERR (-50);Unix.EUNKNOWNERR (-1)]);
  test "unsupported suffix fallback reconstructs bytes without duplicate writes" (fun () ->
    let source = Bytes.init 40 (fun i -> Char.chr (65+i)) in
    let target = Bytes.make 40 '#' and writes = Array.make 40 0 in
    let cursor = ref 9 and calls = ref 0 in
    let write offset length =
      for i=0 to length-1 do
        Bytes.set target (!cursor+i) (Bytes.get source (offset+i));
        writes.(!cursor+i) <- writes.(!cursor+i)+1
      done; cursor := !cursor+length in
    let step ~source_offset ~length:_ =
      incr calls;
      if !calls=1 then (write (Int64.to_int source_offset) 3;3)
      else raise (error Unix.EXDEV) in
    (match run ~offset:5L ~length:19L step with
     | C.Unsupported (p,_) ->
         progress p 3L 19L;
         let copied = Int64.to_int p.completed in write (5+copied) (19-copied)
     | _ -> failwith "expected fallback receipt");
    check (!cursor=28 && !calls=2) "fallback used wrong cursor";
    for i=0 to 39 do
      let inside=i>=9 && i<28 in
      check (writes.(i)=(if inside then 1 else 0)) "fallback rewrote prefix or sentinels";
      check (Bytes.get target i=(if inside then Bytes.get source (i-9+5) else '#'))
        "fallback byte mismatch"
    done);
  test "operational errors fail before or after a prefix without fallback" (fun () ->
    List.iter (fun errno -> List.iter (fun prefix ->
      let calls,step = scripted prefix errno in
      let notices = ref 0 in
      (match run ~notify:(fun n -> notices := !notices+n) step with
       | C.Failed (p,C.System_error e) ->
           progress p (Int64.of_int prefix) 17L;
           check (e.errno=errno && e.operation="injected-copy" && e.argument="fixture")
             "operational error context changed"
       | _ -> failwith "operational failure became fallback or success");
      check (!calls=(if prefix=0 then 1 else 2) && !notices=prefix)
        "operational failure continued copying") [0;3])
      [Unix.EIO;Unix.ENOSPC;Unix.EACCES;Unix.EPERM;Unix.EROFS;Unix.EBADF;
       Unix.EINTR;Unix.EUNKNOWNERR 12345]);
  test "zero progress before EOF fails and is never notified" (fun () ->
    List.iter (fun prefix ->
      let calls = ref 0 and noticed = ref 0 in
      let step ~source_offset:_ ~length:_ =
        incr calls; if !calls=1 && prefix>0 then prefix else 0 in
      (match run ~notify:(fun n -> check (n>0) "zero progress notified"; noticed := !noticed+n) step with
       | C.Failed (p,C.No_progress) -> progress p (Int64.of_int prefix) 17L
       | _ -> failwith "zero progress accepted");
      check (!calls=(if prefix=0 then 1 else 2) && !noticed=prefix) "no-progress loop") [0;3]);
  test "invalid native counts fail without counting or retrying them" (fun () ->
    List.iter (fun returned -> List.iter (fun prefix ->
      let calls = ref 0 and notices = ref 0 in
      let step ~source_offset:_ ~length:_ =
        incr calls; if !calls=1 && prefix>0 then prefix else returned in
      (match run ~notify:(fun n -> notices := !notices+n) step with
       | C.Failed (p,C.Invalid_progress value) ->
           progress p (Int64.of_int prefix) 17L;
           check (value.returned=returned && value.requested=8) "invalid count context lost"
       | _ -> failwith "invalid native count accepted");
      check (!calls=(if prefix=0 then 1 else 2) && !notices=prefix) "invalid count used") [0;3]) [-1;9]);
  test "cancellation before and between calls propagates unchanged" (fun () ->
    List.iter (fun cancel_at ->
      let checks = ref 0 and calls = ref 0 and notices = ref 0 in
      let check_cancel () = incr checks; if !checks=cancel_at then raise Cancelled in
      let stopped = try
        ignore (run ~check_cancel ~notify:(fun n -> notices := !notices+n)
          (fun ~source_offset:_ ~length:_ -> incr calls;3)); false
        with Cancelled -> true in
      check (stopped && !calls=cancel_at-1 && !notices=3 * (cancel_at-1))
        "cancellation was classified or ignored") [1;2]);
  test "notification exceptions never enter native unsupported classification" (fun () ->
    List.iter (fun thrown ->
      let calls = ref 0 in
      let escaped = try
        ignore (run ~notify:(fun _ -> raise thrown)
          (fun ~source_offset:_ ~length:_ -> incr calls;3)); false
        with e -> e=thrown in
      check (escaped && !calls=1) "observer error became native fallback")
      [Unix.Unix_error (Unix.ENOSYS,"notify","fixture");Failure "observer";Cancelled]);
  test "cancellation and non-Unix step errors are not capability results" (fun () ->
    let raised = try ignore (run (fun ~source_offset:_ ~length:_ -> raise Sys.Break));false
      with Sys.Break -> true in
    check raised "step cancellation was swallowed";
    let raised = try ignore (run ~check_cancel:(fun () -> raise (error Unix.ENOSYS))
      (fun ~source_offset:_ ~length:_ -> failwith "cancelled step ran"));false
      with Unix.Unix_error (Unix.ENOSYS,_,_) -> true in
    check raised "cancellation Unix error became unsupported");
  test "invalid ranges reject before any effects" (fun () ->
    List.iter (fun (offset,length,max_chunk) ->
      let called = ref false in
      let rejected = try
        ignore (C.run ~check_cancel:(fun () -> called := true)
          ~max_chunk ~source_offset:offset ~length
          ~step:(fun ~source_offset:_ ~length:_ -> called := true;1)
          ~notify:(fun _ -> called := true) ());false
        with Invalid_argument _ -> true in
      check (rejected && not !called) "invalid request performed effects")
      [-1L,0L,8;0L,-1L,8;Int64.max_int,1L,8;0L,1L,0]);
  print_endline "Copy range: exact prefixes, explicit fallback, operational failures and callback boundaries"
