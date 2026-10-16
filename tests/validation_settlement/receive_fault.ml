(* Appended to private Lwt implementation/interface by receive.py. These
   controls never decode production values or substitute work. *)
let validation_test_env key = match Sys.getenv_opt key with Some text -> text | None -> ""
let validation_test_owned () = validation_test_env "UNISON_VALIDATION_TEST_OWNED"
let validation_test_phase () = validation_test_env "UNISON_VALIDATION_TEST_PHASE"
let validation_test_log fields =
  let path = validation_test_env "UNISON_VALIDATION_TEST_TRACE" in
  if path <> "" then begin
    let channel = open_out_gen [Open_wronly;Open_creat;Open_append;Open_binary] 0o600 path in
    Fun.protect ~finally:(fun () -> close_out channel)
      (fun () -> output_string channel (String.concat "\t" fields ^ "\n"))
  end
let validation_test_ready () =
  let directory = validation_test_owned () in
  if directory = "" then [] else
  Array.fold_left (fun entries name ->
    if Filename.check_suffix name ".ready" then
      let channel = open_in (Filename.concat directory name) in
      let path = Fun.protect ~finally:(fun () -> close_in channel) (fun () -> input_line channel) in
      (int_of_string (Filename.chop_suffix name ".ready"),path) :: entries
    else entries) [] (Sys.readdir directory)
let validation_test_workers () =
  let directory=validation_test_owned () in
  if directory="" then [] else Array.to_list (Sys.readdir directory) |>
    List.filter (fun name -> Filename.check_suffix name ".worker" &&
      not (Sys.file_exists (Filename.concat directory (name ^ ".done"))))
let validation_test_barrier : (int -> unit) ref = ref (fun _ -> ())
let validation_test_set_barrier barrier = validation_test_barrier := barrier
let validation_test_target : Obj.t option ref = ref None
let validation_test_attempts = ref 0
let validation_test_launches = ref 0
let validation_test_watch phase path promise =
  if validation_test_phase () = phase && !validation_test_target = None then begin
    validation_test_target := Some (Obj.repr promise);
    validation_test_log ["watch";phase;path]
  end;
  promise
let validation_test_consume path work () =
  incr validation_test_launches;
  if validation_test_phase () = "directory-launch" && !validation_test_launches = 3 then begin
    !validation_test_barrier 2;
    validation_test_log ["injected";"directory-launch";"Primary_waiter"];
    raise (Failure "validation-test Primary_waiter")
  end;
  validation_test_watch "directory-join" path (work ())
let validation_test_waiter promise = match !validation_test_target with
  | Some target when target == promise ->
      incr validation_test_attempts;
      if !validation_test_attempts <= 2 then begin
        !validation_test_barrier (if validation_test_phase () = "directory-join" then 2 else 1);
        let error = if !validation_test_attempts = 1 then "Primary_waiter" else "Secondary_waiter" in
        validation_test_log ["injected";validation_test_phase ();error];
        raise (Failure ("validation-test " ^ error))
      end
  | _ -> ()
