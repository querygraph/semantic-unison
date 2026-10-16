module A = SemanticAdmission
module H = HelperSupervisor
let check v s = if not v then failwith s
let source : A.cost = {payload_bytes=134479872;descriptors=8}
let consumer : A.cost = {payload_bytes=2281963520;descriptors=24}
let gate mib fds = A.create ~source_headroom:(Some source) ~max_transactions:4
  ~max_payload_bytes:(mib*1048576) ~max_descriptors:fds ~max_pending:4
let take t role cost =
 let r=A.make_reservation t ~role ~cost in
 check (Lwt_unix.run (A.acquire r (H.cancellation ()))) "acquire cancelled";r
let empty t = let u=A.usage t in check (u.transactions=0 && u.pending=0 && u.payload_bytes=0 && u.descriptors=0) "credits leaked"
let () =
 let t=gate 6144 64 in
 let a=take t A.Consumer consumer in
 let b=take t A.Consumer consumer in
 let s=take t A.Source source in
 let u=A.usage t in
 check (u.transactions=3 && u.payload_bytes=4698406912 && u.descriptors=56) "actual source/two consumers differ";
 List.iter A.retire [s;b;a];empty t;
 Printf.printf "PASS two consumers plus source held simultaneously at6GiB/64FD\n%!";
 List.iter (fun (mib,fds) ->
  let t=gate mib fds in
  let a=take t A.Consumer consumer in
  let b=A.make_reservation t ~role:A.Consumer ~cost:consumer in
  let cancel=H.cancellation () in
  let pending=A.acquire b cancel in
  check (not (A.is_held b) && (A.usage t).pending=1) "second consumer should queue";
  H.cancel_and_cleanup cancel;
  check (not (Lwt_unix.run pending)) "cancelled consumer admitted";
  A.retire b;A.retire a;empty t;
  Printf.printf "PASS insufficient gate%dMiB/%dFD queues then cancels second consumer\n%!" mib fds)
 [4096,64;6144,55]
