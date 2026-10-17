include CandidateValidator.S
val resources : unit -> BackendResources.t
val all_scanned : unit -> bool
val scan_limits : unit -> int * int * int64
(** Strict scope/capability checks and positive file/path/snapshot limits.
    Off does not request scan validation; received remains the default. *)
(** DNG-owned endpoint policy, capability and qualified SDK-driver invocation.
    Recognition/validation is independent of both DNG transfer profiles. *)
