let try_bind work success failure =
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
    if not !returned then failure error
    else
      try Lwt.try_bind await after_settlement after_settlement
      with _ -> poll_then_fail () in
  try Lwt.try_bind invoke success failure
  with first_error -> after_installation_error first_error
