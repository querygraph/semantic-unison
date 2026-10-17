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
 W.set_read_observer pool None;finish pool b;
 let b=budget 1 in let io=IoAdmission.create ~per_device:1 ~max_pending:4 in
 let pool=W.create_with_io ~io ~workers:1 ~max_pending:4 ~budget:b in
 let release=Lwt.wait () in
 let held=H.with_cpu_permits b ~weight:1 (H.cancellation()) (fun () -> release) in
 let cancel=H.cancellation() in let waiting=borrow pool cancel empty 8192L "fixture.dng" in
 H.cancel cancel;
 check(Lwt_unix.run waiting=None) "queued cancellation delivered component data";
 Lwt.wakeup release ();Lwt_unix.run held;
 check((IoAdmission.usage io).active_jobs=0) "cancelled component job retained IO gate";
 check((summary(Lwt_unix.run(borrow pool (H.cancellation()) empty 8192L "fixture.dng"))).full_sha256=expected)
   "component job failed through filesystem gate";
 check(H.usage b=(0,0) && (IoAdmission.usage io).active_jobs=0 && (IoAdmission.usage io).pending=0)
   "successful component job retained filesystem/CPU admission";
 let original=Unix.openfile "fixture.dng" [Unix.O_RDONLY] 0 in
 check(try ignore(W.components pool (H.cancellation()) ~decoders:empty ~max_read_bytes:(-1L) original);false
   with Invalid_argument _ -> true) "negative public read budget admitted";
 check((W.usage pool).pending=0 && (Unix.fstat original).Unix.st_kind=Unix.S_REG)
   "negative admission borrowed caller descriptor";
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
