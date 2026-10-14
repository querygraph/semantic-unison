let passed = ref 0
let check name f = f (); incr passed; Printf.printf "PASS %s\n%!" name
let invalid f = try ignore (f ()); failwith "accepted invalid declaration"
  with Invalid_argument _ -> ()
let plan ?(cpu=1) ?(covered=0) ?(uncovered=0) ?(fd=0)
    ?(coverage=BackendResources.Accounting_only) () =
  BackendResources.make ~backend:"test/backend-v0" ~cpu_lanes:cpu
    ~covered_bytes:covered ~uncovered_estimate:uncovered
    ~descriptor_credits:fd ~coverage
module Recognition = struct
  let format = "test/backend-v0"
  let identify _ = FormatRecognition.Not_matched
end
module Validator = struct
  let recognition = FormatRecognition.trusted (module Recognition)
  let enabled = ref true
  let select () = if !enabled then Some (fun _ -> Lwt.return ()) else None
end
let () =
  check "overflow" (fun () -> invalid (fun () -> plan ~uncovered:max_int ~covered:1
    ~coverage:(BackendResources.Allocator_callbacks ["malloc"]) ()));
  check "negative estimate" (fun () -> invalid (fun () -> plan ~uncovered:(-1) ()));
  check "invalid CPU" (fun () -> invalid (fun () -> plan ~cpu:0 ()));
  check "invalid descriptors" (fun () -> invalid (fun () -> plan ~fd:65537 ()));
  check "accounting cannot claim enforcement" (fun () -> invalid (fun () -> plan ~covered:1 ()));
  check "duplicate allocation callbacks" (fun () -> invalid (fun () -> plan ~covered:1
    ~coverage:(BackendResources.Allocator_callbacks ["malloc";"malloc"]) ()));
  check "empty allocation callbacks" (fun () -> invalid (fun () -> plan ~covered:1
    ~coverage:(BackendResources.Allocator_callbacks []) ()));
  check "invalid callback identifier" (fun () -> invalid (fun () -> plan ~covered:1
    ~coverage:(BackendResources.Allocator_callbacks ["bad name"]) ()));
  check "zero address space" (fun () -> invalid (fun () -> plan
    ~coverage:BackendResources.Address_space ()));
  check "sequential component maxima" (fun () ->
    let p = BackendResources.maximum [plan ~cpu:6 ~uncovered:8 ~fd:2 ();
      plan ~cpu:1 ~covered:12 ~fd:9 ~coverage:BackendResources.Address_space ()] in
    assert (BackendResources.cpu_lanes p=6 && BackendResources.bytes p=12 &&
      BackendResources.descriptors p=9 && BackendResources.covered_bytes p=0 &&
      BackendResources.coverage p=BackendResources.Accounting_only));
  check "credit addition overflow" (fun () -> invalid (fun () ->
    BackendResources.add_cost (plan ~uncovered:1 ()) ~bytes:max_int ~descriptors:0));
  check "resource declarations frozen across disable/re-enable" (fun () ->
    let current = ref (plan ~uncovered:1024 ()) in
    let h = CandidateValidator.trusted ~resources:(fun () -> !current) (module Validator) in
    assert (Option.is_some (CandidateValidator.select h));
    assert (Option.is_some (CandidateValidator.select h));
    Validator.enabled := false; current := plan ~uncovered:2048 ();
    assert (CandidateValidator.select h=None);
    Validator.enabled := true;
    (try ignore (CandidateValidator.select h); failwith "accepted changed plan"
     with Util.Fatal _ -> ());
    current := plan ~uncovered:1024 ();
    assert (Option.is_some (CandidateValidator.select h)));
  check "held envelope rejects upgrades without callback or debit" (fun () ->
    let gate = SemanticAdmission.create ~source_headroom:None ~max_transactions:1
      ~max_payload_bytes:8192 ~max_descriptors:8 ~max_pending:4 in
    let cost = {SemanticAdmission.payload_bytes=4096;descriptors=4} in
    let r = SemanticAdmission.make_reservation gate ~role:SemanticAdmission.Consumer ~cost in
    assert (Lwt.poll (SemanticAdmission.acquire r (HelperSupervisor.cancellation ()))=Some true);
    let invoked = ref false in
    List.iter (fun cost ->
      (try ignore (Lwt.poll (SemanticAdmission.with_borrow r ~cost
        (fun () -> invoked := true; Lwt.return ()))); failwith "accepted oversized borrow"
       with SemanticAdmission.Failed _ -> ());
      assert (not !invoked);
      let u = SemanticAdmission.usage gate in
      assert (u.payload_bytes=4096 && u.descriptors=4 && u.transactions=1))
      [{SemanticAdmission.payload_bytes=4097;descriptors=4};
       {SemanticAdmission.payload_bytes=4096;descriptors=5}];
    assert (Lwt.poll (SemanticAdmission.with_borrow r ~cost (fun () -> Lwt.return ()))=Some ());
    SemanticAdmission.retire r;
    let u = SemanticAdmission.usage gate in
    assert (u.payload_bytes=0 && u.descriptors=0 && u.transactions=0));
  Printf.printf "PASSED %d resource controls\n%!" !passed
