type t = {max_entries:int;max_path_bytes:int;mutable entries:int;mutable path_bytes:int}
exception Exceeded of string
let create ~max_entries ~max_path_bytes =
  if max_entries < 0 || max_path_bytes < 0 then invalid_arg "negative validation tree limit";
  {max_entries;max_path_bytes;entries=0;path_bytes=0}
let add a b =
  if a < 0 || b < 0 then invalid_arg "negative validation tree path length";
  if a > max_int - b then raise (Exceeded "Validation tree accounting overflow");
  a+b
let reserve t ~prefix_bytes ~name_bytes =
  let entries = add t.entries 1 in
  let bytes = add t.path_bytes (add prefix_bytes name_bytes) in
  if t.max_entries <> 0 && entries > t.max_entries then
    raise (Exceeded "Validation tree exceeds validationtreeentries");
  if t.max_path_bytes <> 0 && bytes > t.max_path_bytes then
    raise (Exceeded "Validation tree exceeds validationtreepathbytes");
  t.entries <- entries; t.path_bytes <- bytes
let usage t = t.entries,t.path_bytes
