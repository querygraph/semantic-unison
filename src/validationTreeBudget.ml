type t = {max_entries:int;max_path_bytes:int;max_memory_bytes:int;
  mutable entries:int;mutable path_bytes:int;mutable estimated_bytes:int}
exception Exceeded of string
let create_with_memory ~max_memory_bytes ~max_entries ~max_path_bytes =
  if max_entries < 0 || max_path_bytes < 0 || max_memory_bytes < 0 then invalid_arg "negative validation tree limit";
  {max_entries;max_path_bytes;max_memory_bytes;entries=0;path_bytes=0;estimated_bytes=0}
let create ~max_entries ~max_path_bytes = create_with_memory ~max_memory_bytes:0 ~max_entries ~max_path_bytes
let add a b =
  if a < 0 || b < 0 then invalid_arg "negative validation tree path length";
  if a > max_int - b then raise (Exceeded "Validation tree accounting overflow");
  a+b
let reserve t ~prefix_bytes ~name_bytes =
  let entries = add t.entries 1 in
  let length = add prefix_bytes name_bytes in
  let bytes = add t.path_bytes length in
  if t.max_entries <> 0 && entries > t.max_entries then
    raise (Exceeded "Validation tree exceeds validationtreeentries");
  if t.max_path_bytes <> 0 && bytes > t.max_path_bytes then
    raise (Exceeded "Validation tree exceeds validationtreepathbytes");
  let memory = if t.max_memory_bytes=0 then t.estimated_bytes else
    let scaled = if length > max_int / 8 then raise (Exceeded "Validation tree accounting overflow") else length * 8 in
    add t.estimated_bytes (add 1024 scaled) in
  if t.max_memory_bytes <> 0 && memory > t.max_memory_bytes then
    raise (Exceeded "Validation tree exceeds validationtreememory");
  t.entries <- entries; t.path_bytes <- bytes; t.estimated_bytes <- memory
let usage t = t.entries,t.path_bytes
let memory_enabled t = t.max_memory_bytes <> 0
let estimated_bytes t = t.estimated_bytes
let charge_metadata t bytes =
  if bytes < 0 then invalid_arg "negative validation tree metadata size";
  if t.max_memory_bytes <> 0 then begin
    if bytes > max_int / 8 then raise (Exceeded "Validation tree accounting overflow");
    let memory = add t.estimated_bytes (bytes * 8) in
    if memory > t.max_memory_bytes then raise (Exceeded "Validation tree exceeds validationtreememory");
    t.estimated_bytes <- memory
  end
