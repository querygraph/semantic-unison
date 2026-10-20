(* Original deterministic fake close operations; no OS descriptors are closed. *)
let attempts=ref []
let failing=ref []
exception Injected of int
module Ownership=OwnedClose.Make(struct
  type descriptor = int
  let empty = 0
  let close number =
    attempts := number :: !attempts;
    if List.mem number !failing then raise (Injected number)
end)
let fd n = n
let reset () = attempts:=[];failing:=[]
let expect_invalid f = try f ();failwith "accepted invalid adoption" with Invalid_argument _ -> ()
let () =
  reset ();
  let a=Ownership.prepare ~label:"input" and b=Ownership.prepare ~label:"output" in
  let group=Ownership.group [|a;b|] in
  Ownership.adopt a (fd 101);Ownership.adopt b (fd 102);
  expect_invalid (fun () -> Ownership.adopt a (fd 103));
  failing:=[101;102];
  let error=try Ownership.close_all group;failwith "uncertainty released" with error -> error in
  assert(Ownership.owns_exception group error);
  assert(not(Ownership.settled group));
  assert(Ownership.state a=Ownership.Uncertain && Ownership.state b=Ownership.Uncertain);
  assert(Ownership.cause a=Some(Injected 101) && Ownership.cause b=Some(Injected 102));
  assert(List.sort compare !attempts=[101;102]);
  (* Simulate numeric reuse: a retry must not touch the new descriptor. *)
  failing:=[];attempts:=[];
  let second=try Ownership.close_all group;failwith "uncertainty cleared" with error -> error in
  assert(error==second && !attempts=[]);
  reset ();
  let c=Ownership.prepare ~label:"known" and d=Ownership.prepare ~label:"unused" in
  let known=Ownership.group [|c;d|] in
  Ownership.adopt c (fd 104);Ownership.close_all known;Ownership.close_all known;
  assert(Ownership.settled known && !attempts=[104] && Ownership.state d=Ownership.Empty);
  expect_invalid (fun () -> Ownership.adopt c (fd 105));
  let e=Ownership.prepare ~label:"not grouped" in
  expect_invalid (fun () -> Ownership.adopt e (fd 106));
  expect_invalid (fun () -> ignore(Ownership.group [|e;e|]));
  let independent=Ownership.group [|e|] in
  assert(not(Ownership.owns_exception independent error));
  expect_invalid (fun () -> ignore(Ownership.group [|e|]));
  print_endline "PASS combined close uncertainty/no numeric retry/settled idempotence/empty and unique ownership"
