(** Read-only descriptions of current data-fork observations. These explain
    differences; they never authorize a transfer or resolve a conflict. *)
type supported = {
  description : SemanticDelta.description;
  samples : SemanticDelta.sample list;
  meaning : (FormatExtension.observation, string) result option;
}
type observation = Supported of supported | Unsupported of string * string |
                   Unavailable of string * string
type classification = Exact_bytes | Metadata_only | Other_bytes | Unknown
(** Metadata_only is a legacy region-byte classification, not proof of private
    meaning, rendering equivalence or independence from unparsed references. *)
val from_proof : ?meaning:(FormatExtension.observation, string) result -> SemanticDelta.proof -> observation
val profile : observation -> string
val classification : observation -> observation -> classification
val encode : nonce:string -> observation -> string
val decode : nonce:string -> profile:string -> max_payload:int -> string ->
  (observation, string) result
(** Versioned bounded SIR/0 observation. A peer's hashes remain statements from
    that trusted connection, not independently checked local proofs. *)
val max_size : int
val max_observation_size : int
val encode_observation : nonce:string -> observation -> string
val decode_observation : nonce:string -> profile:string -> max_payload:int -> string ->
  (observation, string) result
(** Separately negotiated bounded SIR/1 advisory extension properties. SIR/0
    remains byte-identical and omits these properties. No transfer authority,
    schema equivalence, XML/RDF value equality or rendering identity follows. *)
val reason : string -> string
val display_reason : string -> string
(** Clip diagnostics before escaping terminal control and non-ASCII bytes. *)
val render : left_label:string -> right_label:string -> observation -> observation -> string
(** Bounded terminal-safe text and byte previews, with explicit current-replica
    scope. No XML interpretation, rendering identity or archive-base claim. *)

type component_observation = {
  schema : string;
  full_sha256 : string;
  layout_sha256 : string;
  projections : (ComponentHash.role * ComponentHash.projection option) list;
}
val render_components : left:component_observation -> right:component_observation ->
  (string, string) result
(** Local advisory comparison only; no SIR/0 or SIR/1 wire change. The owner
    supplies the explicit common projection contract, not a camera model label.
    Missing lanes are unknown, never equal empty content. Incompatible schemas
    suppress component comparisons. Exact full hashes remain independently
    comparable. No persistent binding, rendering, transfer or merge authority. *)
