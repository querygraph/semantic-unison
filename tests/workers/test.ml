open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
module A = SemanticAdmission
module Synthetic = struct
  let profile = "test.synthetic/0"
  let inspect file =
    if SemanticFile.size file <> 64L || SemanticFile.read file 0L 4 <> "SYN1" then
      Error "not synthetic format"
    else Ok {FormatExtension.regions=[{FormatExtension.offset=4L;length=16}]}
end
let check value reason = if not value then failwith reason
let budget n = H.create ~cpu_permits:n ~max_children:n ~max_pending:128
let fd path = Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0
let hash pool c path =
  let file = fd path in
  try_bind (fun () -> W.digest pool c file)
    (fun result -> Unix.close file; return result)
    (fun exn -> Unix.close file; fail exn)
let inspect pool c path =
  let file = fd path in
  try_bind (fun () -> W.inspect_dng pool c file)
    (fun result -> Unix.close file; return result)
    (fun exn -> Unix.close file; fail exn)
let expect_failed f = try ignore (Lwt_unix.run (f ())); false with W.Failed _ -> true
let rec await = function
  | [] -> return []
  | job :: jobs -> job >>= fun result -> await jobs >>= fun rest -> return (result :: rest)
let test name f = f (); Printf.printf "PASS %s\n%!" name
let write_fixture () =
  let channel = open_out_bin "sample" in
  let block = Bytes.init 65536 (fun i -> Char.chr ((i * 71 + 19) land 255)) in
  for _ = 1 to 256 do output_bytes channel block done;
  close_out channel;
  let file = fd "sample" in
  let digest = SemanticFile.with_fd file SemanticFile.digest in
  Unix.close file;
  digest
let finish pool budget =
  Lwt_unix.run (W.shutdown pool);
  check (H.usage budget = (0, 0)) "leaked CPU permits";
  check ((W.usage pool).pending = 0 && (W.usage pool).running = 0) "worker not settled"
let () =
  let expected = write_fixture () in
  test "36 actual domains, immutable digest parity and bounded concurrency" (fun () ->
    let b = budget 36 in
    let pool = W.create ~workers:36 ~max_pending:72 ~budget:b in
    let jobs = List.init 72 (fun _ -> hash pool (H.cancellation ()) "sample") in
    let results = Lwt_unix.run (await jobs) in
    List.iter (function Some f ->
      check (f.W.digest = expected && f.stats.Unix.LargeFile.st_size = 16777216L) "digest mismatch"
      | None -> failwith "unexpected cancellation") results;
    let u = W.usage pool in
    check (u.workers = 36 && u.peak_running > 1 && u.peak_running <= 36) "domain concurrency not bounded";
    finish pool b;
    Lwt_unix.run (W.shutdown pool);
    check (expect_failed (fun () -> hash pool (H.cancellation ()) "sample")) "closed pool accepted job");
  test "shared CPU reservation prevents dispatch and queued cancellation releases fd" (fun () ->
    let b = budget 1 in
    let io = IoAdmission.create ~per_device:1 ~max_pending:4 in
    let pool = W.create_with_io ~io ~workers:2 ~max_pending:2 ~budget:b in
    let release = Lwt.wait () in
    let held = H.with_cpu_permits b ~weight:1 (H.cancellation ()) (fun () -> release) in
    let c = H.cancellation () in
    let job = hash pool c "sample" in
    let checked = Lwt_unix.sleep 0.03 >>= fun () ->
      check ((W.usage pool).running = 0 && H.usage b = (1, 0) &&
        (IoAdmission.usage io).active_jobs=1) "ignored shared CPU budget or I/O lease";
      H.cancel c; job >>= fun result ->
      check (result = None && (IoAdmission.usage io).active_jobs=0)
        "queued CPU cancellation returned result or retained I/O lease";
      Lwt.wakeup release (); held >>= fun _ -> return () in
    Lwt_unix.run checked;
    finish pool b);
  test "filesystem waiters occupy no CPU or domain slots; disjoint errors and shutdown settle" (fun () ->
    let b = budget 2 in
    let io = IoAdmission.create ~per_device:1 ~max_pending:16 in
    let file = fd "sample" in
    let devices = IoAdmission.devices_of_fds [file] in
    let release = Lwt.wait () in
    let held = IoAdmission.with_devices io (H.cancellation ()) ~devices (fun () -> release) in
    let pool = W.create_with_io ~io ~workers:2 ~max_pending:8 ~budget:b in
    let cancellations = List.init 6 (fun _ -> H.cancellation ()) in
    let jobs = List.map (fun c -> hash pool c "sample") cancellations in
    Lwt_unix.run (Lwt_unix.sleep 0.03);
    check (H.usage b=(0,0) && (W.usage pool).running=0 &&
      (IoAdmission.usage io).pending=6) "filesystem wait consumed execution resources";
    (* A native pipe is a separate device group on this qualified host. Its
       rejection must reach an actual worker despite older blocked file jobs.
       This proves scheduling independence, not two-storage-device throughput. *)
    let r,w = Unix.pipe ~cloexec:true () in
    check (IoAdmission.devices_of_fds [r] <> devices) "pipe device does not distinguish groups";
    check (expect_failed (fun () -> W.digest pool (H.cancellation ()) r))
      "blocked file jobs prevented disjoint native worker rejection";
    Unix.close r; Unix.close w;
    Lwt_unix.run (W.shutdown pool);
    List.iter (fun result -> check (result=None) "shutdown lost queued I/O cancellation")
      (Lwt_unix.run (await jobs));
    check ((IoAdmission.usage io).pending=0 && (IoAdmission.usage io).active_jobs=1)
      "shutdown cancelled unrelated I/O lease or leaked queued jobs";
    Lwt.wakeup release ();
    ignore (Lwt_unix.run held); Unix.close file;
    check ((IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).devices=[])
      "filesystem ledger did not settle";
    finish pool b);
  test "actual hash and same-filesystem apply share one execution credit" (fun () ->
    let b = budget 4 in let io = IoAdmission.create ~per_device:1 ~max_pending:16 in
    let pool = W.create_with_io ~io ~workers:4 ~max_pending:16 ~budget:b in
    let jobs = List.init 8 (fun _ -> hash pool (H.cancellation ()) "sample") in
    List.iter (function Some result -> check (result.W.digest=expected) "I/O gated hash mismatch"
      | _ -> failwith "I/O gated hash cancelled") (Lwt_unix.run (await jobs));
    check ((W.usage pool).peak_running=1 && (IoAdmission.usage io).peak_per_device=1)
      "same-filesystem jobs exceeded their execution limit";
    let basis = fd "fixture.dng" and target = fd "target.dng" in
    let proof file = match SemanticFile.with_fd file
      (SemanticDelta.inspect (module DngSemantic)) with Ok p -> p | Error e -> failwith e in
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'i')
      ~base:(proof basis) ~target:(proof target) with Ok p -> p | Error e -> failwith e in
    let output = Unix.openfile "io-stage.dng" [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL] 0o600 in
    let original = SemanticFile.with_fd basis (fun f -> SemanticFile.read f 0L 8192) in
    ignore (Unix.write_substring output original 0 (String.length original));
    check (Lwt_unix.run (W.apply_dng pool (H.cancellation ()) plan ~basis ~output)=Some ())
      "deduplicated source/output reservation could not materialize";
    check (SemanticFile.with_fd output SemanticFile.digest =
      SemanticFile.with_fd target SemanticFile.digest) "I/O gated target differs";
    check (SemanticFile.with_fd basis (fun f -> SemanticFile.read f 0L 8192)=original)
      "I/O gated apply changed its basis";
    Unix.close basis; Unix.close target; Unix.close output;
    check ((IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).pending=0 &&
      (IoAdmission.usage io).devices=[]) "worker completion retained I/O credits";
    finish pool b);
  test "throwing observer settles sibling completions and leaves pool usable" (fun () ->
    let b = budget 4 in let pool = W.create ~workers:4 ~max_pending:16 ~budget:b in
    let first = hash pool (H.cancellation ()) "sample" in
    let siblings = List.init 7 (fun _ -> hash pool (H.cancellation ()) "sample") in
    Lwt.ignore_result (first >>= fun _ -> fail (Failure "synthetic worker observer"));
    let propagated = try
      Lwt_unix.run (await siblings >>= fun _ -> Lwt_unix.sleep 0.03); false
      with Failure why -> why="synthetic worker observer" in
    check propagated "unhandled observer error disappeared";
    List.iter (function Some value -> check (value.W.digest=expected) "sibling digest changed"
      | _ -> failwith "sibling cancelled") (Lwt_unix.run (await siblings));
    (match Lwt_unix.run (hash pool (H.cancellation ()) "sample") with
     | Some value -> check (value.W.digest=expected) "pool stopped pumping after observer error"
     | _ -> failwith "pool cancelled new work");
    finish pool b);
  test "admitted weighted helper and actual domains share one CPU budget" (fun () ->
    let b = budget 8 in
    let pool = W.create ~workers:8 ~max_pending:16 ~budget:b in
    let admission = A.create ~source_headroom:None ~max_transactions:9
      ~max_payload_bytes:(16 * 1048576) ~max_descriptors:128 ~max_pending:16 in
    let lease c f = A.with_lease admission c ~role:A.Consumer
      ~cost:{A.payload_bytes=1048576;descriptors=8} f in
    let cancel_helper = H.cancellation () in
    let helper = lease cancel_helper (fun () -> H.run b ~weight:3 cancel_helper
      ~limits:{H.timeout=60.;terminate_grace=0.1;stdout_bytes=128;stderr_bytes=128}
      ~executable:"/bin/sleep" ~arguments:[|"30"|] ~environment:[||]) in
    check (H.usage b=(3,1)) "weighted helper did not reserve its CPU threads";
    let jobs = List.init 8 (fun _ -> let c = H.cancellation () in
      lease c (fun () -> hash pool c "sample")) in
    List.iter (function Some (Some f) -> check (f.W.digest=expected) "mixed-work digest mismatch"
      | _ -> failwith "mixed-work hash cancelled") (Lwt_unix.run (await jobs));
    let u = W.usage pool in
    check (u.peak_running > 1 && u.peak_running <= 5) "domains exceeded weighted helper CPU reservation";
    check (H.usage b=(3,1)) "helper CPU released before child stopped";
    H.cancel cancel_helper;
    (match Lwt_unix.run helper with Some result ->
      check (result.H.outcome=H.Cancelled) "weighted helper cancellation lost"
      | None -> failwith "active helper admission lost");
    let admitted = A.usage admission in
    check (admitted.transactions=0 && admitted.pending=0 && admitted.payload_bytes=0 && admitted.descriptors=0)
      "mixed-work resource reservation leaked";
    finish pool b);
  test "typed DNG inspection matches sequential proof without registry access" (fun () ->
    let b = budget 2 in let pool = W.create ~workers:2 ~max_pending:4 ~budget:b in
    let file = fd "fixture.dng" in
    let reference = SemanticFile.with_fd file (SemanticDelta.inspect (module DngSemantic)) in
    Unix.close file;
    let reference = match reference with Ok p -> p | Error e -> failwith e in
    let jobs = List.init 4 (fun _ -> inspect pool (H.cancellation ()) "fixture.dng") in
    List.iter (function
      | Some {W.proof = Ok proof; stats} ->
        check (stats.Unix.LargeFile.st_size = 8192L) "inspection stat mismatch";
        check (SemanticDelta.classify ~base:reference ~target:proof = FormatExtension.Exact_bytes)
          "inspection proof mismatch"
      | _ -> failwith "valid DNG inspection declined") (Lwt_unix.run (await jobs));
    (match Lwt_unix.run (inspect pool (H.cancellation ()) "sample") with
      | Some {W.proof = Error _; _} -> ()
      | _ -> failwith "non-DNG did not return eligibility reason");
    finish pool b);
  test "DNG whole-file proof hashing is cancellable and keeps owner responsive" (fun () ->
    let b = budget 1 in let pool = W.create ~workers:1 ~max_pending:2 ~budget:b in
    let c = H.cancellation () in
    let job = inspect pool c "large.dng" in
    let result = Lwt_unix.run (Lwt_unix.sleep 0.02 >>= fun () -> H.cancel c; job) in
    check (result = None && H.usage b = (0,0)) "DNG inspection cancellation failed";
    finish pool b);
  test "cancellation reaches active worker without an owner-loop tick" (fun () ->
    let b = budget 1 in let io = IoAdmission.create ~per_device:1 ~max_pending:4 in
    let pool = W.create_with_io ~io ~workers:1 ~max_pending:2 ~budget:b in
    let c = H.cancellation () in
    let job = inspect pool c "large.dng" in
    let rec started () = if (W.usage pool).running > 0 then return ()
      else Lwt_unix.sleep 0.001 >>= started in
    Lwt_unix.run (started ());
    H.cancel c;
    (* Intentionally stop the owner loop: cancellation must already be atomic. *)
    Unix.sleepf 0.1;
    check ((W.usage pool).running = 0) "worker waited for owner cancellation timer";
    check (H.usage b = (1,0) && (IoAdmission.usage io).active_jobs=1)
      "CPU/I/O budget released before owner consumed completion";
    check (Lwt_unix.run job = None) "direct cancellation lost";
    check ((IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).devices=[])
      "active cancellation retained I/O credits";
    finish pool b);
  test "typed DNG apply reconstructs exact target and rejects live inode" (fun () ->
    let b = budget 2 in let pool = W.create ~workers:2 ~max_pending:4 ~budget:b in
    let proof path = match Lwt_unix.run (inspect pool (H.cancellation ()) path) with
      | Some {W.proof = Ok p; _} -> p | _ -> failwith "missing proof" in
    let base = proof "fixture.dng" and target = proof "target.dng" in
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target with
      | Ok p -> p | Error e -> failwith e in
    let basis = fd "fixture.dng" in
    let output = Unix.openfile "stage.dng" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
    check (Lwt_unix.run (W.apply_dng pool (H.cancellation ()) plan ~basis ~output) = Some ())
      "apply failed";
    let actual = SemanticFile.with_fd output SemanticFile.digest in
    let expected = match Lwt_unix.run (hash pool (H.cancellation ()) "target.dng") with
      | Some f -> f.W.digest | _ -> failwith "missing target hash" in
    check (actual = expected) "apply target mismatch";
    check (expect_failed (fun () -> W.apply_dng pool (H.cancellation ()) plan ~basis ~output:basis))
      "same inode accepted";
    (* Reapplying requires the exact old basis in output, so this must fail. *)
    check (expect_failed (fun () -> W.apply_dng pool (H.cancellation ()) plan ~basis ~output))
      "stale output accepted";
    check (SemanticFile.with_fd output SemanticFile.digest = expected) "failed apply changed output";
    Unix.close basis; Unix.close output; finish pool b);
  test "generic registered second extension inspects and applies through the same workers" (fun () ->
    FormatExtension.register ~capability:"test-synthetic-v0" (module Synthetic);
    let extension = match FormatExtension.resolve Synthetic.profile with
      | Some e -> e | None -> failwith "registered extension missing" in
    check (FormatExtension.resolve "unknown-profile" = None) "unknown profile resolved";
    check (FormatExtension.capability extension = "test-synthetic-v0") "capability lost";
    let write path value = let channel = open_out_bin path in output_string channel value; close_out channel in
    let contents c = "SYN1" ^ String.make 16 c ^ String.make 44 'P' in
    write "synthetic-base" (contents 'A'); write "synthetic-target" (contents 'B');
    write "synthetic-output" (contents 'A');
    let b = budget 2 in let pool = W.create ~workers:2 ~max_pending:4 ~budget:b in
    let proof path = let file = fd path in
      let result = Lwt_unix.run (W.inspect pool (H.cancellation ()) ~extension file) in
      Unix.close file;
      match result with Some {W.proof=Ok p;_} -> p | _ -> failwith "synthetic inspection declined" in
    let base = proof "synthetic-base" and target = proof "synthetic-target" in
    let desc = SemanticDelta.describe target in
    check (desc.profile = Synthetic.profile && desc.size = 64L &&
      desc.digest = SemanticHash.string (contents 'B') && List.length desc.regions = 1)
      "public proof description incorrect";
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target with
      | Ok p -> p | Error e -> failwith e in
    let basis = fd "synthetic-base" in
    let output = Unix.openfile "synthetic-output" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
    let wrong = FormatExtension.trusted (module DngSemantic) in
    check (expect_failed (fun () -> W.apply pool (H.cancellation ()) ~extension:wrong plan ~basis ~output))
      "profile mismatch accepted";
    check (SemanticFile.with_fd output SemanticFile.digest = SemanticHash.string (contents 'A'))
      "profile mismatch wrote stage";
    check (Lwt_unix.run (W.apply pool (H.cancellation ()) ~extension plan ~basis ~output) = Some ())
      "generic apply failed";
    check (SemanticFile.with_fd output SemanticFile.digest = desc.digest) "generic target differs";
    check (SemanticFile.with_fd basis SemanticFile.digest = SemanticHash.string (contents 'A'))
      "generic basis changed";
    Unix.close basis; Unix.close output; finish pool b);
  test "worker enforces declared payload before proof allocation or materialization" (fun () ->
    let extension = FormatExtension.trusted ~max_payload:8 (module Synthetic) in
    let b = budget 2 in let pool = W.create ~workers:2 ~max_pending:4 ~budget:b in
    let file = fd "synthetic-base" in
    begin match Lwt_unix.run (W.inspect pool (H.cancellation ()) ~extension file) with
    | Some {W.proof=Error _;_} -> ()
    | _ -> failwith "worker ignored declared payload limit" end;
    let proof path = let file = fd path in
      let result = SemanticFile.with_fd file (SemanticDelta.inspect (module Synthetic)) in
      Unix.close file; match result with Ok p -> p | Error e -> failwith e in
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'n')
      ~base:(proof "synthetic-base") ~target:(proof "synthetic-target") with
      | Ok p -> p | Error e -> failwith e in
    let output = Unix.openfile "synthetic-limited-output" [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL] 0o600 in
    let original = "SYN1" ^ String.make 16 'A' ^ String.make 44 'P' in
    ignore (Unix.write_substring output original 0 (String.length original));
    check (expect_failed (fun () -> W.apply pool (H.cancellation ()) ~extension plan
      ~basis:file ~output)) "apply ignored payload declaration";
    check (SemanticFile.with_fd output SemanticFile.digest = SemanticHash.string original)
      "declared-limit failure changed output";
    Unix.close file; Unix.close output; finish pool b);
  test "typed DNG apply cancellation waits for worker descriptor cleanup" (fun () ->
    let b = budget 1 in let io = IoAdmission.create ~per_device:1 ~max_pending:4 in
    let pool = W.create_with_io ~io ~workers:1 ~max_pending:2 ~budget:b in
    let base = match Lwt_unix.run (inspect pool (H.cancellation ()) "large.dng") with
      | Some {W.proof = Ok p; _} -> p | _ -> failwith "missing large proof" in
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'n') ~base ~target:base with
      | Ok p -> p | Error e -> failwith e in
    let basis = fd "large.dng" in
    let output = Unix.openfile "large-stage.dng" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
    let c = H.cancellation () in
    let job = W.apply_dng pool c plan ~basis ~output in
    check (Lwt_unix.run (Lwt_unix.sleep 0.02 >>= fun () -> H.cancel c; job) = None)
      "apply cancellation lost";
    check (H.usage b = (0,0) && (W.usage pool).running = 0 &&
      (IoAdmission.usage io).active_jobs=0) "apply returned before CPU/I/O cleanup";
    Unix.close basis; Unix.close output; finish pool b);
  test "pending queue limit rejects without consuming descriptor or budget" (fun () ->
    let b = budget 1 in
    let pool = W.create ~workers:1 ~max_pending:1 ~budget:b in
    let release = Lwt.wait () in
    let held = H.with_cpu_permits b ~weight:1 (H.cancellation ()) (fun () -> release) in
    let c = H.cancellation () in
    let first = hash pool c "sample" in
    check (expect_failed (fun () -> hash pool (H.cancellation ()) "sample")) "queue bound ignored";
    H.cancel c;
    Lwt_unix.run (first >>= fun _ -> Lwt.wakeup release (); held >>= fun _ -> return ());
    finish pool b);
  test "active cancellation leaves owner responsive and finishes before permit release" (fun () ->
    let sparse = Unix.openfile "large" [Unix.O_RDWR; Unix.O_CREAT; Unix.O_EXCL] 0o600 in
    Unix.LargeFile.ftruncate sparse 1073741824L; Unix.close sparse;
    let b = budget 1 in let pool = W.create ~workers:1 ~max_pending:2 ~budget:b in
    let c = H.cancellation () in
    let job = hash pool c "large" in
    let ticks = ref 0 in
    let rec pulse n = if n = 0 then (H.cancel c; return ()) else
      Lwt_unix.sleep 0.005 >>= fun () -> incr ticks; pulse (n-1) in
    let result = Lwt_unix.run (pulse 3 >>= fun () -> job) in
    check (!ticks = 3 && result = None) "owner stalled or cancellation lost";
    check ((W.usage pool).running = 0 && H.usage b = (0, 0)) "premature permit release";
    finish pool b);
  test "nonregular fd fails safely and pool remains usable" (fun () ->
    let b = budget 1 in let pool = W.create ~workers:1 ~max_pending:2 ~budget:b in
    let r, w = Unix.pipe () in
    check (expect_failed (fun () -> W.digest pool (H.cancellation ()) r)) "pipe accepted";
    Unix.close r; Unix.close w;
    check (expect_failed (fun () -> W.digest pool (H.cancellation ()) r)) "closed fd accepted";
    check (Lwt_unix.run (hash pool (H.cancellation ()) "sample") <> None) "pool did not recover";
    finish pool b);
  test "concurrent mutation invalidates hash and caller descriptor remains owned" (fun () ->
    let b = budget 1 in let pool = W.create ~workers:1 ~max_pending:2 ~budget:b in
    let original = fd "large" in
    let job = W.digest pool (H.cancellation ()) original in
    let changed = Lwt_unix.sleep 0.01 >>= fun () ->
      let writer = Unix.openfile "large" [Unix.O_WRONLY] 0 in
      Unix.LargeFile.ftruncate writer 1073741825L; Unix.close writer;
      job in
    check (expect_failed (fun () -> changed)) "mutation accepted";
    check ((Unix.LargeFile.fstat original).Unix.LargeFile.st_size = 1073741825L) "closed caller fd";
    Unix.close original; finish pool b);
  test "shutdown cancels active and waiting jobs without cancelling other budget users" (fun () ->
    let b = budget 1 in let io = IoAdmission.create ~per_device:1 ~max_pending:4 in
    let pool = W.create_with_io ~io ~workers:2 ~max_pending:3 ~budget:b in
    let a = hash pool (H.cancellation ()) "large" in
    let rec started () = if (W.usage pool).running > 0 then return ()
      else Lwt_unix.sleep 0.001 >>= started in
    Lwt_unix.run (started ());
    let caller_c = H.cancellation () in
    let waiting = hash pool caller_c "sample" in
    Lwt_unix.run (W.shutdown pool);
    check (Lwt_unix.run a = None && Lwt_unix.run waiting = None) "shutdown retained results";
    check (not (H.is_cancelled caller_c)) "shutdown modified caller cancellation";
    check (H.usage b = (0, 0) && (IoAdmission.usage io).active_jobs=0 &&
      (IoAdmission.usage io).pending=0) "shutdown leaked CPU/I/O budget");
  test "repeated pool lifecycle leaves descriptor count stable" (fun () ->
    let descriptors () = Array.length (Sys.readdir "/dev/fd") in
    let before = descriptors () in
    for _ = 1 to 12 do
      let b = budget 1 in let pool = W.create ~workers:1 ~max_pending:2 ~budget:b in
      let c = H.cancellation () in H.cancel c;
      check (Lwt_unix.run (hash pool c "sample") = None) "cancelled admission accepted";
      finish pool b
    done;
    check (descriptors () = before) "pool lifecycle leaked descriptors");
  print_endline "All typed domain worker tests passed."
