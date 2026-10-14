(** Pure packet reconciliation only; does not choose an archive base, inspect
    DNG payloads, publish files or override ordinary conflicts. *)
val policy : string
val merge : base:string -> left:string -> right:string -> (string, string) result
(** All three packets must have identical non-allowlisted bytes and supported
    scalar shapes. One-sided scalar edits are selected; equal decoded concurrent
    values converge with deterministic exact encoding; competing values conflict.
    Deletion/addition, namespace/subject/unknown/rendering/structural changes
    conflict. The output uses the base shell and selected encodings. It may
    differ in length; container materialization must separately prove capacity,
    exact preservation, input identity and normal guarded commits. *)
