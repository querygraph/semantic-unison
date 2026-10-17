include FormatExtension.S
val inspect_extended : SemanticFile.t -> (FormatExtension.manifest, string) result
(** Inspector for the separately negotiated v1 profile. Extends the unchanged
    v0 subset with BigTIFF and bounded embedded CR camera-profile graphs. Both
    byte orders and each embedded profile's relative offset base are explicit.
    The same single fixed XMP region and complete complement proof are required;
    this does not establish full DNG validity or rendering equivalence. *)
val inspect_layout : SemanticFile.t -> (FormatExtension.manifest, string) result
(** Layout-only exact transfer inspector. Unknown/private declared values stay
    protected and byte-exact; hidden pointer rules are not interpreted. Must be
    used under its separate profile with full-donor-hash materialization. No
    reconciliation, relocation or semantic-equivalence authority follows. *)
type component_role = Image_bytes | Standard_value | Private_value | Structure
type component_region = { logical_id : string; schema : string; role : component_role;
                          offset : int64; length : int64 }
val component_regions : SemanticFile.t -> (component_region list, string) result
(** Bounded advisory physical claims from the same TIFF graph reader; no XMP
    requirement. Inline values are separated from descriptors/padding. Aliases are not
    independent components: consumers must reject conflicting physical claims.
    Logical image IDs identify graph traversal/unit order, not decoded pixels. *)
val observer : FormatExtension.observer
(** Advisory namespace-aware XMP property encodings. Parsing failures affect
    descriptions only; exact byte proofs and transfer eligibility are unchanged. *)
