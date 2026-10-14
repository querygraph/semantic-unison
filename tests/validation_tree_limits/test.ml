let checks = ref 0
let check b = incr checks; assert b
let rejected f = try f (); failwith "accepted over-budget tree"
  with ValidationTreeBudget.Exceeded _ -> ()
let () =
  let t = ValidationTreeBudget.create ~max_entries:2 ~max_path_bytes:10 in
  ValidationTreeBudget.reserve t ~prefix_bytes:0 ~name_bytes:4;
  ValidationTreeBudget.reserve t ~prefix_bytes:4 ~name_bytes:2;
  check (ValidationTreeBudget.usage t=(2,10));
  rejected (fun () -> ValidationTreeBudget.reserve t ~prefix_bytes:0 ~name_bytes:0);
  check (ValidationTreeBudget.usage t=(2,10));
  let b = ValidationTreeBudget.create ~max_entries:0 ~max_path_bytes:4 in
  ValidationTreeBudget.reserve b ~prefix_bytes:0 ~name_bytes:4;
  rejected (fun () -> ValidationTreeBudget.reserve b ~prefix_bytes:0 ~name_bytes:1);
  check (ValidationTreeBudget.usage b=(1,4));
  let u = ValidationTreeBudget.create ~max_entries:0 ~max_path_bytes:0 in
  ValidationTreeBudget.reserve u ~prefix_bytes:max_int ~name_bytes:0;
  rejected (fun () -> ValidationTreeBudget.reserve u ~prefix_bytes:0 ~name_bytes:1);
  check (ValidationTreeBudget.usage u=(1,max_int));
  (try ignore (ValidationTreeBudget.create ~max_entries:(-1) ~max_path_bytes:0);
    failwith "accepted negative limit" with Invalid_argument _ -> incr checks);
  (try ValidationTreeBudget.reserve u ~prefix_bytes:(-1) ~name_bytes:1;
    failwith "accepted negative path length" with Invalid_argument _ -> incr checks);
  check (ValidationTreeBudget.usage u=(1,max_int));
  let paths = ValidationTreeBudget.create ~max_entries:0 ~max_path_bytes:9 in
  rejected (fun () -> ValidationTreeBudget.reserve paths ~prefix_bytes:8 ~name_bytes:2);
  check (ValidationTreeBudget.usage paths=(0,0));
  Printf.printf "PASS validation tree arithmetic/boundaries: %d checks\n" !checks
