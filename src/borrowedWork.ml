let guard ~on_setup_error work success failure =
  (* These owners and closures exist before [work] can dispatch a borrower.
     Assignment of its returned promise does not allocate. *)
  let returned = ref false and awaited = ref (Lwt.wait ())
  and first_error = ref Out_of_memory in
  let invoke () =
    let promise = work () in
    awaited := promise;
    returned := true;
    promise in
  let after_settlement _ = failure !first_error in
  let await () = !awaited in
  let rec poll_then_fail () =
    let settled =
      try match Lwt.poll !awaited with None -> false | Some _ -> true
      with _ -> true in
    if settled then failure !first_error
    else
      (* A timer/observer setup error must not escape this drain while the
         borrower sleeps. Finite failures retry; persistent allocation failure
         retains ownership but has no owner-loop responsiveness guarantee. *)
      try Lwt.try_bind delay resume_success resume_failure
      with _ -> poll_then_fail ()
  and delay () = Lwt_unix.sleep 0.01
  and resume_success () = poll_then_fail ()
  and resume_failure (_ : exn) = poll_then_fail () in
  let after_installation_error error =
    first_error := error;
    (try on_setup_error error with _ -> ());
    if not !returned then failure error
    else
      try Lwt.try_bind await after_settlement after_settlement
      with _ -> poll_then_fail () in
  try Lwt.try_bind invoke success failure
  with first_error -> after_installation_error first_error

let ignore_setup_error _ = ()
let try_bind work success failure =
  guard ~on_setup_error:ignore_setup_error work success failure

let bind work success = try_bind work success Lwt.fail
let catch work failure = try_bind work Lwt.return failure

let all ?(on_error=(fun _ -> ())) work =
  (* Allocate the ledger and every join/drain callback before the first launch.
     Once a thunk returns, storing its promise and incrementing [started] cannot
     allocate. A later launch or join error cannot lose earlier participants. *)
  let tasks = Array.of_list work in
  let count = Array.length tasks in
  let promises = Array.make count (Lwt.wait ()) in
  let started = ref 0 and failed = ref false and first_error = ref Out_of_memory
  and ready = ref true in
  let remember error =
    if not !failed then begin
      failed := true; first_error := error;
      (try on_error error with _ -> ())
    end in
  let finish () =
    if !failed then Lwt.fail !first_error
    else
      let results = ref [] in
      for index = !started - 1 downto 0 do
        match Lwt.poll promises.(index) with
        | Some value -> results := value :: !results
        | None -> assert false
      done;
      Lwt.return !results in
  let rec drain () =
    ready := true;
    for index = 0 to !started - 1 do
      try match Lwt.poll promises.(index) with
        | None -> ready := false
        | Some _ -> ()
      with error -> remember error
    done;
    if !ready then finish ()
    else
      try Lwt.try_bind delay resume_success resume_failure
      with error -> remember error; drain ()
  and delay () = Lwt_unix.sleep 0.01
  and resume_success () = drain ()
  and resume_failure error = remember error; drain () in
  let next = ref (fun _ -> assert false) in
  let invoke = Array.init count (fun index -> fun () -> promises.(index)) in
  let success = Array.init count (fun index -> fun _ -> !next (index + 1)) in
  let failure = Array.init count (fun index -> fun error ->
    remember error; !next (index + 1)) in
  let await index =
    if index = !started then finish ()
    else
      try guard ~on_setup_error:remember invoke.(index) success.(index) failure.(index)
      with error -> remember error; drain () in
  next := await;
  let launch () =
    for index = 0 to count - 1 do
      if not !failed then begin
        let promise = tasks.(index) () in
        promises.(index) <- promise;
        started := index + 1
      end
    done in
  try launch (); await 0
  with error -> remember error; drain ()
