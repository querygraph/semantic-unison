type entry = {
  mutable actual_cause:exn;
  mutable reported:exn;
  mutable classifier_cause:exn;
  mutable classifier_failed:bool;
  mutable pending:bool;
  mutable registered:bool;
  mutable previous:entry option;
  keepalive:unit -> bool;
}
let roots = ref None
let retained_count = ref 0
let count () = !retained_count
let iter f =
  let rec loop = function
    | None -> ()
    | Some entry -> f entry; loop entry.previous in
  loop !roots
let cause entry = entry.actual_cause
let reported_error entry = entry.reported
let classification_error entry =
  if entry.classifier_failed then Some entry.classifier_cause else None
let borrowed_pending entry = entry.pending
let reply_sleeping entry = entry.keepalive ()
let guard ~is_uncertain ?(on_retained=(fun _ -> ())) work =
  let pending = Lwt.wait () in
  let returned = ref false and borrowed = ref (Lwt.wait ())
  and uncertain = ref false in
  let keepalive () =
    (* Keep both the actual borrower and unresolved reply reachable. Polling
       is diagnostic only and never supplies close/release authority. *)
    let sleeping = if !returned then
      try Lwt.poll !borrowed = None with _ -> false else false in
    let retained = try Lwt.poll pending = None with _ -> false in
    sleeping || retained in
  let entry = {actual_cause=Out_of_memory;reported=Out_of_memory;
    classifier_cause=Out_of_memory;classifier_failed=false;pending=false;
    registered=false;previous=None;keepalive} in
  (* The option cell is also allocated before work can acquire anything. *)
  let cell = Some entry in
  let retain () =
    if not entry.registered then begin
      entry.previous <- !roots;
      roots := cell;
      entry.registered <- true;
      if !retained_count < max_int then incr retained_count;
      (try on_retained entry with _ -> ())
    end;
    pending in
  let classify error =
    try is_uncertain error with failure ->
      entry.classifier_cause <- failure;
      entry.classifier_failed <- true;
      true in
  let failure error =
    entry.reported <- error;
    entry.actual_cause <- error;
    uncertain := classify error;
    if !returned then begin
      try match Lwt.poll !borrowed with
        | None -> entry.pending <- true; uncertain := true
        | Some _ -> ()
      with actual ->
        entry.actual_cause <- actual;
        (* Do not short circuit: preserve a classifier failure on either cause. *)
        let actual_uncertain = classify actual in
        uncertain := !uncertain || actual_uncertain
    end;
    if !uncertain then retain () else Lwt.fail error in
  let invoke () =
    let promise = work () in
    borrowed := promise;
    returned := true;
    promise in
  BorrowedWork.try_bind invoke Lwt.return failure
