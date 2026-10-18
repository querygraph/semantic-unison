let require yes reason=if not yes then failwith reason
let () =
 let empty=DomainOwner.prepare () in DomainOwner.join empty;
 require(DomainOwner.state empty=DomainOwner.Empty) "empty handle interpreted";
 let slots=Array.init 2 (fun _ -> DomainOwner.prepare ()) in
 let completed=Atomic.make 0 in
 for i=0 to 1 do
  let domain=Domain.spawn (* ox-safe-worker-spawn *) (fun () -> ignore(Atomic.fetch_and_add completed 1)) in
  let baseline_before=Gc.allocated_bytes () in
  ignore(Sys.opaque_identity ());
  let baseline_after=Gc.allocated_bytes () in
  let before=Gc.allocated_bytes () in
  DomainOwner.adopt slots.(i) domain;
  let after=Gc.allocated_bytes () in
  require(after -. before = baseline_after -. baseline_before) "adopt allocated after spawn";
  let refused=try DomainOwner.adopt slots.(i) domain;false with Invalid_argument _ -> true in
  require refused "duplicate transfer accepted"
 done;
 DomainOwner.join_all slots;DomainOwner.join_all slots;
 require(Atomic.get completed=2) "worker did not finish";
 Array.iter(fun slot -> require(DomainOwner.state slot=DomainOwner.Joined && DomainOwner.cause slot=None) "known join not recorded") slots;
 print_endline "PASS typed preallocated domain slots: empty/adopt/refusal/repeated known join"
