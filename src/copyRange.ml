type progress = { requested : int64; completed : int64 }
type system_error = {
  errno : Unix.error;
  operation : string;
  argument : string;
}
type failure =
  | System_error of system_error
  | No_progress
  | Invalid_progress of { returned : int; requested : int }
type outcome =
  | Copied of progress
  | Unsupported of progress * system_error
  | Failed of progress * failure

(* This preserves the existing native adapter boundary while removing the
   catch-all fallback. EINVAL in particular needs more precise native
   status reporting before they can be classified independently of legacy
   backend conventions. No filesystem-wide capability is inferred here. *)
let legacy_unsupported = function
  | Unix.EINVAL | Unix.ENOSYS | Unix.EXDEV
  | Unix.ESPIPE | Unix.ENOTSOCK | Unix.EOPNOTSUPP
  | Unix.EUNKNOWNERR (-50) | Unix.EUNKNOWNERR (-1) -> true
  | _ -> false

let run ?(check_cancel = fun () -> ()) ~max_chunk ~source_offset ~length
    ~step ~notify () =
  if max_chunk <= 0 || source_offset < 0L || length < 0L ||
     length > Int64.sub Int64.max_int source_offset then
    invalid_arg "CopyRange.run: invalid range or chunk size";
  let chunk = Int64.of_int max_chunk in
  let rec loop completed =
    let progress = { requested = length; completed } in
    let remaining = Int64.sub length completed in
    if remaining = 0L then Copied progress else begin
      check_cancel ();
      let requested = Int64.to_int (min chunk remaining) in
      let offset = Int64.add source_offset completed in
      (* Keep this handler around only the native step. A progress callback
         can raise an exception with the same shape and must not cause retry. *)
      match (try Ok (step ~source_offset:offset ~length:requested) with
        | Unix.Unix_error (errno, operation, argument) ->
            Error { errno; operation; argument }) with
      | Error error when legacy_unsupported error.errno ->
          Unsupported (progress, error)
      | Error error -> Failed (progress, System_error error)
      | Ok 0 -> Failed (progress, No_progress)
      | Ok returned when returned < 0 || returned > requested ->
          Failed (progress, Invalid_progress { returned; requested })
      | Ok returned ->
          let completed = Int64.add completed (Int64.of_int returned) in
          notify returned;
          loop completed
    end
  in loop 0L
