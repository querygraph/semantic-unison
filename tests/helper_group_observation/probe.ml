(* Original finite owned-child fixture. Never a source-photo/SDK invocation. *)
type owner
external create : unit -> owner = "unsn_helper_group_owner_create"
external retire : owner -> unit = "unsn_helper_group_owner_retire"
external spawn : string -> string array -> string array -> Unix.file_descr -> Unix.file_descr -> owner -> int
  = "unsn_helper_spawn_group_owned_bytecode" "unsn_helper_spawn_group_owned"
external terminal : int -> bool = "unsn_helper_exited_unreaped"
external observe : owner -> int = "unsn_helper_retained_group_others"
let helper = Sys.argv.(1)
let check yes message = if not yes then failwith message
let sleep () = ignore (Unix.select [] [] [] 0.005)
let until f =
  let deadline = Unix.gettimeofday () +. 3. in
  while not (f ()) do
    if Unix.gettimeofday () > deadline then failwith "owned fixture deadline";
    sleep ()
  done
let with_child args f =
  let owner = create () in
  let rd,wr = Unix.pipe ~cloexec:true () in
  let null = Unix.openfile "/dev/null" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
  let pid = try
    spawn helper (Array.append [|helper|] args) (Unix.environment ()) wr null owner
    with error -> Unix.close rd; Unix.close wr; Unix.close null; raise error in
  Unix.close wr; Unix.close null;
  let input = Unix.in_channel_of_descr rd and owned = ref true in
  let reap ?(retire_owner=true) () =
    if retire_owner then retire owner; let _,status = Unix.waitpid [] pid in owned := false; status in
  let cleanup () =
    close_in_noerr input;
    if !owned then begin
      (* No previous waitpid in this fixture releases the reservation without
         clearing owned. Never signal after reap, even on assertion failure. *)
      (try Unix.kill (-pid) Sys.sigkill
       with Unix.Unix_error ((Unix.ESRCH|Unix.EPERM),_,_) -> ());
      ignore (reap ())
    end in
  match f owner pid input reap with
  | () -> cleanup ()
  | exception error -> cleanup (); raise error
let rejected expected f =
  try ignore (f ()); false with Unix.Unix_error (error,_,_) -> error = expected
let () =
  if Array.length Sys.argv > 2 then begin
    let expected = if Sys.argv.(2) = "ENOMEM" then Unix.ENOMEM else Unix.EIO in
    with_child [|"identity"|] (fun owner pid input reap ->
      ignore(input_line input); until(fun () -> terminal pid);
      check (rejected expected (fun () -> observe owner)) "observation error became empty success";
      check (reap () = Unix.WEXITED 0) "failed observation lost owned child");
    print_endline "PASS injected observation failure refuses zero and preserves exact owned reap";
    exit 0
  end;
  check (try ignore(observe(create()));false with Invalid_argument _ -> true) "unspawned owner accepted";
  let unused = create () in retire unused;
  check (try ignore(observe unused);false with Invalid_argument _ -> true) "retired owner accepted";
  with_child [|"identity"|] (fun owner pid input reap ->
    check (int_of_string (input_line input) = pid) "spawn identity differs";
    until (fun () -> terminal pid);
    Gc.full_major (); Gc.compact ();
    check (observe owner = 0 && observe owner = 0) "lone retained leader not observed";
    check (try ignore(Marshal.to_string owner []);false with Invalid_argument _ -> true)
      "owner binding was serializable";
    let null = Unix.openfile "/dev/null" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
    let reused = try ignore(spawn helper [|helper;"identity"|] [||] null null owner);false
      with Invalid_argument _ -> true in
    Unix.close null; check reused "spawn binding reused";
    check (reap () = Unix.WEXITED 0) "observer reaped or changed status";
    check (try ignore(observe owner);false with Invalid_argument _ -> true) "retired binding accepted");
  print_endline "PASS retained leader zero, repeat observation, real status and post-reap refusal";
  with_child [|"pid-wait"|] (fun owner pid input reap ->
    check (int_of_string (input_line input) = pid) "running identity differs";
    check (rejected Unix.EBUSY (fun () -> observe owner)) "running leader certified";
    Unix.kill pid Sys.sigterm;
    until (fun () -> terminal pid);
    check (observe owner = 0) "terminated retained leader not observed";
    ignore (reap ()));
  print_endline "PASS running child rejected before observing terminated owned group";
  print_endline "PASS unspawned/retired bindings cannot certify a group";
  with_child [|"identity"|] (fun owner pid input reap ->
    ignore(input_line input); until(fun () -> terminal pid);
    check (reap ~retire_owner:false () = Unix.WEXITED 0) "external-reap fixture status";
    check (rejected Unix.ECHILD (fun () -> observe owner)) "lost direct-child ownership certified";
    retire owner);
  print_endline "PASS external reap cannot produce a fresh group observation";
  let marker = Filename.concat (Sys.getcwd ()) "descendant-marker" in
  with_child [|"descendant";marker|] (fun owner pid input reap ->
    ignore(int_of_string(input_line input)); until(fun () -> terminal pid);
    check (observe owner > 0) "live descendant missing from observation";
    Unix.kill (-pid) Sys.sigkill;
    until(fun () -> observe owner = 0);
    check (reap () = Unix.WEXITED 0) "leader status changed";
    ignore(Unix.select [] [] [] 0.5);
    check (not(Sys.file_exists marker)) "descendant survived group cleanup");
  print_endline "PASS descendant present then absent while exact leader remains unreaped"
