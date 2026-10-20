module Make (Ownership : sig
  type group
  val close_all : group -> unit
  val settled : group -> bool
end) = struct
  type 'a t = {group:Ownership.group; reply:'a Lwt.t;
               mutable finished:bool; mutable outcome:('a,exn) result;
               mutable close_failed:bool; mutable close_error:exn}
  let prepare group = {group;reply=Lwt.wait ();finished=false;outcome=Error Exit;
                       close_failed=false;close_error=Exit}
  let promise t = t.reply
  let retained t = t.finished && not (Ownership.settled t.group)
  let operation_outcome t = t.outcome
  let close_failure t = if t.close_failed then Some t.close_error else None
  let finish t outcome =
    if t.finished then invalid_arg "borrowed close completion repeated";
    t.finished <- true;
    t.outcome <- outcome;
    (try Ownership.close_all t.group
     with error -> t.close_error <- error; t.close_failed <- true);
    if Ownership.settled t.group then
      if t.close_failed then Lwt.wakeup_exn t.reply t.close_error
      else match t.outcome with
        | Ok value -> Lwt.wakeup t.reply value
        | Error error -> Lwt.wakeup_exn t.reply error
end
