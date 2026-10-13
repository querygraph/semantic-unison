type region = { offset : int64; length : int }
type manifest = { regions : region list }
type change = Exact_bytes | Editable_metadata | Other_bytes
module type S = sig
  val profile : string
  val inspect : SemanticFile.t -> (manifest, string) result
end
let max_region = 1048576
let max_payload = 16 * 1048576
type handle = { name : string; capability : string; extension : (module S);
                payload_limit : int; suffixes : string list }
let trusted ?capability ?(max_payload=max_payload) ?(suffixes=[])
    ((module E : S) as extension) =
  if max_payload <= 0 || max_payload > 16 * 1048576 then
    invalid_arg "invalid format payload limit";
  if E.profile = "" || String.length E.profile > 128 || String.contains E.profile '\000' then
    invalid_arg "invalid format profile";
  let capability = match capability with Some value -> value
    | None -> "semantic-profile:" ^ E.profile in
  if capability = "" || String.length capability > 256 || String.contains capability '\000' then
    invalid_arg "invalid format capability";
  if List.length suffixes > 16 || List.exists (fun suffix ->
    String.length suffix < 2 || String.length suffix > 32 || suffix.[0] <> '.' ||
    String.contains suffix '\000' || String.contains suffix '/' || String.contains suffix '\\') suffixes then
    invalid_arg "invalid format suffix hint";
  let suffixes = List.sort_uniq String.compare (List.map String.lowercase_ascii suffixes) in
  {name=E.profile;capability;extension;payload_limit=max_payload;suffixes}
let profile handle = handle.name
let capability handle = handle.capability
let implementation handle = handle.extension
let payload_limit handle = handle.payload_limit
let suffixes handle = handle.suffixes
let matches_filename handle filename =
  let filename = String.lowercase_ascii filename in
  List.exists (fun suffix ->
    let n = String.length suffix and length = String.length filename in
    n <= length && String.sub filename (length-n) n = suffix) handle.suffixes
(* Registration and lookup belong to the owner loop. Workers receive modules
   directly and never modify this table. Native modules are locally trusted. *)
let registry = ref []
let register ?capability ?max_payload ?suffixes extension =
  let handle = trusted ?capability ?max_payload ?suffixes extension in
  if List.mem_assoc handle.name !registry ||
     List.exists (fun (_,h) -> h.capability = handle.capability) !registry then
    invalid_arg "duplicate or invalid format profile";
  registry := (handle.name, handle) :: !registry
let resolve name = try Some (List.assoc name !registry) with Not_found -> None
let find name = match resolve name with None -> None | Some handle -> Some handle.extension
let profiles () = List.map fst !registry
let registered () = List.rev_map snd !registry
let inspect ?(max_payload=max_payload) (module E : S) file =
  if max_payload <= 0 || max_payload > 16 * 1048576 then
    invalid_arg "invalid inspection payload limit";
  match E.inspect file with
  | Error _ as error -> error
  | Ok manifest ->
    let rec check previous total count = function
      | [] -> if count = 0 then Error "no editable regions" else Ok manifest
      | r :: rest ->
        if count >= 64 || r.length <= 0 || r.length > max_region ||
           total > max_payload - r.length || r.offset < previous ||
           r.offset > SemanticFile.size file ||
           Int64.of_int r.length > Int64.sub (SemanticFile.size file) r.offset then
          Error "invalid editable regions"
        else check (Int64.add r.offset (Int64.of_int r.length))
            (total+r.length) (count+1) rest
    in check 0L 0 0 manifest.regions
