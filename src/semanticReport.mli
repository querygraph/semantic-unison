(** Read-only descriptions of current data-fork observations. These explain
    differences; they never authorize a transfer or resolve a conflict. *)
type supported = {
  description : SemanticDelta.description;
  samples : SemanticDelta.sample list;
}
type observation = Supported of supported | Unsupported of string * string |
                   Unavailable of string * string
type classification = Exact_bytes | Metadata_only | Other_bytes | Unknown
val from_proof : SemanticDelta.proof -> observation
val profile : observation -> string
val classification : observation -> observation -> classification
val encode : nonce:string -> observation -> string
val decode : nonce:string -> profile:string -> max_payload:int -> string ->
  (observation, string) result
(** Versioned bounded SIR/0 observation. A peer's hashes remain statements from
    that trusted connection, not independently checked local proofs. *)
val max_size : int
val reason : string -> string
val display_reason : string -> string
(** Clip diagnostics before escaping terminal control and non-ASCII bytes. *)
val render : left_label:string -> right_label:string -> observation -> observation -> string
(** Bounded terminal-safe text and byte previews, with explicit current-replica
    scope. No XML interpretation, rendering identity or archive-base claim. *)
