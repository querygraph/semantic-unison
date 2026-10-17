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
let identify_tests () =
  let owner = Domain.self () in
  let module Matched = struct
    let format = "test.identify/matched"
    let identify file =
      check (Domain.self () <> owner) "recognizer executed on owner";
      check (SemanticFile.read file 0L 4="SYN1") "wrong probe bytes";
      FormatRecognition.Recognized
  end in
  let module Unmatched = struct
    let format = "test.identify/unmatched"
    let identify _ = FormatRecognition.Not_matched
  end in
  let module Unknown = struct
    let format = "test.identify/unknown"
    let identify _ = FormatRecognition.Indeterminate "checked unsupported structure"
  end in
  let module Error = struct
    let format = "test.identify/error"
    let identify _ = raise (Unix.Unix_error (Unix.EIO,"private recognizer read",""))
  end in
  let matched=FormatRecognition.trusted (module Matched)
  and unmatched=FormatRecognition.trusted (module Unmatched)
  and unknown=FormatRecognition.trusted (module Unknown)
  and error=FormatRecognition.trusted (module Error)
  and dng=FormatRecognition.trusted ~suffixes:[".dng"] (module DngRecognition) in
  let expected = let input=open_in "identify-probe.sha256" in
    let value=input_line input in close_in input;value in
  let identify pool cancellation recognizers path =
    let file=fd path in
    try_bind (fun () -> W.identify pool cancellation ~recognizers file)
      (fun result -> ignore(Unix.LargeFile.fstat file);Unix.close file;return result)
      (fun error -> Unix.close file;fail error) in
  let selected formats = function
    | Some result ->
      check (result.W.formats=formats) "wrong selected formats";
      (match result.W.fingerprint with
       | Some fingerprint ->
         check (SemanticHash.hex fingerprint.W.digest=expected) "conditional fingerprint differs from hashlib";
         check (fingerprint.W.stats=result.W.stats) "fingerprint/recognition identity differs"
       | None -> failwith "selected recognition lacks fingerprint")
    | None -> failwith "recognition unexpectedly cancelled" in
  let control name f = test name (fun () ->
    let before=Array.length(Sys.readdir "/dev/fd") in
    let b=budget 2 in let pool=W.create ~workers:2 ~max_pending:4 ~budget:b in
    f pool b;finish pool b;
    check (Array.length(Sys.readdir "/dev/fd")=before) "Identify lifecycle leaked FD") in
  control "Identify off-owner content match hashes the same identity" (fun pool _ ->
    selected [Matched.format] (Lwt_unix.run(identify pool (H.cancellation()) [matched,false] "identify-probe.bin")));
  control "Identify filename claim and indeterminate verdict require validation" (fun pool _ ->
    selected [Unmatched.format;Unknown.format]
      (Lwt_unix.run(identify pool (H.cancellation()) [unmatched,true;unknown,false] "identify-probe.bin")));
  control "Identify unmatched result does not hash or disturb caller position" (fun pool _ ->
    let file=fd "identify-probe.bin" in
    ignore(Unix.LargeFile.lseek file 17L Unix.SEEK_SET);
    let result=Lwt_unix.run(W.identify pool (H.cancellation()) ~recognizers:[unmatched,false] file) in
    check (match result with Some r -> r.W.formats=[] && r.W.fingerprint=None | None -> false)
      "unmatched selected or hashed";
    check (Unix.LargeFile.lseek file 0L Unix.SEEK_CUR=17L) "unmatched branch performed full hashing";
    Unix.close file);
  control "Identify DNG content recognition ignores the filename and XMP eligibility" (fun pool _ ->
    let result=Lwt_unix.run(identify pool (H.cancellation()) [dng,false] "recognition-only.bin") in
    check (match result with Some r -> r.W.formats=[DngRecognition.format] && r.W.fingerprint<>None
      | None -> false) "content DNG was not selected";
    check (not(FormatRecognition.matches_filename dng "recognition-only.bin")) "fixture unexpectedly claimed filename";
    let file=fd "recognition-only.bin" in
    let proof=SemanticFile.with_fd file (SemanticDelta.inspect(module DngExtended)) in
    Unix.close file;
    check (match proof with Error _ -> true | Ok _ -> false) "fixture unexpectedly eligible for XMP transfer");
  control "Identify operational and nonregular errors never become no match" (fun pool _ ->
    check (expect_failed(fun () -> identify pool (H.cancellation()) [error,false] "identify-probe.bin")) "EIO became unmatched";
    let r,w=Unix.pipe() in
    check (expect_failed(fun () -> W.identify pool (H.cancellation()) ~recognizers:[unmatched,false] r)) "pipe became unmatched";
    Unix.close r;Unix.close w;
    check (expect_failed(fun () -> W.identify pool (H.cancellation()) ~recognizers:[unmatched,false] r)) "closed FD became unmatched";
    selected [Matched.format] (Lwt_unix.run(identify pool (H.cancellation()) [matched,false] "identify-probe.bin")));
  control "Identify cancellation and shared CPU waiting settle without admission leaks" (fun pool b ->
    let release=Lwt.wait() in
    let held=H.with_cpu_permits b ~weight:2 (H.cancellation()) (fun () -> release) in
    let cancellation=H.cancellation() in
    let waiting=identify pool cancellation [matched,false] "identify-probe.bin" in
    check (H.usage b=(2,0) && (W.usage pool).running=0) "Identify bypassed shared CPU reservation";
    H.cancel cancellation;
    check (Lwt_unix.run waiting=None) "cancelled Identify became a result";
    Lwt_unix.run(Lwt.wakeup release ();held >>= fun _ -> return());
    check (H.usage b=(0,0) && (W.usage pool).pending=0) "Identify cancellation leaked accounting";
    selected [Matched.format] (Lwt_unix.run(identify pool (H.cancellation()) [matched,false] "identify-probe.bin")));
  control "Identify duplicate and oversized capture rejected before FD dispatch" (fun pool _ ->
    let rejects f=try ignore(f());false with Invalid_argument _ -> true in
    let file=fd "identify-probe.bin" in
    check (rejects(fun () -> W.identify pool (H.cancellation()) ~recognizers:[matched,false;matched,false] file)) "duplicate accepted";
    check (rejects(fun () -> W.identify pool (H.cancellation()) ~recognizers:(List.init 17(fun _ -> matched,false)) file)) "capture ceiling ignored";
    check ((W.usage pool).pending=0) "invalid captures dispatched";Unix.close file)
let scheduling_stress () =
  let before=Array.length(Sys.readdir "/dev/fd") in
  List.iter (fun max_pending ->
    let b=budget 1 in
    check (try ignore(W.create ~workers:1 ~max_pending ~budget:b);false
      with Invalid_argument _ -> true) "worker mailbox bound not enforced";
    check (H.usage b=(0,0)) "invalid worker capacity acquired permits") [0;-1;65537;max_int];
  check(Array.length(Sys.readdir "/dev/fd")=before) "invalid worker capacity opened descriptors";
  let seeds = [1;17;103;4099;65537;20261014] in
  let checks = ref 0 and completed = ref 0 and cancelled = ref 0 in
  let verify value reason = incr checks; check value reason in
  let sequential path =
    let file=fd path in
    let result=SemanticFile.with_fd file (fun f ->
      SemanticFile.digest f, SemanticDelta.inspect (module DngExtended) f) in
    Unix.close file; result in
  let baselines=List.map (fun path -> path,sequential path)
    ["fixture.dng";"extended-base.dng";"extended-target.dng"] in
  let extension=FormatExtension.trusted (module DngExtended) in
  List.iter (fun seed ->
    let rng=Random.State.make [|seed|] in
    let before=Array.length(Sys.readdir "/dev/fd") in
    let cpu=1+Random.State.int rng 4 in
    let b=budget cpu in
    let pool=W.create ~workers:4 ~max_pending:64 ~budget:b in
    for round=1 to 20 do
      let release=Lwt.wait () in
      let held=H.with_cpu_permits b ~weight:cpu (H.cancellation ())
        (fun () -> release) in
      let jobs=List.init 32 (fun _ ->
        let path,(digest,proof)=List.nth baselines (Random.State.int rng 3) in
        let c=H.cancellation () in
        let result=if Random.State.bool rng then
          hash pool c path >>= fun result ->
          return (Option.map (fun f ->
            verify (f.W.digest=digest) "stress hash differs from sequential") result)
        else
          let file=fd path in
          try_bind (fun () -> W.inspect pool c ~extension file)
            (fun result -> Unix.close file;
              (match result with None -> () | Some actual ->
                verify (match proof,actual.W.proof with
                  | Ok expected,Ok got -> SemanticDelta.describe expected=SemanticDelta.describe got
                  | _ -> false) "stress proof differs from sequential");
              return (Option.map (fun _ -> ()) result))
            (fun error -> Unix.close file;fail error) in
        c,result,Random.State.int rng 4=0) in
      verify (H.usage b=(cpu,0) && (W.usage pool).running=0)
        "stress worker bypassed held CPU budget";
      let shuffled=List.sort (fun (a,_) (b,_) -> compare a b)
        (List.map (fun job -> Random.State.bits rng,job) jobs) in
      List.iter (fun (_, (c,_,cancel)) -> if cancel then H.cancel c) shuffled;
      (* Await queued cancellations while every CPU credit remains held. *)
      List.iter (fun (_,job,cancel) -> if cancel then
        verify (Lwt_unix.run job=None) "queued cancellation returned data") jobs;
      Lwt.wakeup release ();
      Lwt_unix.run (held >>= fun _ -> return ());
      let results=Lwt_unix.run (await (List.map (fun (_,job,_) -> job) jobs)) in
      List.iter2 (fun (_,_,cancel) result ->
        verify ((result=None)=cancel) "stress result/cancellation mismatch";
        if cancel then incr cancelled else incr completed) jobs results;
      verify (H.usage b=(0,0) && (W.usage pool).pending=0 && (W.usage pool).running=0)
        "stress round failed settlement";
      verify ((W.usage pool).peak_running<=cpu) "stress exceeded CPU admission";
      if round mod 5=0 then Printf.printf "STRESS seed=%d round=%d cpu=%d\n%!" seed round cpu
    done;
    finish pool b;
    verify (Array.length(Sys.readdir "/dev/fd")=before) "stress descriptor leak") seeds;
  Printf.printf "PASS seeded scheduling stress seeds=%d jobs=%d completed=%d cancelled=%d checks=%d\n%!"
    (List.length seeds) (!completed + !cancelled) !completed !cancelled !checks
let apply_scheduling_stress () =
  let seeds=[1;17;103;4099;65537;20261014] in
  let checks=ref 0 and completed=ref 0 and cancelled=ref 0 and late=ref 0 in
  let verify value why=incr checks;check value why in
  let bytes path =
    let ch=open_in_bin path in
    let value=really_input_string ch (in_channel_length ch) in close_in ch;value in
  let original=bytes "extended-base.dng" and target_bytes=bytes "extended-target.dng" in
  let proof path =
    let file=fd path in
    let result=SemanticFile.with_fd file (SemanticDelta.inspect (module DngExtended)) in
    Unix.close file;match result with Ok p -> p | Error e -> failwith e in
  let base=proof "extended-base.dng" and target=proof "extended-target.dng" in
  let plan=match SemanticDelta.plan ~nonce:(String.make 32 's') ~base ~target with
    | Ok p -> p | Error e -> failwith e in
  let extension=FormatExtension.trusted (module DngExtended) in
  List.iter (fun seed ->
    let rng=Random.State.make [|seed|] in
    let before=Array.length(Sys.readdir "/dev/fd") in
    let cpu=1+Random.State.int rng 4 in
    let b=budget cpu in
    let pool=W.create ~workers:4 ~max_pending:32 ~budget:b in
    for round=1 to 4 do
      let jobs=List.init 16 (fun i ->
        let path=Printf.sprintf "stress-stage-%d-%d-%d.dng" seed round i in
        let ch=open_out_bin path in output_string ch original;close_out ch;
        let basis=fd "extended-base.dng" in
        let output=Unix.openfile path [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
        let c=H.cancellation () in
        let cancellation_delay=if i mod 2=0 then Some ([|0.;0.0001;0.001;0.005|].(Random.State.int rng 4)) else None in
        let job=try_bind
          (fun () -> W.apply_report pool c ~extension plan ~basis ~output)
          (fun result ->
            (* Caller descriptors must still be owned when worker settles. *)
            verify ((Unix.LargeFile.fstat basis).Unix.LargeFile.st_size=Int64.of_int(String.length original)) "apply closed basis";
            verify ((Unix.LargeFile.fstat output).Unix.LargeFile.st_size=Int64.of_int(String.length original)) "apply closed output";
            Unix.close basis;Unix.close output;
            (match result with None -> incr cancelled | Some report ->
              incr completed;
              verify (bytes path=target_bytes) "completed apply not exact target bytes";
              verify (report.SemanticDelta.logical_bytes_written=String.length "<x>two</x>      " && report.write_calls=1)
                "apply write report changed");
            (* Cancelled output is never reused or published. *)
            Unix.unlink path;return result)
          (fun error -> Unix.close basis;Unix.close output;fail error) in
        let timer=match cancellation_delay with None -> return () | Some delay ->
          Lwt_unix.sleep delay >>= fun () -> H.cancel c;return () in
        job,timer,cancellation_delay) in
      let results=Lwt_unix.run(await(List.map (fun (job,_,_) -> job) jobs)) in
      ignore(Lwt_unix.run(await(List.map (fun (_,timer,_) -> timer) jobs)));
      List.iter2 (fun (_,_,delay) result -> match delay,result with
        | None,None -> failwith "uncancelled apply lost result"
        | Some _,Some _ -> incr late
        | _ -> ()) jobs results;
      verify (bytes "extended-base.dng"=original) "shared basis mutated";
      verify (bytes "extended-target.dng"=target_bytes) "target oracle mutated";
      verify (H.usage b=(0,0) && (W.usage pool).pending=0 && (W.usage pool).running=0)
        "apply round resources not settled";
      verify ((W.usage pool).peak_running<=cpu) "apply exceeded shared CPU budget";
      Printf.printf "APPLY-STRESS seed=%d round=%d cpu=%d\n%!" seed round cpu
    done;
    finish pool b;
    verify (Array.length(Sys.readdir "/dev/fd")=before) "apply lifecycle descriptor leak") seeds;
  verify (!cancelled>0) "no cancellation exercised";
  Printf.printf "PASS seeded apply stress seeds=6 jobs=%d completed=%d cancelled=%d late_cancel=%d checks=%d\n%!"
    (!completed+ !cancelled) !completed !cancelled !late !checks
let read_stats_tests () =
  let expected = write_fixture () in
  test "reader reports exact repeated reads/iteration/hash and ignores empty requests" (fun () ->
    let file = fd "sample" in
    let size = (Unix.LargeFile.fstat file).Unix.LargeFile.st_size in
    let digest,stats = SemanticFile.with_read_stats file (fun input ->
      ignore (SemanticFile.read input 2L 3);
      ignore (SemanticFile.read input 0L 0);
      SemanticFile.iter input 0L 65537L (fun _ _ -> ());
      SemanticFile.iter input 0L 0L (fun _ _ -> failwith "empty iteration callback");
      SemanticFile.digest input) in
    Unix.close file;
    check (digest=expected) "measurement changed digest";
    check (stats.SemanticFile.logical_bytes=Int64.add size 65540L) "logical read total";
    check (stats.chunks=Int64.add (Int64.div size 65536L) 3L && not stats.saturated)
      "logical chunk total");
  test "read failures and callback exceptions close readers without reporting success" (fun () ->
    let baseline=Array.length(Sys.readdir "/dev/fd") in
    let file=fd "sample" in
    let rejected = try ignore(SemanticFile.with_read_stats file (fun input ->
      ignore(SemanticFile.read input 0L 1);raise Exit));false with Exit -> true in
    check rejected "callback exception changed";
    let bad_read = try
      ignore(SemanticFile.with_read_stats file (fun input -> SemanticFile.read input 0L 1048577));false
      with SemanticFile.Invalid _ -> true in
    check bad_read "invalid measured read accepted";
    let size=(Unix.LargeFile.fstat file).Unix.LargeFile.st_size in
    let writer=Unix.openfile "sample" [Unix.O_WRONLY;Unix.O_CLOEXEC] 0 in
    let unstable = Fun.protect ~finally:(fun () ->
      Unix.LargeFile.ftruncate writer size;Unix.close writer) (fun () ->
      try ignore(SemanticFile.with_read_stats file (fun input ->
        ignore(SemanticFile.read input 0L 1);
        Unix.LargeFile.ftruncate writer (Int64.succ size)));false
      with SemanticFile.Invalid _ -> true) in
    Unix.close file;
    check unstable "unstable measured reader returned success";
    check (Array.length(Sys.readdir "/dev/fd")=baseline) "measured reader descriptor leak");
  test "worker read observer is opt-in owner-only exact and idle-bound" (fun () ->
    let b=budget 1 in let pool=W.create ~workers:1 ~max_pending:4 ~budget:b in
    let owner=Domain.self () and events=ref [] in
    ignore(Lwt_unix.run(hash pool (H.cancellation ()) "sample"));
    W.set_read_observer pool (Some(fun id stats ->
      check (Domain.self()=owner) "observer ran on worker";events:=(id,stats)::!events));
    let job=hash pool (H.cancellation ()) "sample" in
    check (try W.set_read_observer pool None;false with Invalid_argument _ -> true)
      "changed observer while pending";
    (match Lwt_unix.run job with Some value -> check(value.W.digest=expected) "measured hash changed"
     | None -> failwith "measured hash cancelled");
    check (List.length !events=1) "observer completion count";
    let _,stats=List.hd !events in
    check (stats.SemanticFile.logical_bytes=16777216L && stats.chunks=256L && not stats.saturated)
      "worker read total";
    W.set_read_observer pool None;
    ignore(Lwt_unix.run(hash pool (H.cancellation ()) "sample"));
    check(List.length !events=1) "disabled observer invoked";
    finish pool b);
  test "reply callback may disable future telemetry without losing its own report" (fun () ->
    let b=budget 1 in let pool=W.create ~workers:1 ~max_pending:4 ~budget:b in
    let reports=ref 0 in
    W.set_read_observer pool (Some(fun _ _ -> incr reports));
    ignore(Lwt_unix.run(hash pool (H.cancellation ()) "sample" >>= fun value ->
      W.set_read_observer pool None;return value));
    check(!reports=1) "reentrant observer change discarded completed read report";
    finish pool b);
  test "parallel measured jobs return exact independent owner reports" (fun () ->
    let b=budget 3 in let pool=W.create ~workers:4 ~max_pending:64 ~budget:b in
    let owner=Domain.self() and reports=ref [] in
    W.set_read_observer pool (Some(fun id stats ->
      check(Domain.self()=owner) "parallel observer ran on domain";
      reports:=(id,stats)::!reports));
    let jobs=List.init 48(fun _ -> hash pool (H.cancellation ()) "sample") in
    List.iter(function Some value -> check(value.W.digest=expected) "parallel measured hash changed"
      | None -> failwith "parallel measured job cancelled") (Lwt_unix.run(await jobs));
    check(List.length !reports=48) "parallel report count";
    check(List.length(List.sort_uniq Int.compare(List.map fst !reports))=48) "duplicate report ID";
    List.iter(fun (_,stats) ->
      check(stats.SemanticFile.logical_bytes=16777216L && stats.chunks=256L && not stats.saturated)
        "parallel report total") !reports;
    check((W.usage pool).peak_running<=3) "measured jobs bypassed CPU budget";
    finish pool b);
  test "throwing read observer leaves replies siblings and pool usable" (fun () ->
    let b=budget 1 in let pool=W.create ~workers:1 ~max_pending:4 ~budget:b in
    let once=ref false in
    W.set_read_observer pool (Some(fun _ _ -> if not !once then begin
      once:=true;failwith "synthetic read observer" end));
    let jobs=List.init 3(fun _ -> hash pool (H.cancellation ()) "sample") in
    let failed=try ignore(Lwt_unix.run(await jobs >>= fun _ -> Lwt_unix.sleep 0.03));false
      with Failure reason -> reason="synthetic read observer" in
    check failed "observer error disappeared";
    List.iter(function Some value -> check(value.W.digest=expected) "sibling changed"
      | None -> failwith "sibling cancelled") (Lwt_unix.run(await jobs));
    W.set_read_observer pool None;
    ignore(Lwt_unix.run(hash pool (H.cancellation ()) "sample"));finish pool b)
let shared_worker_parity () =
  let path="shared-parity.bin" in
  let data="SYN1" ^ String.init 60 (fun i -> Char.chr ((i*37+11) land 255)) in
  let output=open_out_bin path in output_string output data;close_out output;
  let source=fd path in
  let expected=SemanticFile.with_fd source (SemanticDelta.inspect (module Synthetic)) in
  Unix.close source;
  let extension=FormatExtension.trusted (module Synthetic) in
  List.iter (fun workers ->
    let descriptors=Array.length(Sys.readdir "/dev/fd") in
    let cpu=min workers 6 in
    let b=budget cpu in
    let pool=W.create ~workers ~max_pending:32 ~budget:b in
    let release=Lwt.wait () in
    let held=H.with_cpu_permits b ~weight:cpu (H.cancellation ()) (fun () -> release) in
    let jobs=List.init 16 (fun index ->
      let c=H.cancellation () in
      let result=if index mod 2=0 then
        hash pool c path >>= fun value ->
        return (Option.map (fun actual ->
          check(actual.W.digest=SemanticHash.string data) "configured-worker hash parity") value)
      else
        let input=fd path in
        try_bind (fun () -> W.inspect pool c ~extension input)
          (fun value -> Unix.close input;
            return (Option.map (fun actual ->
              check(match expected,actual.W.proof with
                | Ok a,Ok b -> SemanticDelta.describe a=SemanticDelta.describe b
                | _ -> false) "configured-worker proof parity") value))
          (fun error -> Unix.close input;fail error) in
      c,result,index mod 4=0) in
    check(H.usage b=(cpu,0) && (W.usage pool).running=0)
      "configured-worker queued jobs bypassed admission";
    List.iter (fun (c,_,cancel) -> if cancel then H.cancel c) (List.rev jobs);
    List.iter (fun (_,job,cancel) -> if cancel then
      check(Lwt_unix.run job=None) "configured-worker queued cancellation") jobs;
    Lwt.wakeup release ();
    Lwt_unix.run(held >>= fun _ -> return());
    let results=Lwt_unix.run(await(List.map(fun (_,job,_) -> job) jobs)) in
    List.iter2 (fun (_,_,cancel) result ->
      check((result=None)=cancel) "configured-worker cancellation parity") jobs results;
    check((W.usage pool).peak_running<=cpu) "configured-worker CPU bound";
    finish pool b;
    check(Array.length(Sys.readdir "/dev/fd")=descriptors)
      "configured-worker descriptor leak";
    Printf.printf "PASS shared parity workers=%d admitted_cpu=%d jobs=16 cancelled=4 completed=12\n%!"
      workers cpu) [1;2;4;8]
let cpu_hash_helper width =
  check (width>=1 && width<=2) "bounded helper width required";
  let payload=String.make 65536 'h' in
  let domains=List.init width(fun _ -> Domain.spawn (* TEST_HASH_SPAWN *) (fun () ->
    let result=ref "" in
    for _=1 to 32 do result:=SemanticHash.string payload done;
    !result)) in
  let values=List.map Domain.join domains in
  check(List.for_all((=)(SemanticHash.reference_string payload)) values)
    "child native hash differs from portable SHA reference";
  print_endline(SemanticHash.hex(List.hd values))

let shared_mixed_tests ?(cpu_helpers=false) () =
  let before = Array.length (Sys.readdir "/dev/fd") in
  let channel = open_out_bin "sample" in
  output_string channel (String.make 64 'm'); close_out channel;
  let file = fd "sample" in
  let expected = SemanticFile.with_fd file SemanticFile.digest in
  Unix.close file;
  List.iter (fun permits ->
    let b = budget permits in
    let pool = W.create ~workers:6 ~max_pending:32 ~budget:b in
    let helper weight =
      let group = ref None in
      H.run ~observe_group:(fun value -> group:=Some value) b ~weight (H.cancellation ())
        ~limits:{H.timeout=5.;terminate_grace=0.1;stdout_bytes=128;stderr_bytes=128}
        ~executable:(if cpu_helpers then Sys.executable_name else "/bin/sleep")
        ~arguments:(if cpu_helpers then [|"--cpu-hash-helper";string_of_int weight|] else [|"0.05"|])
        ~environment:[||]
      >>= fun result ->
        if cpu_helpers then check(result.H.stdout=
          SemanticHash.hex(SemanticHash.reference_string(String.make 65536 'h'))^"\n")
          "weighted child hash transcript differs";
        return (result,!group) in
    let first = helper 1 in
    let second = helper (min 2 permits) in
    let jobs = List.init 16 (fun _ -> hash pool (H.cancellation ()) "sample") in
    List.iter (function Some value -> check (value.W.digest=expected) "mixed hash parity"
      | None -> failwith "unexpected mixed hash cancellation") (Lwt_unix.run (await jobs));
    List.iter (fun (value,group) ->
        check (value.H.outcome=H.Completed && value.H.status=Some (Unix.WEXITED 0)) "mixed helper failed";
        check (group=Some (Some 0)) "mixed helper retained-group observation missing or nonzero";
        let pid=match value.H.child_pid with Some pid when pid>0 -> pid
          | _ -> failwith "mixed helper actual child identity missing" in
        Printf.printf "PASS shared mixed helper permits=%d pid=%d waited=0 observed-other-members=0\n%!" permits pid
      )
      (Lwt_unix.run (await [first;second]));
    let usage = W.usage pool in
    check (usage.peak_running <= permits) "mixed workers exceeded CPU budget";
    finish pool b;
    check (Array.length (Sys.readdir "/dev/fd")=before) "mixed helper/domain FD leak";
    Printf.printf "PASS shared mixed permits=%d hashes=16 helpers=2 settled\n%!" permits
  ) [1;2;4;6]

let () =
  if Array.length Sys.argv=3 && Sys.argv.(1)="--cpu-hash-helper" then
    (cpu_hash_helper(int_of_string Sys.argv.(2));exit 0);
  if Array.exists ((=) "--shared-mixed-hash-only") Sys.argv then
    (shared_mixed_tests ~cpu_helpers:true ();exit 0);
  if Array.exists ((=) "--shared-mixed-only") Sys.argv then (shared_mixed_tests ();exit 0);
  if Array.exists ((=) "--shared-parity-only") Sys.argv then (shared_worker_parity ();exit 0);
  if Array.exists ((=) "--read-stats-only") Sys.argv then (read_stats_tests ();exit 0);
  if Array.exists ((=) "--apply-stress-only") Sys.argv then (apply_scheduling_stress ();exit 0);
  if Array.exists ((=) "--stress-only") Sys.argv then (scheduling_stress ();exit 0);
  identify_tests ();
  if Array.exists ((=) "--identify-only") Sys.argv then exit 0;
  let expected = write_fixture () in
  test "18 actual domains, immutable digest parity and bounded concurrency" (fun () ->
    let b = budget 18 in
    let pool = W.create ~workers:18 ~max_pending:72 ~budget:b in
    let jobs = List.init 72 (fun _ -> hash pool (H.cancellation ()) "sample") in
    let results = Lwt_unix.run (await jobs) in
    List.iter (function Some f ->
      check (f.W.digest = expected && f.stats.Unix.LargeFile.st_size = 16777216L) "digest mismatch"
      | None -> failwith "unexpected cancellation") results;
    let u = W.usage pool in
    check (u.workers = 18 && u.peak_running > 1 && u.peak_running <= 18) "domain concurrency not bounded";
    finish pool b;
    Lwt_unix.run (W.shutdown pool);
    check (expect_failed (fun () -> hash pool (H.cancellation ()) "sample")) "closed pool accepted job");
  test "18 domains keep extended BigTIFF/CR proofs and exact materialization independent" (fun () ->
    let extension = FormatExtension.trusted ~observer:DngExtended.observer (module DngExtended) in
    let b = budget 18 in let pool = W.create ~workers:18 ~max_pending:36 ~budget:b in
    let inspect path =
      let file = fd path in
      try_bind (fun () -> W.inspect pool (H.cancellation ()) ~extension file)
        (fun result -> Unix.close file; return result)
        (fun error -> Unix.close file; fail error) in
    let sequential path =
      let file = fd path in
      let result = SemanticFile.with_fd file (SemanticDelta.inspect (module DngExtended)) in
      Unix.close file; match result with Ok proof -> proof | Error why -> failwith why in
    let base = sequential "extended-base.dng" and target = sequential "extended-target.dng" in
    let results = Lwt_unix.run (await (List.init 36 (fun i ->
      inspect (if i mod 2=0 then "extended-base.dng" else "extended-target.dng")))) in
    List.iteri (fun i -> function
      | Some result -> (match result.W.proof with
          | Ok proof -> check (SemanticDelta.describe proof =
              SemanticDelta.describe (if i mod 2=0 then base else target))
              "extended worker proof differs from sequential bytes/layout"
          | Error why -> failwith why)
      | None -> failwith "extended inspection cancelled") results;
    let plan = match SemanticDelta.plan ~nonce:(String.make 32 'e') ~base ~target with
      | Ok plan -> plan | Error why -> failwith why in
    let contents file = SemanticFile.read file 0L 1048576 ^
      SemanticFile.read file 1048576L 1048576 in
    let basis = fd "extended-base.dng" in
    let original = SemanticFile.with_fd basis contents in
    Unix.close basis;
    let jobs = List.init 18 (fun i ->
      let path = Printf.sprintf "extended-stage-%d.dng" i in
      let channel = open_out_bin path in output_string channel original; close_out channel;
      let basis = fd "extended-base.dng" in
      let output = Unix.openfile path [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
      try_bind (fun () -> W.apply_report pool (H.cancellation ()) ~extension plan ~basis ~output)
        (fun result ->
          let digest = SemanticFile.with_fd output SemanticFile.digest in
          Unix.close basis; Unix.close output;
          return (result,digest))
        (fun error -> Unix.close basis; Unix.close output; fail error)) in
    List.iter (function
      | Some report,digest ->
          check (report.SemanticDelta.logical_bytes_written=String.length "<x>two</x>      " &&
            report.write_calls=1 && digest=(SemanticDelta.describe target).digest)
            "extended worker output/report differs from target"
      | None,_ -> failwith "extended materialization cancelled") (Lwt_unix.run (await jobs));
    let file = fd "extended-base.dng" in
    check (SemanticFile.with_fd file contents=original)
      "extended workers changed their shared basis";
    Unix.close file;
    check ((W.usage pool).workers=18 && (W.usage pool).peak_running>1 &&
      (W.usage pool).peak_running<=18) "extended jobs did not use bounded domain concurrency";
    finish pool b);
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
  test "portable DNG observation matches the full sequential metadata transcript" (fun () ->
    let extension=FormatExtension.trusted ~observer:DngSemantic.observer (module DngSemantic) in
    let file=fd "observed.dng" in
    let proof=SemanticFile.with_fd file (SemanticDelta.inspect(module DngSemantic)) in
    Unix.close file;
    let reference=match proof with Ok proof -> SemanticDelta.observe ~extension proof
      | Error why -> failwith why in
    (match reference with Some(Ok observation) ->
      check(List.length observation.FormatExtension.properties=1) "reference observation lacks rating"
      | _ -> failwith "reference observation declined");
    let b=budget 6 in let pool=W.create ~workers:6 ~max_pending:48 ~budget:b in
    let jobs=List.init 48(fun _ ->
      let file=fd "observed.dng" in
      try_bind(fun () -> W.observe pool(H.cancellation()) ~extension file)
        (fun result -> Unix.close file;return result)
        (fun error -> Unix.close file;fail error)) in
    List.iter(function Some result ->
      check(result.W.meaning=reference) "worker metadata transcript changed";
      (match result.W.inspection.proof with Ok actual ->
        let expected=match proof with Ok p -> p | _ -> assert false in
        check(SemanticDelta.classify ~base:expected ~target:actual=FormatExtension.Exact_bytes)
          "worker observation byte proof changed" | Error why -> failwith why)
      | None -> failwith "worker observation cancelled") (Lwt_unix.run(await jobs));
    finish pool b);
  test "typed reconciliation plans are deterministic, bounded and cancellable" (fun () ->
    let extension=FormatExtension.trusted(module DngSemantic) in
    let proof path=let file=fd path in
      let result=SemanticFile.with_fd file(SemanticDelta.inspect(module DngSemantic)) in
      Unix.close file;match result with Ok p -> p | Error why -> failwith why in
    let base=proof "merge-base.dng" and left=proof "merge-left.dng" and right=proof "merge-right.dng" in
    let expected=SemanticDelta.describe(proof "merge-target.dng") in
    let b=budget 6 in let pool=W.create ~workers:6 ~max_pending:48 ~budget:b in
    let submit c=let file=fd "merge-left.dng" in
      try_bind(fun () -> W.reconcile_xmp pool c ~extension ~nonce:(String.make 32 'r') ~base ~left ~right file)
        (fun result -> Unix.close file;return result)
        (fun error -> Unix.close file;fail error) in
    let jobs=List.init 48(fun _ -> submit(H.cancellation())) in
    List.iter(function Some result -> (match result.W.merge_plan with
      | Ok plan -> check(SemanticDelta.target_digest plan=expected.SemanticDelta.digest)"worker merge target differs"
      | Error why -> failwith why) | None -> failwith "merge unexpectedly cancelled") (Lwt_unix.run(await jobs));
    let held=H.cancellation() in
    let reservation=H.with_cpu_permits b ~weight:6 held(fun ()->Lwt_unix.sleep 30.) in
    let cancel=H.cancellation() in let waiting=submit cancel in
    H.cancel cancel;check(Lwt_unix.run waiting=None)"queued reconciliation did not cancel";
    H.cancel held;ignore(Lwt_unix.run reservation);finish pool b);
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
