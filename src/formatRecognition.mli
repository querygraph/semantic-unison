(** Immutable, locally trusted content recognition for receiving validators.
    Recognition is independent of exact-transfer eligibility and preferences. *)
type verdict = Not_matched | Recognized | Indeterminate of string
module type S = sig (* ox-portable-signature *)
  val format : string
  val identify : SemanticFile.t -> verdict
end
type handle
val trusted : ?suffixes:string list -> (module S) -> handle
(** Owner-side construction. The compiled recognizer uses only worker-local
    state and bounded reads of the supplied file, with no registry, preference,
    subprocess or owner callback access. Stock relies on this trusted-code contract; OxCaml additionally checks
    portable callback capture. This does not prove format validity or bounds. *)
val format : handle -> string
val matches_filename : handle -> string -> bool
(** A destination filename claim forces validation even for malformed bytes;
    absence of a claim does not suppress content recognition. *)
val identify : handle -> SemanticFile.t -> verdict
(** Bound an indeterminate diagnostic to 1,024 bytes. Operational, stability
    and cancellation errors propagate; they never become Not_matched. *)
val max_recognizers : int
