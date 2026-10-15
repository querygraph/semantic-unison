(** Optional validation of a private, finalized DNG candidate by a qualified
    Adobe SDK driver. This protocol is deliberately not the stock dng_validate
    CLI: that CLI can report digest errors while returning exit status zero.

    Call on every receiving transfer path before rename/archive update. This
    module neither publishes files nor negotiates remote enforcement. An old
    receiver cannot enforce this policy without an explicit capability. *)

type policy = Off | Warn | Require
type snapshot = { sha256 : string; size : int64; identity : string }
(** SHA-256 is lowercase hex over all candidate data-fork bytes. [identity]
    identifies the opened file and its relevant change metadata. The supplied
    inspector must reject unstable reads and must be asynchronous or schedule
    expensive hashing through the same CPU budget. Resource-fork verification
    and the final commit fence remain the caller's responsibility. *)

type tool = {
  executable : string;
  executable_sha256 : string;
  build_id : string;
  arguments : string array;
  environment : string array;
  cpu_weight : int;
  limits : HelperSupervisor.limits;
}
(** Locally configured absolute executable, content pin, qualified build ID,
    and fixed argument prefix. [cpu_weight] includes SDK internal threads.
    The executable and its containing directories must be trusted: pre/post
    identity checks detect ordinary changes, not hostile exec-time replacement.
    Pinning a launcher does not pin its interpreter/libraries; the qualification
    and build ID must cover the complete SDK driver deployment. *)

type raw_digest = Valid | Missing | Mismatch | Unsupported | Not_checked
type report = {
  candidate_sha256 : string;
  candidate_size : int64;
  driver_build : string;
  structure : string;
  decode : string;
  raw_digest : raw_digest;
  errors : int;
  warnings : int;
}
val parse_report : string -> (report, string) result
(** Strict, bounded protocol parser; unknown, repeated or reordered fields are
    rejected. See tests/helpers/README.md for the wire format. *)

type receipt = {
  candidate : snapshot;
  executable_sha256 : string;
  build_id : string;
  report : report;
  process : HelperSupervisor.result;
}
type result =
  | Skipped
  | Passed of receipt
  | Warning of string * HelperSupervisor.result option
  | Rejected of string * HelperSupervisor.result option

val validate :
  HelperSupervisor.t -> HelperSupervisor.cancellation ->
  policy:policy -> tool:tool option ->
  inspect:(string -> snapshot Lwt.t) ->
  candidate:string -> expected:snapshot -> result Lwt.t
(** Require fails closed for unavailable tools, malformed/incomplete receipts,
    unsupported validation, timeouts, cancellation, mismatches, changed files,
    or any SDK error count (including exit-zero errors). Missing optional raw
    digest tags are reported separately and are not themselves corruption.
    Warn returns validation findings as warnings; the caller decides presentation.
    Candidate input/pre-inspection errors, candidate/tool mutation, a failed
    post-inspection, and cancellation always
    reject, even under Warn. The caller must still fence changes at commit.
    Receipts are tied to this exact candidate and qualified tool, never merely
    to a DNG semantic fingerprint. No cache is maintained by this module. *)

val validate_with_execution :
  ?process_limits:HelperSupervisor.process_limits ->
  ?observe_group:(int option -> unit) ->
  execute:((unit -> HelperSupervisor.result Lwt.t) -> HelperSupervisor.result Lwt.t) ->
  HelperSupervisor.t -> HelperSupervisor.cancellation ->
  policy:policy -> tool:tool option ->
  inspect:(string -> snapshot Lwt.t) ->
  candidate:string -> expected:snapshot -> result Lwt.t
(** [validate] with an endpoint-owned wrapper around only the actual supervised
    helper execution. Pre/post digest inspections run outside this wrapper, so
    a shared I/O lease cannot deadlock nested worker admission. The wrapper
    must await helper settlement on every path before releasing its resources. *)

(** [validate_with_execution]'s optional [observe_group] has the same owner-loop,
    observational-only contract as [HelperSupervisor.run]. It never substitutes
    for SDK receipt validation or candidate identity checks. *)
