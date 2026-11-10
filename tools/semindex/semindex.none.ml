(* unison-dngscan -semindex without the opam sqlite3 package: refused. *)

type row = { size : int64; mtime_ns : int64; sha256 : string; dng_blocks : string; image_data : string }
type t = unit

let available = false
let open_ (_ : string) : t = failwith "-semindex: this unison-dngscan was built without the opam sqlite3 package"
let at () (_ : string) : row option = None
let holding () (_ : string) (_ : int) : (string * row) list = []
let sharing () (_ : string) (_ : string) (_ : int) : (string * row) list = []
