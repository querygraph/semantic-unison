module C = CopyRange

let check condition message = if not condition then failwith message
let tests = ref 0
let test name body =
  (try body () with error -> Printf.eprintf "FAIL %s\n%!" name; raise error);
  incr tests; Printf.printf "PASS %s\n%!" name
exception Cancelled

let context ?(errno=None) ?(mutation=C.Known_prefix) ?(native_code=0L) () =
  { C.backend=C.Linux_copy_file_range; phase=C.Copy_file_range;
    errno; mutation; native_code }
let success n = C.Native_progress (n,context ())
let run ?(notify=fun _ -> ()) ?check_cancel ?(offset=7L) ?(length=17L) step =
  C.run_native ?check_cancel ~max_chunk:8 ~source_offset:offset ~length ~step ~notify ()
let prefix (value : C.progress) completed requested =
  check (value.completed=completed && value.requested=requested) "incorrect prefix receipt"
let native_error errno = context ~errno:(Some errno) ~native_code:22L ()
let decline_context ?(mutation=C.No_effect) scope =
  let backend,phase,errno,native_code = match scope with
    | C.Platform_unavailable -> C.Platform,C.Unavailable,None,0L
    | C.Kernel_unavailable -> C.Linux_copy_file_range,C.Copy_file_range,Some Unix.ENOSYS,38L
    | C.Filesystem_unsupported -> C.Linux_copy_file_range,C.Copy_file_range,Some Unix.EOPNOTSUPP,95L
    | C.Cross_device -> C.Linux_copy_file_range,C.Copy_file_range,Some Unix.EXDEV,18L
    | C.Alignment -> C.Windows,C.Geometry,None,0L in
  {C.backend;phase;errno;mutation;native_code}
let syscall_error errno = Unix.Unix_error (errno,"injected-native","fixture")
let dangerous_errors = [Unix.EINVAL;Unix.ESPIPE;Unix.ENOTSOCK;Unix.EBADF;
  Unix.EIO;Unix.ENOSPC;Unix.EACCES;Unix.EPERM;Unix.ENOSYS;Unix.EXDEV;
  Unix.EOPNOTSUPP;Unix.EUNKNOWNERR (-50);Unix.EUNKNOWNERR (-1)]

(* The oracle checks authorized bytes/write counts independently of chunks.
   In the indeterminate case one real extra write intentionally lies outside
   the reported prefix: no returned decline may authorize another write. *)
let bytes_fixture body =
  let source=Bytes.init 50 (fun i -> Char.chr ((i*73+19) land 255)) in
  let target=Bytes.make 50 '#' and writes=Array.make 50 0 in
  let destination=9 and source_offset=5 and length=19 in
  let write displacement count =
    for i=0 to count-1 do
      let position=destination+displacement+i in
      Bytes.set target position (Bytes.get source (source_offset+displacement+i));
      writes.(position)<-writes.(position)+1
    done in
  let verify completed =
    for position=0 to 49 do
      let inside=position>=destination && position<destination+completed in
      check (writes.(position)=(if inside then 1 else 0)) "unauthorized or repeated suffix write";
      check (Bytes.get target position=(if inside then
        Bytes.get source (source_offset+position-destination) else '#')) "byte/sentinel mismatch"
    done in
  body length write verify

let () =
  test "empty/extreme valid ranges make bounded exact requests" (fun () ->
    let called=ref false in
    (match run ~offset:Int64.max_int ~length:0L
      ~check_cancel:(fun () -> called:=true) ~notify:(fun _ -> called:=true)
      (fun ~source_offset:_ ~length:_ -> called:=true; success 1) with
     | C.Copied p -> prefix p 0L 0L | _ -> failwith "empty range failed");
    check (not !called) "empty range performed work";
    let requests=ref [] in
    (match run ~offset:(Int64.sub Int64.max_int 3L) ~length:3L
      (fun ~source_offset ~length -> requests:=(source_offset,length)::!requests;success (min 2 length)) with
     | C.Copied p -> prefix p 3L 3L | _ -> failwith "extreme valid range failed");
    check (List.rev !requests=[Int64.sub Int64.max_int 3L,3;Int64.sub Int64.max_int 1L,1]) "offset overflow");
  test "short successful prefixes advance and notify exactly once" (fun () ->
    let counts=ref [3;2;8;4] and requests=ref [] and notices=ref [] in
    let step ~source_offset ~length =
      requests:=(source_offset,length)::!requests;
      match !counts with n::rest -> counts:=rest;success n | [] -> failwith "extra request" in
    (match run ~notify:(fun n -> notices:=n::!notices) step with
     | C.Copied p -> prefix p 17L 17L | _ -> failwith "short progress failed");
    check (List.rev !requests=[7L,8;10L,8;12L,8;20L,4] && List.rev !notices=[3;2;8;4]) "progress lost or repeated");
  test "each scoped decline preserves known prior and in-call prefixes" (fun () ->
    List.iter (fun scope -> List.iter (fun prior -> List.iter (fun current ->
      let calls=ref 0 and notified=ref 0 in
      let c=decline_context ~mutation:(if current=0 then C.No_effect else C.Known_prefix) scope in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;
          if prior>0 && !calls=1 then success prior else C.Native_declined (current,scope,c)) with
       | C.Native_unsupported (p,actual,observed) ->
           prefix p (Int64.of_int (prior+current)) 17L;
           check (actual=scope && observed=c) "decline context/scope changed"
       | _ -> failwith "known decline failed");
      check (!calls=(if prior=0 then 1 else 2) && !notified=prior+current) "decline accounting wrong")
      [0;2]) [0;3])
      [C.Platform_unavailable;C.Kernel_unavailable;C.Filesystem_unsupported;C.Cross_device;C.Alignment]);
  test "known decline suffix fallback matches bytes with one write per byte" (fun () ->
    bytes_fixture (fun length write verify ->
      let calls=ref 0 in
      let outcome=run ~offset:5L ~length:(Int64.of_int length)
        (fun ~source_offset ~length:_ -> incr calls;
          if !calls=1 then (write (Int64.to_int source_offset-5) 3;success 3)
          else C.Native_declined (0,C.Filesystem_unsupported,
            context ~errno:(Some Unix.EOPNOTSUPP) ~mutation:C.No_effect () )) in
      (match outcome with C.Native_unsupported (p,_,_) ->
        let completed=Int64.to_int p.completed in write completed (length-completed)
       | _ -> failwith "expected explicit decline");
      check (!calls=2) "decline was retried";verify length));
  test "errno-looking native failures preserve in-call prefixes without fallback" (fun () ->
    List.iter (fun errno -> List.iter (fun prior -> List.iter (fun current ->
      let calls=ref 0 and notified=ref 0 in
      let c=native_error errno in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;
          if prior>0 && !calls=1 then success prior else C.Native_failed (current,c)) with
       | C.Failed (p,C.Native_error observed) ->
           prefix p (Int64.of_int (prior+current)) 17L;check (observed=c) "native error context lost"
       | _ -> failwith "native operational error became fallback");
      check (!calls=(if prior=0 then 1 else 2) && !notified=prior+current) "terminal error continued work")
      [0;2]) [0;3]) dangerous_errors);
  test "thrown Unix errors never acquire legacy unsupported semantics" (fun () ->
    List.iter (fun errno -> List.iter (fun prior ->
      let calls=ref 0 and notified=ref 0 in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;
          if prior>0 && !calls=1 then success prior else raise (syscall_error errno)) with
       | C.Failed (p,C.System_error e) -> prefix p (Int64.of_int prior) 17L;
           check (e.errno=errno && e.operation="injected-native" && e.argument="fixture") "thrown error changed"
       | _ -> failwith "thrown native error became decline");
      check (!calls=(if prior=0 then 1 else 2) && !notified=prior) "thrown error retried") [0;3]) dangerous_errors);
  test "indeterminate decline cannot authorize unknown-extra-byte suffix fallback" (fun () ->
    bytes_fixture (fun length write verify ->
      let calls=ref 0 and notified=ref 0 in
      let outcome=run ~offset:5L ~length:(Int64.of_int length)
        ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls; write 0 4;
          C.Native_declined (3,C.Filesystem_unsupported,
            context ~errno:(Some Unix.EOPNOTSUPP) ~mutation:C.Indeterminate () )) in
      (* Model only the caller's permitted fallback action, then let the byte
         oracle catch an unsafe result rather than trusting status spelling. *)
      (match outcome with C.Native_unsupported (p,_,_) ->
        let completed=Int64.to_int p.completed in write completed (length-completed)
       | _ -> ());
      verify 4;
      (match outcome with C.Failed (p,C.Native_error c) -> prefix p 3L 19L;
         check (c.mutation=C.Indeterminate) "mutation uncertainty lost"
       | _ -> failwith "indeterminate decline was publishable");
      check (!calls=1 && !notified=3) "indeterminate result continued work"));
  test "indeterminate errors retain only their authoritative reported prefix" (fun () ->
    List.iter (fun prior ->
      let calls=ref 0 and notified=ref 0 in
      let c=context ~errno:(Some Unix.EIO) ~mutation:C.Indeterminate ~native_code:5L () in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;
          if prior>0 && !calls=1 then success prior else C.Native_failed (2,c)) with
       | C.Failed (p,C.Native_error observed) -> prefix p (Int64.of_int (prior+2)) 17L;
           check (observed=c) "indeterminate error lost"
       | _ -> failwith "indeterminate error became fallback");
      check (!calls=(if prior=0 then 1 else 2) && !notified=prior+2) "unknown effects counted") [0;3]);
  test "zero and invalid counts never notify invalid bytes or retry" (fun () ->
    List.iter (fun count -> List.iter (fun prior ->
      let calls=ref 0 and notified=ref 0 in
      let outcome=run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;
          if prior>0 && !calls=1 then success prior else success count) in
      (match outcome with
       | C.Failed (p,C.No_progress) when count=0 -> prefix p (Int64.of_int prior) 17L
       | C.Failed (p,C.Invalid_progress actual) when count<>0 ->
           prefix p (Int64.of_int prior) 17L;check (actual.returned=count && actual.requested=8) "bad count context"
       | _ -> failwith "invalid progress accepted");
      check (!calls=(if prior=0 then 1 else 2) && !notified=prior) "invalid progress used") [0;3]) [0;-1;9]);
  test "contradictory no-effect and indeterminate success results fail" (fun () ->
    List.iter (fun result ->
      let calls=ref 0 and notified=ref 0 in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;result) with
       | C.Failed (p,C.Invalid_native_result _) -> prefix p 0L 17L
       | _ -> failwith "contradictory effect accepted");
      check (!calls=1 && !notified=0) "malformed effect counted")
      [C.Native_progress (3,context ~mutation:C.No_effect ());
       C.Native_progress (3,context ~mutation:C.Indeterminate ());
       C.Native_declined (3,C.Alignment,decline_context C.Alignment);
       C.Native_failed (3,context ~errno:(Some Unix.EIO) ~mutation:C.No_effect ())]);
  test "raw protocol preserves every scalar context code and unsigned Win32 error" (fun () ->
    List.iteri (fun backend b -> List.iteri (fun phase p ->
      let raw=(2,3,backend,phase,Some Unix.EINVAL,1,0,4_294_967_295L) in
      match C.decode_native raw with C.Native_failed (3,c) ->
        check (c.backend=b && c.phase=p && c.errno=Some Unix.EINVAL &&
               c.mutation=C.Known_prefix && c.native_code=4_294_967_295L) "raw scalar transport changed"
      | _ -> failwith "raw error decoded wrong")
      [C.Unavailable;C.Arguments;C.Descriptors;C.Copy_file_range;C.Sendfile;
       C.Volume_query;C.Geometry;C.Sparse;C.Extend_eof;C.Duplicate_extents;
       C.Advance_position;C.Verify_position])
      [C.Platform;C.Linux_copy_file_range;C.Linux_sendfile;C.Freebsd;C.Solaris;C.Windows]);
  test "unknown/contradictory raw protocol fields reject before fallback" (fun () ->
    let valid=(2,0,1,3,Some Unix.EIO,0,0,5L) in
    let malformed=[(3,0,1,3,Some Unix.EIO,0,0,5L);
      (2,0,6,3,Some Unix.EIO,0,0,5L);(2,0,1,12,Some Unix.EIO,0,0,5L);
      (2,0,1,3,Some Unix.EIO,3,0,5L);(2,0,1,3,Some Unix.EIO,0,0,-1L);
      (0,1,1,3,Some Unix.EIO,1,0,5L);(0,1,1,3,None,1,1,0L);
      (0,1,1,3,None,1,0,5L);(2,0,1,3,None,0,0,0L);
      (2,0,1,3,Some Unix.EIO,0,1,5L);(1,0,1,3,None,0,0,0L);
      (1,0,1,3,None,0,6,0L);
      (1,0,1,3,Some Unix.EINVAL,0,3,22L);
      (1,0,1,3,Some Unix.EIO,0,3,5L);
      (1,0,1,3,Some Unix.ENOSYS,0,1,38L);
      (1,0,5,9,None,0,5,0L);
      (1,0,5,6,Some Unix.EINVAL,0,5,22L);
      (1,0,0,0,Some Unix.ENOSYS,0,1,38L)] in
    ignore (C.decode_native valid);
    List.iter (fun raw ->
      let direct_rejected=try ignore (C.decode_native raw);false with C.Invalid_native_status _ -> true in
      check direct_rejected "malformed raw status decoded";
      let calls=ref 0 in
      (match run (fun ~source_offset:_ ~length:_ -> incr calls;C.decode_native raw) with
       | C.Failed (p,C.Invalid_native_result _) -> prefix p 0L 17L
       | _ -> failwith "malformed raw status authorized fallback");
      check (!calls=1) "malformed raw status retried") malformed);
  test "direct typed operational declines cannot bypass decoder consistency" (fun () ->
    List.iter (fun c ->
      let notified=ref 0 in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> C.Native_declined (0,C.Filesystem_unsupported,c)) with
       | C.Failed (p,C.Invalid_native_result _) -> prefix p 0L 17L
       | _ -> failwith "operational decline bypassed consistency");
      check (!notified=0) "operational decline notified")
      [native_error Unix.EINVAL;native_error Unix.EIO;native_error Unix.ENOSYS;
       { (decline_context C.Filesystem_unsupported) with C.phase=C.Descriptors }]);
  test "raw count/effect contradictions fail in the strict loop" (fun () ->
    List.iter (fun raw ->
      let notified=ref 0 in
      (match run ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> C.decode_native raw) with
       | C.Failed (p,_) -> prefix p 0L 17L
       | _ -> failwith "bad raw count/effect accepted");
      check (!notified=0) "bad raw count/effect notified")
      [(0,-1,1,3,None,1,0,0L);(0,9,1,3,None,1,0,0L);
       (0,3,1,3,None,0,0,0L);(0,3,1,3,None,2,0,0L)]);
  test "cancellation before/between steps and callback exceptions propagate" (fun () ->
    List.iter (fun at ->
      let checks=ref 0 and calls=ref 0 and notified=ref 0 in
      let escaped=try ignore (run ~check_cancel:(fun () -> incr checks;if !checks=at then raise Cancelled)
        ~notify:(fun n -> notified:= !notified+n)
        (fun ~source_offset:_ ~length:_ -> incr calls;success 3));false with Cancelled -> true in
      check (escaped && !calls=at-1 && !notified=3*(at-1)) "cancel swallowed") [1;2];
    List.iter (fun thrown ->
      let calls=ref 0 in
      let escaped=try ignore (run ~notify:(fun _ -> raise thrown)
        (fun ~source_offset:_ ~length:_ -> incr calls;success 3));false with e -> e=thrown in
      check (escaped && !calls=1) "callback exception classified as native decline")
      [Cancelled;Failure "notify";syscall_error Unix.ENOSYS;C.Invalid_native_status "callback"];
    let escaped=try ignore (run (fun ~source_offset:_ ~length:_ -> raise Sys.Break));false with Sys.Break -> true in
    check escaped "step break swallowed");
  test "invalid range/overflow rejects before callbacks or steps" (fun () ->
    List.iter (fun (offset,length,maximum) ->
      let performed=ref false in
      let rejected=try ignore (C.run_native ~max_chunk:maximum ~source_offset:offset ~length
        ~check_cancel:(fun () -> performed:=true) ~notify:(fun _ -> performed:=true)
        ~step:(fun ~source_offset:_ ~length:_ -> performed:=true;success 1) ());false
        with Invalid_argument _ -> true in
      check (rejected && not !performed) "invalid range performed work")
      [-1L,0L,8;0L,-1L,8;Int64.max_int,1L,8;0L,1L,0]);
  Printf.printf "Strict CopyRange: %d named independent groups; synthetic adapters only\n%!" !tests
