(** Bounded range-copy progress over the existing native copy API.
    This module does not claim that successful native copying shared blocks. *)

type progress = { requested : int64; completed : int64 }
(** [completed] is the contiguous successful prefix, not an extent set. *)

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
  backend : backend; phase : phase; errno : Unix.error option;
  mutation : mutation; native_code : int64;
}
(** [native_code] preserves a POSIX errno or unsigned Win32 DWORD/NTSTATUS
    when supplied by the backend; zero means no native error was reported.
    The mapped [errno] is separate. Native success does not attest sharing. *)
type native_step =
  | Native_progress of int * native_context
  | Native_declined of int * decline_scope * native_context
  | Native_failed of int * native_context
type native_raw = int * int * int * int * Unix.error option * int * int * int64
exception Invalid_native_status of string
val decode_native : native_raw -> native_step
(** Decode the additive C protocol. Unknown IDs and contradictory error/decline
    fields reject the result, never grant permission to fall back. *)
val describe_native : native_context -> string
val scope_name : decline_scope -> string

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
(** [Copied] means exact requested completion with sharing unreported.
    [Unsupported] permits suffix fallback under the legacy native contract:
    successful calls advance destination position, unsuccessful calls do not.
    [Failed] never permits fallback. Invalid progress may imply unknown effects
    from the last call; the candidate must be discarded. *)

val run :
  ?check_cancel:(unit -> unit) ->
  max_chunk:int -> source_offset:int64 -> length:int64 ->
  step:(source_offset:int64 -> length:int -> int) ->
  notify:(int -> unit) -> unit -> outcome
(** Validate offsets/length before calling anything; request bounded chunks and
    report each positive successful count once. A zero return before the exact
    requested end is [No_progress], not successful completion or fallback.

    Only [Unix.Unix_error] raised directly by [step] is classified. Cancellation,
    notification and other step exceptions propagate unchanged. The compatibility
    unsupported set is EINVAL, ENOSYS, EXDEV, ESPIPE, ENOTSOCK, EOPNOTSUPP
    and historical EUNKNOWNERR -50/-1. Ambiguous EINVAL and platform-specific
    ESPIPE/ENOTSOCK remain compatibility cases, not proven capabilities. EBADF
    escaping the native adapter is a failure, not permission to retry copying.
    Per-backend native statuses and generation-aware capability checks remain
    separate work. *)

val run_native :
  ?check_cancel:(unit -> unit) -> max_chunk:int -> source_offset:int64 -> length:int64 ->
  step:(source_offset:int64 -> length:int -> native_step) ->
  notify:(int -> unit) -> unit -> outcome
(** Strict caller path. Only explicit scoped [Native_declined] with no effect
    or a known reported prefix permits suffix fallback. Indeterminate effects,
    thrown Unix errors, malformed results and native failures are terminal even
    when their errno occurs in the legacy unsupported set. A reported prefix
    on a terminal native error remains counted; the candidate must be discarded.
    Direct typed adapters obey the raw decoder's context invariants too:
    negative native codes, successful results carrying errors, and failed
    results without errno stop before accounting or notification of that call.
    Callback/cancellation exceptions propagate. [run] retains the old ABI's
    compatibility classification and is not used by the migrated production
    caller. *)
