(* Build-only, stock-compatible selector for individually qualified OxCaml
   contracts. It neither receives peer code nor suppresses portability errors. *)
let read path =
  let ch=open_in_bin path in
  try
    let length=in_channel_length ch in
    if length>1048576 then invalid_arg "mode filter source limit";
    let text=really_input_string ch length in close_in ch;text
  with error -> close_in_noerr ch;raise error
let replace text needle replacement =
  let size=String.length needle in
  let output=Buffer.create(String.length text) and count=ref 0 in
  let rec loop at =
    if at+size>String.length text then
      Buffer.add_substring output text at (String.length text-at)
    else if String.sub text at size=needle then begin
      incr count;Buffer.add_string output replacement;loop(at+size)
    end else begin Buffer.add_char output text.[at];loop(at+1) end in
  loop 0;Buffer.contents output, !count
let is_ox version = snd(replace version "+ox" "")>0
let exact text needle replacement =
  let output,count=replace text needle replacement in
  if count<>1 then invalid_arg "qualified mode declaration changed";
  output
let transform version path =
  let name=Filename.basename path in
  let source=read path in
  let component=Filename.remove_extension name in
  let interface=Filename.extension name=".mli" in
  if (not interface && Filename.extension name<>".ml") ||
     not(List.mem component ["ownedClose";"semanticHash";"semanticFile";"componentHash";"semanticMailbox";"wholeFileClone";"validationSnapshot";
       "formatRecognition";"dngRecognition";"formatExtension";"xmpObservation";
       "xmpMerge";"dngSemantic";"dngExtended";"dngLayout";"dngComponents";"jpegSemantic";"semanticDelta";"semanticWorkers";"semanticFormats"])
  then invalid_arg "unqualified mode-filter module";
  if not(is_ox version) then source
  else if component="ownedClose" then
    let body=exact source "(* ox-portable-operations *)" "@@ portable" in
    let body=exact body "type descriptor\n" "type descriptor : value mod portable contended\n" in
    if not interface then body else
    let body=exact body "(* ox-portable-owner *)" "@@ portable" in
    let body=exact body "  type slot\n" "  type slot : value mod portable contended\n" in
    let body=exact body "  type group\n" "  type group : value mod portable contended\n" in
    let expected="@@ portable\n"^body in
    let template=read(Filename.concat(Filename.dirname path)(component^".ox.mli.in")) in
    if template<>expected then invalid_arg "owned close mode template differs";
    template
  else if component="semanticFormats" then
    if not interface then source else
    let expected=exact source "(module FormatExtension.S) -> unit"
      "(module FormatExtension.S) @ portable contended -> unit" in
    let template=read(Filename.concat(Filename.dirname path)(component^".ox.mli.in")) in
    if template<>expected then invalid_arg "owner mode template differs from qualified interface";
    template
  else if component="semanticWorkers" then
    if interface then source else
    exact source "Domain.spawn (* ox-safe-worker-spawn *)"
      "Domain.Safe.spawn"
  else begin
    let signature_count,field_count = match component,interface with
      | "componentHash",_ -> 0,1
      | "formatRecognition",true -> 1,0
      | "formatRecognition",false -> 1,1
      | "formatExtension",true -> 1,1
      | "formatExtension",false -> 1,2
      | _ -> 0,0 in
    let body,ns=replace source "(* ox-portable-signature *)" "@@ portable contended" in
    let body,nf=replace body "(* ox-portable-field *)" "@@ portable contended" in
    if ns<>signature_count || nf<>field_count then
      invalid_arg "qualified extension mode declarations changed";
    if interface then begin
      let body = if component="componentHash" then
        exact body "type checkpoint\n" "type checkpoint : value mod portable contended\n"
      else if component="semanticMailbox" then
        exact body "type 'a t" "type 'a t : value mod portable contended with 'a"
      else if component="dngComponents" then
        exact (exact (exact body "type decoders\n" "type decoders : value mod portable contended\n")
          "type owner_entry\n" "type owner_entry : value mod portable contended\n")
          "type owner_index\n" "type owner_index : value mod portable contended\n"
      else if component="formatRecognition" || component="formatExtension" then
        exact body "type handle\n" "type handle : value mod portable contended\n"
      else if component="semanticDelta" then
        exact (exact body "type proof\n" "type proof : value mod portable contended\n")
          "type t\n" "type t : value mod portable contended\n"
      else body in
      let body = if component="formatRecognition" || component="formatExtension" then
        let body,_=replace body "(module S)" "(module S) @ portable contended" in
        let body,_=replace body "(module S) @ portable contended option"
          "(module S) option @ contended" in body
      else if component="semanticDelta" then
        fst(replace body "(module FormatExtension.S)"
          "(module FormatExtension.S) @ portable contended")
      else body in
      let owner_declarations = match component with
        | "formatExtension" -> [
          "val resolve : string -> handle option";
          "  ?observer:observer -> ?span_semantics:span_semantics -> (module S) @ portable contended -> unit";
          "val find : string -> (module S) option @ contended";
          "val profiles : unit -> string list";
          "val registered : unit -> handle list"]
        | "componentHash" -> [
          "val metadata_leaf_present : directory:Unix.file_descr -> name:string -> bool";
          "val check_metadata_leaf : directory:Unix.file_descr -> name:string -> max_bytes:int ->\n  Unix.file_descr -> unit";
          "val prepare_metadata_quota : directory:Unix.file_descr -> max_bytes:int64 -> max_entries:int -> metadata_quota";
          "val reserve_metadata_slot : metadata_quota -> Unix.file_descr -> bool";
          "val metadata_slot_reserved : metadata_quota -> bool";
          "val metadata_slot_name : metadata_quota -> string";
          "val open_metadata_stage : metadata_quota -> Unix.file_descr -> metadata_stage -> Unix.file_descr";
          "val metadata_stage_created : metadata_quota -> metadata_stage -> bool";
          "val admit_metadata_stages : metadata_quota -> Unix.file_descr ->\n  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit";
          "val seal_metadata_stages : metadata_quota -> Unix.file_descr ->\n  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit";
          "val record_publication_available : unit -> bool";
          "val prepare_record_publication : directory:Unix.file_descr -> stage:Unix.file_descr ->\n  temporary:string -> expected_binding:string -> expected_record_sha256:string ->\n  SemanticFile.t -> record_publication";
          "val prepare_metadata_publication : directory:Unix.file_descr -> stage:Unix.file_descr ->\n  temporary:string -> max_bytes:int -> expected_sha256:string -> SemanticFile.t -> record_publication";
          "val publish_checkpoint_record : record_publication -> Unix.file_descr -> Unix.file_descr -> unit";
          "val record_published : record_publication -> bool"]
        | "dngComponents" -> [
          "val open_component_source : (unit -> Unix.file_descr) -> component_source";
          "val component_source_descriptor : component_source -> Unix.file_descr";
          "val settle_component_source : component_source -> exn option -> unit";
          "val cache_origin_descriptor : cache_ownership -> cache_descriptor";
          "val open_cache_parent : string -> cache_parent";
          "val check_cache_parent : cache_parent -> unit";
          "val cache_parent_descriptor : cache_parent -> Unix.file_descr";
          "val settle_cache_parent : cache_parent -> exn option -> unit";
          "val managed_cache_store_namespace : managed_cache_store -> int * int";
          "val prepare_managed_cache_store : entry:owner_entry -> checkpoint:ComponentHash.checkpoint ->\n  index:owner_index -> expected_entry_sha256:string option -> binding:string ->\n  max_bytes:int64 -> max_entries:int -> managed_cache_store";
          "val execute_managed_cache_store : managed_cache_store -> namespace:cache_namespace ->\n  parent:Unix.file_descr -> bool";
          "val managed_cache_store_reference : managed_cache_store -> string * string";
          "val managed_cache_store_index : managed_cache_store -> owner_index";
          "val managed_cache_store_effects : managed_cache_store -> bool * bool * bool * bool * bool";
          "val prepare_cache_namespace : ?expected:(int * int) -> parent:Unix.file_descr -> unit -> cache_namespace";
          "val provision_cache_namespace : cache_namespace -> parent:Unix.file_descr -> unit";
          "val cache_namespace_created : cache_namespace -> bool";
          "val cache_namespace_identity : cache_namespace -> int * int";
          "val with_cache_namespace : cache_namespace -> parent:Unix.file_descr ->\n  (Unix.file_descr -> 'a) -> 'a";
          "val load_owner_index : ?check_cancel:(unit -> unit) ->\n  directory:Unix.file_descr -> expected_manifest_sha256:string ->\n  binding:string -> max_entries:int -> max_bytes:int -> unit -> owner_index option";
          "val load_owner_record : ?check_cancel:(unit -> unit) -> directory:Unix.file_descr ->\n  entry:owner_entry -> unit -> string option";
          "val prepare_owner_index_publication : binding:string -> owner_index ->\n  directory:Unix.file_descr -> stage:Unix.file_descr -> temporary:string ->\n  SemanticFile.t -> owner_index_publication";
          "val publish_owner_index : owner_index_publication -> Unix.file_descr -> Unix.file_descr -> unit";
          "val owner_index_published : owner_index_publication -> bool";
          "val owner_index_reference : owner_index_publication -> string * string";
          "val prepare_owner_entry_publication : owner_entry -> directory:Unix.file_descr ->\n  stage:Unix.file_descr -> temporary:string -> SemanticFile.t -> ComponentHash.record_publication";
          "val stage_cache_capture : owner_entry -> checkpoint:ComponentHash.checkpoint ->\n  quota:ComponentHash.metadata_quota -> directory:Unix.file_descr ->\n  record_stage:Unix.file_descr -> entry_stage:Unix.file_descr -> unit";
          "val prepare_cache_capture : owner_entry -> quota:ComponentHash.metadata_quota ->\n  directory:Unix.file_descr -> record_stage:Unix.file_descr -> entry_stage:Unix.file_descr ->\n  record_file:SemanticFile.t -> entry_file:SemanticFile.t -> cache_capture";
          "val publish_cache_capture : cache_capture -> Unix.file_descr -> Unix.file_descr -> Unix.file_descr -> unit";
          "val cache_capture_state : cache_capture -> bool * bool";
          "val inspect_cache_capture : owner_entry -> directory:Unix.file_descr ->\n  record:(Unix.file_descr * SemanticFile.t) option ->\n  index:(Unix.file_descr * SemanticFile.t) option -> capture_recovery";
          "val with_cache_capture : owner_entry -> directory:Unix.file_descr ->\n  record:(Unix.file_descr * SemanticFile.t) option ->\n  index:(Unix.file_descr * SemanticFile.t) option -> decoders:decoders ->\n  max_read_bytes:int64 -> SemanticFile.t ->\n  (ComponentHash.session -> refresh -> 'a) -> ('a, string) result";
          "val with_indexed_capture : owner_index -> root_identity:string -> path:string ->\n  generation_sha256:string -> directory:Unix.file_descr ->\n  record:(Unix.file_descr * SemanticFile.t) option ->\n  index:(Unix.file_descr * SemanticFile.t) option -> decoders:decoders ->\n  max_read_bytes:int64 -> SemanticFile.t ->\n  (ComponentHash.session -> refresh -> 'a) -> ('a, string) result"]
        | "semanticDelta" -> [
          "val apply : t -> basis:SemanticFile.t -> output:Unix.file_descr -> unit";
          "val apply_report : t -> basis:SemanticFile.t -> output:Unix.file_descr -> application"]
        | _ -> [] in
      let body=List.fold_left (fun body declaration ->
        exact body declaration (declaration^" @@ nonportable")) body owner_declarations in
      let expected="@@ portable\n"^body in
      let template=read(Filename.concat(Filename.dirname path)(component^".ox.mli.in")) in
      if template<>expected then invalid_arg "checked mode template differs from qualified interface";
      template
    end else begin
      let expected=match component with "semanticHash" -> 3 | "semanticFile" -> 5 | "validationSnapshot" -> 1 | _ -> 0 in
      let result,count=replace body "(* ox-portable-ffi *)" "@@ portable" in
      if count<>expected then invalid_arg "qualified native mode declarations changed";
      result
    end
  end
let () =
  if Array.length Sys.argv<>3 then invalid_arg "usage: semantic_mode_filter COMPILER_VERSION INPUT";
  let result=transform Sys.argv.(1) Sys.argv.(2) in
  set_binary_mode_out stdout true;
  print_string result
