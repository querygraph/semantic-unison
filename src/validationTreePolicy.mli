(** Owner-only receiving tree policy, independent of runtime worker startup. *)
val memory_bytes : unit -> int
(** Estimated retained bytes per snapshot. Zero disables memory admission.
    First observation pins this setting for the process lifetime. *)
val budget : unit -> ValidationTreeBudget.t
