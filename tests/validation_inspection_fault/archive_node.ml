(* Decode an actual format-23 archive with the production public codecs. *)
let () =
  let input=open_in_bin Sys.argv.(1) in
  let version=input_line input and roots=input_line input and timestamp=input_line input in
  if version<>"Unison archive format 23" then failwith "unexpected archive format";
  let features=match String.split_on_char '\030' timestamp with _::rest -> List.filter((<>) "") rest | [] -> [] in
  let common=Features.inter features (Features.all()) in
  if List.length features<>List.length common then failwith "unknown archive feature";
  Features.setEnabled common;
  let properties=Proplist.m in
  let codec=Umarshal.(prod4 Update.marchive int string properties id id) in
  let archive,_,_,_=Umarshal.from_channel codec input in
  close_in input;
  let node=match archive with
    | Update.ArchiveDir(_,children) ->
      let found=ref None in
      Update.NameMap.iter(fun name node -> if Name.toString name="renamed.bin" then
        match !found with None -> found:=Some node | Some _ -> failwith "duplicate node") children;
      (match !found with Some node -> node | None -> failwith "missing renamed.bin node")
    | _ -> failwith "archive root is not a directory" in
  match node with
  | Update.ArchiveFile(_,fingerprint,_,_) ->
    let prefix="Archive for root " and separator=" synchronizing roots " in
    if String.sub roots 0 (String.length prefix)<>prefix then failwith "invalid root header";
    let at=Str.search_forward(Str.regexp_string separator) roots (String.length prefix) in
    let archive_root=String.sub roots (String.length prefix) (at-String.length prefix) in
    let peers=String.sub roots (at+String.length separator) (String.length roots-at-String.length separator) in
    Printf.printf "{\"format\":23,\"archive_root\":%S,\"peer_roots\":%S,\"filename\":\"renamed.bin\",\"fullfingerprint\":%S,\"node_sha256\":%S}\n"
      archive_root peers (Os.fullfingerprint_to_string fingerprint)
      (SemanticHash.hex(SemanticHash.string(Umarshal.to_string Update.marchive node)))
  | _ -> failwith "renamed.bin node is not a file"
