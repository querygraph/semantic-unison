(** Owner-only optional trusted private metadata base storage. Never accepts a
    peer record or chooses the common archive generation. *)
val enabled : unit -> bool
val store : root:Fspath.t -> path:Path.local -> fingerprint:Os.fullfingerprint ->
  SemanticDelta.proof -> unit
val load : root:Fspath.t -> path:Path.local -> fingerprint:Os.fullfingerprint ->
  SemanticDelta.proof option
(** Fingerprint must be the agreeing previous common archive, not a current
    replica. Missing, incompatible, malformed or untrusted records decline. *)
