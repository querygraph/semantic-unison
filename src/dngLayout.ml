(* Partial format knowledge is sufficient for exact donor reconstruction.
   Unknown private values remain opaque and fully hash-covered. This profile
   does not assert XMP independence or authorize synthesized reconciliation. *)
let profile = "org.firstpair.dng-layout/0"
let inspect = DngSemantic.inspect_layout
