type progress = { requested : int64; completed : int64 }
type system_error = {
  errno : Unix.error;
  operation : string;
  argument : string;
}
type backend = Platform | Linux_copy_file_range | Linux_sendfile
  | Freebsd | Solaris | Windows
type phase = Unavailable | Arguments | Descriptors | Copy_file_range | Sendfile
  | Volume_query | Geometry | Sparse | Extend_eof | Duplicate_extents
  | Advance_position | Verify_position
type mutation = No_effect | Known_prefix | Indeterminate
type decline_scope = Platform_unavailable | Kernel_unavailable
  | Filesystem_unsupported | Cross_device | Alignment
type native_context = {
  backend : backend;
  phase : phase;
  errno : Unix.error option;
  mutation : mutation;
  native_code : int64;
}
type native_step =
  | Native_progress of int * native_context
  | Native_declined of int * decline_scope * native_context
  | Native_failed of int * native_context
type native_raw = int * int * int * int * Unix.error option * int * int * int64
exception Invalid_native_status of string
type failure =
  | System_error of system_error
  | No_progress
  | Invalid_progress of { returned : int; requested : int }
  | Native_error of native_context
  | Invalid_native_result of string
type outcome =
  | Copied of progress
  | Unsupported of progress * system_error
  | Native_unsupported of progress * decline_scope * native_context
  | Failed of progress * failure

let invalid_status reason = raise (Invalid_native_status reason)
let decline_consistent scope context =
  let native_call = match context.backend,context.phase with
    | (Linux_copy_file_range | Freebsd),Copy_file_range
    | (Linux_sendfile | Solaris),Sendfile -> true
    | _ -> false in
  match scope,context.errno with
  | Platform_unavailable,None ->
      context.backend = Platform && context.phase = Unavailable && context.native_code = 0L
  | Kernel_unavailable,Some Unix.ENOSYS -> native_call
  | Filesystem_unsupported,Some Unix.EOPNOTSUPP -> native_call
  | Cross_device,Some Unix.EXDEV -> native_call
  | (Filesystem_unsupported | Cross_device),None ->
      context.backend = Windows && context.phase = Volume_query && context.native_code = 0L
  | Alignment,None ->
      context.backend = Windows && context.phase = Geometry && context.native_code = 0L
  | _ -> false
let decode_native (status,completed,backend,phase,errno,mutation,scope,native_code) =
  let backend = match backend with
    | 0 -> Platform | 1 -> Linux_copy_file_range | 2 -> Linux_sendfile
    | 3 -> Freebsd | 4 -> Solaris | 5 -> Windows
    | _ -> invalid_status "unknown native range backend" in
  let phase = match phase with
    | 0 -> Unavailable | 1 -> Arguments | 2 -> Descriptors
    | 3 -> Copy_file_range | 4 -> Sendfile | 5 -> Volume_query | 6 -> Geometry
    | 7 -> Sparse | 8 -> Extend_eof | 9 -> Duplicate_extents
    | 10 -> Advance_position | 11 -> Verify_position
    | _ -> invalid_status "unknown native range phase" in
  let mutation = match mutation with
    | 0 -> No_effect | 1 -> Known_prefix | 2 -> Indeterminate
    | _ -> invalid_status "unknown native range effect" in
  if native_code < 0L then invalid_status "negative native range error code";
  let context = {backend;phase;errno;mutation;native_code} in
  match status with
  | 0 ->
      if scope <> 0 || errno <> None || native_code <> 0L then
        invalid_status "successful native range result carries an error/decline";
      Native_progress (completed,context)
  | 1 ->
      let scope = match scope with
        | 1 -> Platform_unavailable | 2 -> Kernel_unavailable
        | 3 -> Filesystem_unsupported | 4 -> Cross_device | 5 -> Alignment
        | _ -> invalid_status "unknown native range decline scope" in
      if not (decline_consistent scope context) then
        invalid_status "native range decline contradicts its backend/phase/error";
      Native_declined (completed,scope,context)
  | 2 ->
      if scope <> 0 || errno = None then
        invalid_status "failed native range result lacks an error or carries a decline";
      Native_failed (completed,context)
  | _ -> invalid_status "unknown native range status"

let backend_name = function
  | Platform -> "platform" | Linux_copy_file_range -> "linux-copy_file_range"
  | Linux_sendfile -> "linux-sendfile" | Freebsd -> "freebsd-copy_file_range"
  | Solaris -> "solaris-sendfile" | Windows -> "windows-duplicate-extents"
let phase_name = function
  | Unavailable -> "unavailable" | Arguments -> "arguments"
  | Descriptors -> "descriptors" | Copy_file_range -> "copy_file_range"
  | Sendfile -> "sendfile" | Volume_query -> "volume-query" | Geometry -> "geometry"
  | Sparse -> "sparse" | Extend_eof -> "extend-eof" | Duplicate_extents -> "duplicate-extents"
  | Advance_position -> "advance-position" | Verify_position -> "verify-position"
let scope_name = function
  | Platform_unavailable -> "platform" | Kernel_unavailable -> "kernel"
  | Filesystem_unsupported -> "filesystem" | Cross_device -> "cross-device"
  | Alignment -> "alignment"
let describe_native context =
  Printf.sprintf "%s/%s%s" (backend_name context.backend) (phase_name context.phase)
    (match context.errno with None -> "" | Some errno ->
      Printf.sprintf " [%s; native code %Ld]" (Unix.error_message errno) context.native_code)

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

let run_native ?(check_cancel = fun () -> ()) ~max_chunk ~source_offset ~length
    ~step ~notify () =
  if max_chunk <= 0 || source_offset < 0L || length < 0L ||
     length > Int64.sub Int64.max_int source_offset then
    invalid_arg "CopyRange.run_native: invalid range or chunk size";
  let chunk = Int64.of_int max_chunk in
  let rec loop completed =
    let progress = {requested=length;completed} in
    let remaining = Int64.sub length completed in
    if remaining = 0L then Copied progress else begin
      check_cancel ();
      let requested = Int64.to_int (min chunk remaining) in
      let offset = Int64.add source_offset completed in
      (* A thrown exception is never a native decline. Keep notification and
         cancellation outside this handler, just as in the legacy loop. *)
      match (try Ok (step ~source_offset:offset ~length:requested) with
        | Unix.Unix_error (errno,operation,argument) ->
            Error (System_error {errno;operation;argument})
        | Invalid_native_status reason -> Error (Invalid_native_result reason)) with
      | Error error -> Failed (progress,error)
      | Ok result ->
          let returned,context = match result with
            | Native_progress (n,c) | Native_declined (n,_,c) | Native_failed (n,c) -> n,c in
          if returned < 0 || returned > requested then
            Failed (progress,Invalid_progress {returned;requested})
          else if context.mutation = No_effect && returned <> 0 then
            Failed (progress,Invalid_native_result "no-effect result reports copied bytes")
          else if (match result with Native_progress _ -> context.mutation = Indeterminate | _ -> false) then
            Failed (progress,Invalid_native_result "successful result has indeterminate effects")
          else if (match result with Native_declined (_,scope,context) ->
            not (decline_consistent scope context) | _ -> false) then
            Failed (progress,Invalid_native_result "native range decline contradicts its backend/phase/error")
          else
            let progress = {progress with completed=Int64.add completed (Int64.of_int returned)} in
            if returned > 0 then notify returned;
            match result with
            | Native_progress (0,_) -> Failed (progress,No_progress)
            | Native_progress _ -> loop progress.completed
            | Native_failed (_,context) -> Failed (progress,Native_error context)
            | Native_declined (_,_,context) when context.mutation = Indeterminate ->
                Failed (progress,Native_error context)
            | Native_declined (_,scope,context) ->
                Native_unsupported (progress,scope,context)
    end
  in loop 0L
