(* Actual format-23 archive decoder; selected path can be a file or directory. *)
let () =
  let input=open_in_bin Sys.argv.(1) in
  let version=input_line input and roots=input_line input and timestamp=input_line input in
  if version<>"Unison archive format 23" then failwith "unexpected archive format";
  let features=match String.split_on_char '\030' timestamp with _::rest -> List.filter ((<>) "") rest | [] -> [] in
  let common=Features.inter features (Features.all ()) in
  if List.length features<>List.length common then failwith "unknown archive feature";
  Features.setEnabled common;
  let properties=Proplist.m in
  let codec=Umarshal.(prod4 Update.marchive int string properties id id) in
  let archive,_,_,_=Umarshal.from_channel codec input in
  close_in input;
  let rec select node = function
    | [] -> node
    | name::rest -> match node with
      | Update.ArchiveDir (_,children) ->
          let found=ref None in
          Update.NameMap.iter (fun key node -> if Name.toString key=name then found:=Some node) children;
          select (Option.value ~default:Update.NoArchive !found) rest
      | _ -> Update.NoArchive in
  let node=select archive (String.split_on_char '/' Sys.argv.(2)) in
  let kind,fingerprint=match node with
    | Update.NoArchive -> "absent",""
    | Update.ArchiveFile (_,fingerprint,_,_) -> "file",Os.fullfingerprint_to_string fingerprint
    | Update.ArchiveDir _ -> "directory",""
    | Update.ArchiveSymlink _ -> "symlink","" in
  Printf.printf "{\"format\":23,\"roots\":%S,\"path\":%S,\"kind\":%S,\"fingerprint\":%S,\"node_sha256\":%S}\n"
    roots Sys.argv.(2) kind fingerprint
    (SemanticHash.hex (SemanticHash.string (Umarshal.to_string Update.marchive node)))
