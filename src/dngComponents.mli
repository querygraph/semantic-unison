(** Advisory DNG physical partition for component hashing. Unknown gaps remain
    opaque; table descriptors/padding remain structural. No merge/transfer authority. *)
val describe : SemanticFile.t -> (ComponentHash.spec, string) result
