open Lwt
module W=SemanticWorkers
module H=HelperSupervisor
let checks=ref 0
let check yes message=incr checks;if not yes then failwith message
let empty=match DngComponents.freeze_decoders [] with Ok value -> value | Error why -> failwith why
let owner=Domain.self ()
let called=Atomic.make 0
let decoder : ComponentHash.plugin={id="original.worker-field/0";
 implementation_sha256=SemanticHash.string "original worker field implementation";
 decode=(fun reader ->
   if Domain.self ()=owner then failwith "decoder executed on Lwt owner";
   Atomic.incr called;ignore(ComponentHash.read reader 0L 1);
   Ok [{ComponentHash.id="dng/ifd/0/tag/50740/value/marker";
     schema="original-private-marker/0";role=Private_metadata;offset=0L;length=1L;children=[]}])}
let frozen=match DngComponents.freeze_decoders
 [{component_id="dng/ifd/0/tag/50740/value";decoder}] with Ok value -> value | Error why -> failwith why
let borrow pool cancel decoders limit path =
 let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 try_bind (fun () -> W.components pool cancel ~decoders ~max_read_bytes:limit fd)
   (fun result -> ignore(Unix.fstat fd);Unix.close fd;return result)
   (fun error -> Unix.close fd;fail error)
let summary = function
 | Some {W.components=Ok value;_} -> value
 | Some {W.components=Error why;_} -> failwith why
 | None -> failwith "unexpected cancellation"
let pixels value = List.assoc ComponentHash.Encoded_pixels value.W.projections
let budget n=H.create ~cpu_permits:n ~max_children:n ~max_pending:64
let finish pool b = Lwt_unix.run(W.shutdown pool);
 check (H.usage b=(0,0) && (W.usage pool).running=0 && (W.usage pool).pending=0) "unsettled worker/CPU"
let () =
 let baseline_fds=Array.length(Sys.readdir "/dev/fd") in
 let fd=Unix.openfile "fixture.dng" [Unix.O_RDONLY] 0 in
 let expected=SemanticFile.with_fd fd SemanticFile.digest in Unix.close fd;
 let b=budget 2 in let pool=W.create ~workers:2 ~max_pending:16 ~budget:b in
 let observations=ref [] in
 W.set_read_observer pool (Some(fun _ reads ->
   check (Domain.self ()=owner) "read observer executed off owner";
   observations:=reads::!observations));
 let baseline=summary(Lwt_unix.run(borrow pool (H.cancellation()) empty 8192L "fixture.dng")) in
 check (baseline.full_sha256=expected && baseline.hash_bytes_requested=8192L) "baseline component hash differs";
 check(baseline.checkpoint=None) "ordinary observation exported persistent metadata";
 let jobs=List.init 12 (fun _ -> borrow pool (H.cancellation()) frozen 8321L "fixture.dng") in
 let rec join = function [] -> return [] | job::rest -> job >>= fun value -> join rest >>= fun values -> return(value::values) in
 let results=Lwt_unix.run(join jobs) in
 List.iter(fun result -> let value=summary result in
   check(value.full_sha256=expected && value.hash_bytes_requested=8321L) "component result differs";
   check(pixels value=pixels baseline && pixels value<>None) "pixel projection changed";
   check(List.map(fun (o:DngComponents.outcome) -> o.status) value.refinements=[DngComponents.Refined])
     "frozen decoder result missing") results;
 check(Atomic.get called=12) "decoder call count";
 check(List.length !observations=13) "read observer report count";
 List.iter(fun (reads:SemanticFile.read_stats) ->
   check(not reads.saturated && (reads.logical_bytes=8280L || reads.logical_bytes=8409L))
     "geometry/component delivered reads differ") !observations;
 let unsupported=Lwt_unix.run(borrow pool (H.cancellation()) empty 8192L "unsupported.bin") in
 check(match unsupported with Some {W.components=Error _;_}->true | _->false) "unsupported format mislabeled";
 check(try ignore(Lwt_unix.run(borrow pool (H.cancellation()) frozen 8192L "fixture.dng"));false
   with W.Failed _ -> true) "operational budget failure became unsupported";
 check(H.usage b=(0,0) && (W.usage pool).running=0) "failed job released early or leaked";
 check((summary(Lwt_unix.run(borrow pool (H.cancellation()) empty 8192L "fixture.dng"))).full_sha256=expected)
   "pool failed to recover";
 W.set_read_observer pool None;
 let fd=Unix.openfile "fixture.dng" [Unix.O_RDONLY] 0 in
 let encoded,digest=SemanticFile.with_fd fd (fun file ->
   match DngComponents.with_snapshot ~decoders:empty ~max_read_bytes:8192L file
     (fun session ~initial:_ ~refined _ ->
       let checkpoint=ComponentHash.checkpoint session refined in
       ComponentHash.checkpoint_bytes checkpoint,ComponentHash.checkpoint_sha256 checkpoint) with
   | Ok value -> value | Error why -> failwith why) in
 let restored=summary(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:digest ~encoded ~max_read_bytes:8192L fd)) in
 check(restored.full_sha256=baseline.full_sha256 && restored.layout_sha256=baseline.layout_sha256 &&
   restored.projections=baseline.projections) "worker restore changed cached identities";
 check(restored.refinements=[] && restored.hash_bytes_requested=8192L)
   "worker restore fabricated decoder approval or skipped input verification";
 check(restored.checkpoint=None) "restore silently recaptured historical metadata";
 let captured=summary(Lwt_unix.run(W.components pool (H.cancellation()) ~capture_checkpoint:true
   ~decoders:frozen ~max_read_bytes:8321L fd)) in
 let checkpoint=match captured.checkpoint with Some value -> value | None -> failwith "worker capture absent" in
 check(captured.hash_bytes_requested=8321L) "checkpoint export reread input";
 let from_capture=summary(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:(ComponentHash.checkpoint_sha256 checkpoint)
   ~encoded:(ComponentHash.checkpoint_bytes checkpoint) ~max_read_bytes:8192L fd)) in
 check(from_capture.layout_sha256=captured.layout_sha256 && from_capture.projections=captured.projections)
   "live worker capture did not restore its private view";
 let refresh decoders limit=summary(Lwt_unix.run(W.refresh_components pool (H.cancellation())
   ~previous:captured.refinements ~decoders ~capture_checkpoint:true
   ~expected_checkpoint_sha256:(ComponentHash.checkpoint_sha256 checkpoint)
   ~encoded:(ComponentHash.checkpoint_bytes checkpoint) ~max_read_bytes:limit fd)) in
 let before=Atomic.get called in
 let retained=refresh frozen 8192L in
 check(retained.layout_sha256=captured.layout_sha256 && retained.hash_bytes_requested=8192L &&
   retained.reused_components=["dng/ifd/0/tag/50740/value"] && retained.invalidated_components=[])
   "worker failed to retain unchanged decoder view";
 check(Atomic.get called=before && retained.checkpoint<>None)
   "unchanged worker refresh ran decoder or omitted requested capture";
 let upgraded=match DngComponents.freeze_decoders
   [{component_id="dng/ifd/0/tag/50740/value";
     decoder={decoder with implementation_sha256=SemanticHash.string "worker-upgrade/2"}}] with
   | Ok value -> value | Error why -> failwith why in
 let upgraded=refresh upgraded 8321L in
 check(upgraded.layout_sha256<>captured.layout_sha256 && pixels upgraded=pixels captured &&
   upgraded.reused_components=[] && upgraded.invalidated_components=["dng/ifd/0/tag/50740/value"])
   "worker upgrade failed localized invalidation";
 check(Atomic.get called=before+1 && upgraded.hash_bytes_requested=8321L && upgraded.checkpoint<>None)
   "worker upgrade decoder count/budget/capture mismatch";
 check(try ignore(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:(String.make 32 'X') ~encoded ~max_read_bytes:8192L fd));false
   with W.Failed _ -> true) "worker accepted untrusted checkpoint";
 check(H.usage b=(0,0) && (W.usage pool).running=0 &&
   (Unix.fstat fd).Unix.st_kind=Unix.S_REG) "restore failure leaked budget or closed borrowed FD";
 check(try ignore(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:digest ~encoded ~max_read_bytes:8191L fd));false
   with W.Failed _ -> true) "under-budget restore accepted";
 let changed=Unix.openfile "changed.dng" [Unix.O_RDONLY] 0 in
 check(try ignore(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:digest ~encoded ~max_read_bytes:8192L changed));false
   with W.Failed _ -> true) "changed input reused cached worker hashes";
 Unix.close changed;
 Unix.close fd;finish pool b;
 let b=budget 1 in let io=IoAdmission.create ~per_device:1 ~max_pending:4 in
 let pool=W.create_with_io ~io ~workers:1 ~max_pending:4 ~budget:b in
 let restore_reads=ref 0 in
 W.set_read_observer pool (Some(fun _ _ -> incr restore_reads));
 let restore_fd=Unix.openfile "fixture.dng" [Unix.O_RDONLY] 0 in
 let release=Lwt.wait () in
 let held=H.with_cpu_permits b ~weight:1 (H.cancellation()) (fun () -> release) in
 let cancel=H.cancellation() in let waiting=borrow pool cancel empty 8192L "fixture.dng" in
 H.cancel cancel;
 check(Lwt_unix.run waiting=None) "queued cancellation delivered component data";
 let cancel=H.cancellation() in
 let waiting=W.restore_components pool cancel ~expected_checkpoint_sha256:digest ~encoded
   ~max_read_bytes:8192L restore_fd in
 H.cancel cancel;
 check(Lwt_unix.run waiting=None && !restore_reads=0)
   "queued restore cancellation read input or delivered stale data";
 Lwt.wakeup release ();Lwt_unix.run held;
 check((IoAdmission.usage io).active_jobs=0) "cancelled component job retained IO gate";
 let restored=summary(Lwt_unix.run(W.restore_components pool (H.cancellation())
   ~expected_checkpoint_sha256:digest ~encoded ~max_read_bytes:8192L restore_fd)) in
 check(restored.full_sha256=expected && !restore_reads=1)
   "restore failed to recover through filesystem gate";
 check(H.usage b=(0,0) && (IoAdmission.usage io).active_jobs=0)
   "restore retained filesystem/CPU admission";
 Unix.close restore_fd;W.set_read_observer pool None;
 check((summary(Lwt_unix.run(borrow pool (H.cancellation()) empty 8192L "fixture.dng"))).full_sha256=expected)
   "component job failed through filesystem gate";
 check(H.usage b=(0,0) && (IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).pending=0)
   "successful component job retained filesystem/CPU admission";
 let original=Unix.openfile "fixture.dng" [Unix.O_RDONLY] 0 in
 check(try ignore(W.components pool (H.cancellation()) ~decoders:empty ~max_read_bytes:(-1L) original);false
   with Invalid_argument _ -> true) "negative public read budget admitted";
 check((W.usage pool).pending=0 && (Unix.fstat original).Unix.st_kind=Unix.S_REG)
   "negative admission borrowed caller descriptor";
 List.iter(fun (sha,bytes,limit) ->
   check(try ignore(W.restore_components pool (H.cancellation())
     ~expected_checkpoint_sha256:sha ~encoded:bytes ~max_read_bytes:limit original);false
     with Invalid_argument _ -> true) "invalid restore envelope admitted";
   check((W.usage pool).pending=0 && (Unix.fstat original).Unix.st_kind=Unix.S_REG)
     "restore preentry refusal borrowed caller descriptor")
   [("bad",encoded,8192L);(digest,encoded,-1L);
    (digest,String.make(ComponentHash.max_checkpoint_size+1) 'x',8192L)];
 Unix.close original;
 finish pool b;
 let b=budget 1 in let pool=W.create ~workers:1 ~max_pending:4 ~budget:b in
 let before=Atomic.get called in
 let cancel=H.cancellation() in let completed=borrow pool cancel frozen 8321L "fixture.dng" in
 let deadline=Unix.gettimeofday()+.5. in
 while (Atomic.get called=before || (W.usage pool).running<>0) && Unix.gettimeofday()<deadline do
   ignore(Unix.select [] [] [] 0.001)
 done;
 check(Atomic.get called>before && (W.usage pool).running=0) "worker did not finish before owner delivery";
 check(H.usage b=(1,0) && (W.usage pool).pending=1) "completed result released credits before owner delivery";
 H.cancel cancel;check(Lwt_unix.run completed=None) "late cancellation delivered stale components";
 finish pool b;
 let b=budget 1 in let pool=W.create ~workers:1 ~max_pending:4 ~budget:b in
 let before=Atomic.get called in
 let closing=borrow pool (H.cancellation()) frozen 8321L "fixture.dng" in
 let deadline=Unix.gettimeofday()+.5. in
 while (Atomic.get called=before || (W.usage pool).running<>0) && Unix.gettimeofday()<deadline do
   ignore(Unix.select [] [] [] 0.001)
 done;
 check(Atomic.get called>before && (W.usage pool).running=0) "shutdown control did not complete before owner";
 Lwt_unix.run(W.shutdown pool);
 check(Lwt_unix.run closing=None) "shutdown delivered completed component result";
 check(H.usage b=(0,0) && (W.usage pool).pending=0 && (W.usage pool).running=0) "shutdown retained component budget";
 check(Array.length(Sys.readdir "/dev/fd")=baseline_fds) "component lifecycle leaked descriptor";
 Printf.printf "PASS %d component worker checks; parallel parity, off-owner refinement, read reporting, failure and queued/late cancellation\n%!" !checks
