(** Trusted compiled partial-field decoder; no camera-family routing or stability
    policy. Parent supplies the bounded address-space translation explicitly. *)
type byte_order = Little | Big
type field = { tag : int; name : string; max_bytes : int }
type schema = { component_id : string; decoder_id : string;
                implementation_sha256 : string; byte_order : byte_order;
                directory_at : int64; value_base : int64; max_span : int64;
                max_entries : int; fields : field list }
val freeze : schema -> (ComponentHash.plugin, string) result
(** At most32 selected ASCII fields,256 classic12-byte entries,4096 bytes/field.
    Unknown fields and links are never followed. Selected values must be bounded,
    NUL-terminated ASCII, unique and physically disjoint. Other bytes stay opaque.
    Geometry/encoding mismatch is unsupported; operational reader errors propagate.
    Decoder provenance binds the owner code digest and complete frozen schema.
    No implementation authentication, vendor recognition or rendering authority. *)
