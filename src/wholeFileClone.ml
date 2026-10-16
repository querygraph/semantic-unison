type backend = Platform | Linux_ficlone | Macos_fclonefileat
type phase = Unavailable | Arguments | Source_descriptor | Destination_descriptor
  | Source_eof | Destination_eof | Source_position | Destination_position
  | Destination_parent | Native_clone | Source_verification
  | Destination_verification | Cursor_verification | Property_profile | Cleanup
type mutation = No_effect | Known_prefix | Indeterminate
type decline_scope = Platform_unavailable | Kernel_unavailable
  | Filesystem_unsupported | Cross_device | Source_constraints | Empty_source
type receipt = {
  requested : int64; completed : int64; backend : backend; phase : phase;
  errno : Unix.error option; native_code : int64; mutation : mutation;
}
type result = Native_shared of receipt | No_work of receipt
  | Declined of decline_scope * receipt | Failed of receipt
type native_raw = int * int64 * int * int * Unix.error option * int * int * int64
exception Invalid_native_status of string

let invalid reason = raise (Invalid_native_status reason)
let check_length n =
  if n < 0L then invalid_arg "WholeFileClone: negative expected length"

let backend_name = function
  | Platform -> "platform"
  | Linux_ficlone -> "linux-ficlone"
  | Macos_fclonefileat -> "macos-fclonefileat"
let phase_name = function
  | Unavailable -> "unavailable" | Arguments -> "arguments"
  | Source_descriptor -> "source-descriptor"
  | Destination_descriptor -> "destination-descriptor"
  | Source_eof -> "source-eof" | Destination_eof -> "destination-eof"
  | Source_position -> "source-position"
  | Destination_position -> "destination-position"
  | Destination_parent -> "destination-parent" | Native_clone -> "native-clone"
  | Source_verification -> "source-verification"
  | Destination_verification -> "destination-verification"
  | Cursor_verification -> "cursor-verification"
  | Property_profile -> "property-profile" | Cleanup -> "cleanup"
let scope_name = function
  | Platform_unavailable -> "platform" | Kernel_unavailable -> "kernel"
  | Filesystem_unsupported -> "filesystem" | Cross_device -> "cross-device"
  | Source_constraints -> "source-constraints" | Empty_source -> "empty-source"
let describe_native r =
  Printf.sprintf "whole-clone/%s/%s%s" (backend_name r.backend) (phase_name r.phase)
    (match r.errno with None -> "" | Some error ->
      Printf.sprintf " [%s; native code %Ld]" (Unix.error_message error) r.native_code)
let raise_failed ?(argument = "") r =
  match r.errno with
  | Some error -> raise (Unix.Unix_error (error, describe_native r, argument))
  | None -> invalid "failed whole-file clone receipt has no mapped error"

let native_backend = function Platform -> false | Linux_ficlone | Macos_fclonefileat -> true
let preflight_phase = function
  | Arguments | Source_descriptor | Destination_descriptor | Source_eof
  | Destination_eof | Source_position | Destination_position | Destination_parent -> true
  | _ -> false
let post_clone_phase = function
  | Native_clone | Source_verification | Destination_verification
  | Cursor_verification | Property_profile | Cleanup -> true
  | _ -> false

let decline_consistent scope r =
  match scope, r.backend, r.phase, r.errno with
  | Platform_unavailable, Platform, Unavailable, None -> r.native_code = 0L
  | Kernel_unavailable, (Linux_ficlone | Macos_fclonefileat), Native_clone,
      Some Unix.ENOSYS -> r.native_code > 0L
  | Kernel_unavailable, Linux_ficlone, Native_clone, Some Unix.ENOTTY ->
      r.native_code > 0L
  | Filesystem_unsupported, (Linux_ficlone | Macos_fclonefileat), Native_clone,
      Some Unix.EOPNOTSUPP -> r.native_code > 0L
  | Cross_device, (Linux_ficlone | Macos_fclonefileat), Native_clone,
      Some Unix.EXDEV -> r.native_code > 0L
  | Cross_device, (Linux_ficlone | Macos_fclonefileat),
      (Destination_descriptor | Destination_parent), None -> r.native_code = 0L
  | Source_constraints, (Linux_ficlone | Macos_fclonefileat),
      Source_descriptor, None -> r.native_code = 0L
  | Empty_source, Macos_fclonefileat, Source_eof, None ->
      r.requested = 0L && r.native_code = 0L
  | _ -> false

let validate_result ~expected_length result =
  check_length expected_length;
  let r = match result with
    | Native_shared r | No_work r | Declined (_, r) | Failed r -> r in
  if r.requested <> expected_length then invalid "whole-file clone request changed";
  if r.completed < 0L || r.completed > expected_length then
    invalid "whole-file clone completion is out of bounds";
  if r.completed <> 0L && r.completed <> expected_length then
    invalid "whole-file clone has no authoritative short-prefix result";
  (* Current native clone backends report POSIX errno. Platform-only Windows
     preflight may retain opaque unsigned DWORD/NTSTATUS bits in Int64. *)
  let maximum_native_code = if r.backend = Platform then 4294967295L else 2147483647L in
  if r.native_code < 0L || r.native_code > maximum_native_code then
    invalid "whole-file clone native error code is out of bounds";
  if r.errno = None && r.native_code <> 0L then
    invalid "whole-file clone native error has no mapped error";
  if r.mutation = No_effect && r.completed <> 0L then
    invalid "no-effect whole-file clone reports completed bytes";
  (match result with
   | Native_shared _ ->
       if expected_length = 0L || r.completed <> expected_length ||
          r.mutation <> Known_prefix || not (native_backend r.backend) ||
          r.phase <> Cursor_verification || r.errno <> None || r.native_code <> 0L then
         invalid "invalid whole-file clone success"
   | No_work _ ->
       if expected_length <> 0L || r.completed <> 0L || r.mutation <> No_effect ||
          r.backend = Macos_fclonefileat || r.phase <> Cursor_verification ||
          r.errno <> None || r.native_code <> 0L then
         invalid "invalid empty whole-file clone result"
   | Declined (scope, _) ->
       if r.completed <> 0L || r.mutation <> No_effect ||
          not (decline_consistent scope r) then
         invalid "whole-file clone decline contradicts context/effects"
   | Failed _ ->
       if r.errno = None || r.phase = Unavailable then
         invalid "whole-file clone failure lacks a valid error phase";
       if r.backend = Platform && not (preflight_phase r.phase || r.phase = Cleanup) then
         invalid "platform-only whole-file clone reports native mutation phase";
       if preflight_phase r.phase && (r.completed <> 0L || r.mutation <> No_effect) then
         invalid "whole-file clone preflight failure reports mutation";
       if r.mutation = Known_prefix &&
          (r.completed = 0L || not (native_backend r.backend) ||
           not (post_clone_phase r.phase)) then
         invalid "whole-file clone failure reports an invalid known completion";
       if r.mutation = Indeterminate && not (post_clone_phase r.phase) then
         invalid "whole-file clone has indeterminate preflight effects");
  result

let decode_native ~expected_length
    (status, completed, backend, phase, errno, mutation, decline, native_code) =
  check_length expected_length;
  let backend = match backend with
    | 0 -> Platform | 1 -> Linux_ficlone | 2 -> Macos_fclonefileat
    | _ -> invalid "unknown whole-file clone backend" in
  let phase = match phase with
    | 0 -> Unavailable | 1 -> Arguments | 2 -> Source_descriptor
    | 3 -> Destination_descriptor | 4 -> Source_eof | 5 -> Destination_eof
    | 6 -> Source_position | 7 -> Destination_position | 8 -> Destination_parent
    | 9 -> Native_clone | 10 -> Source_verification | 11 -> Destination_verification
    | 12 -> Cursor_verification | 13 -> Property_profile | 14 -> Cleanup
    | _ -> invalid "unknown whole-file clone phase" in
  let mutation = match mutation with
    | 0 -> No_effect | 1 -> Known_prefix | 2 -> Indeterminate
    | _ -> invalid "unknown whole-file clone effect" in
  let r = { requested = expected_length; completed; backend; phase; errno;
            native_code; mutation } in
  let result = match status with
    | 0 | 2 | 3 when decline <> 0 ->
        invalid "whole-file clone nondecline carries a decline scope"
    | 0 -> Native_shared r
    | 1 ->
        let scope = match decline with
          | 1 -> Platform_unavailable | 2 -> Kernel_unavailable
          | 3 -> Filesystem_unsupported | 4 -> Cross_device
          | 5 -> Source_constraints | 6 -> Empty_source
          | _ -> invalid "unknown whole-file clone decline scope" in
        Declined (scope, r)
    | 2 -> Failed r | 3 -> No_work r
    | _ -> invalid "unknown whole-file clone status" in
  validate_result ~expected_length result

let platform_decline ~expected_length =
  decode_native ~expected_length (1, 0L, 0, 0, None, 0, 1, 0L)
