let describe file =
  match DngSemantic.component_regions file with
  | Error reason -> Error reason
  | Ok regions ->
    let regions=List.sort (fun (a:DngSemantic.component_region) b ->
      Int64.compare a.offset b.offset) regions in
    let rec disjoint stop = function
      | [] -> true
      | (region:DngSemantic.component_region)::rest ->
        region.offset>=stop && disjoint (Int64.add region.offset region.length) rest in
    if not(disjoint 0L regions) then Error "DNG component physical aliases unsupported"
    else
    let children=List.map (fun (region:DngSemantic.component_region) ->
      let role=match region.role with
        | DngSemantic.Image_bytes -> ComponentHash.Encoded_pixels
        | DngSemantic.Standard_value -> ComponentHash.Standard_metadata
        | DngSemantic.Private_value -> ComponentHash.Private_metadata
        | DngSemantic.Structure -> ComponentHash.Structural in
      {ComponentHash.id="dng/"^region.logical_id;schema=region.schema;
       role;offset=region.offset;length=region.length;children=[]}) regions in
    Ok {ComponentHash.id="dng";schema="dng-physical-partition/0";
        role=ComponentHash.Structural;offset=0L;length=SemanticFile.size file;children}

type binding = { component_id : string; decoder : ComponentHash.plugin }
type decoders = binding list
type status = Unmatched | Unsupported of string | Refined
type outcome = { component_id : string; decoder_id : string;
                 implementation_sha256 : string; status : status }
let bounded_id maximum text = text<>"" && String.length text<=maximum
  && not(String.contains text '\000')
let freeze_decoders bindings =
  let descendant parent child =
    let prefix=parent^"/" in
    String.length child>String.length prefix &&
    String.sub child 0 (String.length prefix)=prefix in
  let rec validate count seen = function
    | [] -> Ok bindings
    | (binding:binding)::rest ->
      if count>=64 then Error "DNG decoder binding limit"
      else if not(bounded_id 256 binding.component_id)
        || String.length binding.component_id<4
        || String.sub binding.component_id 0 4<>"dng/" then Error "DNG decoder target ID"
      else if List.mem binding.component_id seen then Error "duplicate DNG decoder target"
      else if List.exists (descendant binding.component_id) seen then
        Error "DNG parent decoder must precede child bindings"
      else if not(bounded_id 128 binding.decoder.id)
        || String.length binding.decoder.implementation_sha256<>32 then Error "DNG decoder provenance"
      else validate (count+1) (binding.component_id::seen) rest in
  validate 0 [] bindings
let rec find id (node:ComponentHash.node) =
  if node.id=id then Some node else
  List.fold_left (fun found child -> match found with Some _ -> found | None -> find id child)
    None node.children
let private_fragment specs =
  (* Bound inspection before handing the fragment to the core's full geometry
     and namespace validation. No unbounded recursive prewalk of plugin output. *)
  let rec visit remaining depth (item:ComponentHash.spec) =
    if remaining<=0 || depth>16 then None else
    match item.role with
    | ComponentHash.Encoded_pixels | ComponentHash.Standard_metadata -> None
    | ComponentHash.Private_metadata | ComponentHash.Opaque | ComponentHash.Structural ->
      children (remaining-1) (depth+1) item.children
  and children remaining depth = function
    | [] -> Some remaining
    | item::rest -> match visit remaining depth item with
      | None -> None | Some remaining -> children remaining depth rest in
  match children 1024 0 specs with Some _ -> true | None -> false
let private_decoder (original:ComponentHash.plugin) =
  {original with ComponentHash.decode=(fun reader ->
    match original.decode reader with
    | Error reason -> Error reason
    | Ok children -> if private_fragment children then Ok children
      else Error "private decoder fragment role/count/depth refused")}
let replace_private_view session snapshot ~component ~expected_schema decoder =
  match find component (ComponentHash.root snapshot) with
  | None -> Error "private replacement target absent"
  | Some node when node.schema<>expected_schema -> Error "private replacement old contract changed"
  | Some node when node.role<>ComponentHash.Private_metadata && node.role<>ComponentHash.Opaque ->
    Error "replacement target is not private or opaque"
  | Some node ->
    let pending=if node.children=[] then snapshot else
      ComponentHash.reset_private_view session snapshot ~component ~schema:"uninterpreted-private/0" in
    ComponentHash.apply_plugin session pending ~component (private_decoder decoder)
let with_checkpoint_base ~expected_checkpoint_sha256 ~max_read_bytes file encoded callback =
  match describe file with
  | Error reason -> Error reason
  | Ok base ->
    Ok(ComponentHash.with_checkpoint ~expected_checkpoint_sha256
      ~expected_root_schema:"dng-physical-partition/0" ~max_read_bytes file encoded
      (fun session snapshot ->
        ComponentHash.validate_base session snapshot base;
        callback session snapshot base))
let with_checkpoint ~expected_checkpoint_sha256 ~max_read_bytes file encoded callback =
  with_checkpoint_base ~expected_checkpoint_sha256 ~max_read_bytes file encoded
    (fun session snapshot _ -> callback session snapshot)
let with_snapshot ~decoders ~max_read_bytes file callback =
  match describe file with
  | Error reason -> Error reason
  | Ok spec ->
    Ok(ComponentHash.with_snapshot ~max_read_bytes file spec (fun session initial ->
      let refined,outcomes=List.fold_left (fun (snapshot,outcomes) (binding:binding) ->
        let outcome status = {component_id=binding.component_id;decoder_id=binding.decoder.id;
          implementation_sha256=binding.decoder.implementation_sha256;status} in
        let retained status = snapshot,outcome status::outcomes in
        match find binding.component_id (ComponentHash.root snapshot) with
        | None -> retained Unmatched
        | Some node when node.children<>[] -> retained (Unsupported "target is already partitioned")
        | Some node when node.role<>ComponentHash.Private_metadata && node.role<>ComponentHash.Opaque ->
          retained (Unsupported "target is not private or opaque")
        | Some _ ->
          let decoder=private_decoder binding.decoder in
          match ComponentHash.apply_plugin session snapshot ~component:binding.component_id decoder with
          | Error reason -> retained (Unsupported reason)
          | Ok refined -> refined,outcome Refined::outcomes
      ) (initial,[]) decoders in
      callback session ~initial ~refined (List.rev outcomes)))

type refresh = { snapshot : ComponentHash.snapshot; outcomes : outcome list;
                 reused : string list; invalidated : string list }
let with_refreshed_checkpoint ~previous ~decoders ~expected_checkpoint_sha256
    ~max_read_bytes file encoded callback =
  with_checkpoint_base ~expected_checkpoint_sha256 ~max_read_bytes file encoded
    (fun session original base ->
      if List.length previous>64 then raise(ComponentHash.Invalid "DNG previous decoder limit");
      let schema (entry:outcome)=entry.decoder_id^"@"^SemanticHash.hex entry.implementation_sha256 in
      let seen=Hashtbl.create 64 in
      let applied=List.filter(fun (entry:outcome) ->
        if not(bounded_id 256 entry.component_id) || not(bounded_id 128 entry.decoder_id) ||
          String.length entry.implementation_sha256<>32 || Hashtbl.mem seen entry.component_id then
          raise(ComponentHash.Invalid "DNG previous decoder provenance");
        Hashtbl.add seen entry.component_id ();
        match entry.status with
        | Unmatched | Unsupported _ -> false
        | Refined ->
          (match find entry.component_id (ComponentHash.root original) with
          | Some node when node.schema=schema entry &&
              (node.role=ComponentHash.Private_metadata || node.role=ComponentHash.Opaque) -> true
          | _ -> raise(ComponentHash.Invalid "DNG historical decoder view mismatch"))) previous in
      let same (entry:outcome) (binding:binding)=entry.component_id=binding.component_id &&
        entry.decoder_id=binding.decoder.id && entry.implementation_sha256=binding.decoder.implementation_sha256 in
      let stale=List.filter(fun entry -> not(List.exists(same entry) decoders)) applied in
      let affected id=List.exists(fun (entry:outcome) ->
        let prefix=entry.component_id^"/" in
        id=entry.component_id || (String.length id>String.length prefix &&
          String.sub id 0 (String.length prefix)=prefix)) stale in
      let reusable=List.filter(fun (entry:outcome) -> not(affected entry.component_id)) applied in
      let stale=List.sort(fun (a:outcome) b -> compare(String.length a.component_id)(String.length b.component_id)) stale in
      let rec base_schema id (spec:ComponentHash.spec)=
        if spec.id=id then Some spec.schema else
        List.fold_left(fun found child -> match found with Some _ -> found | None -> base_schema id child)
          None spec.children in
      let pending=List.fold_left(fun snapshot (entry:outcome) ->
        match find entry.component_id (ComponentHash.root snapshot) with
        | None -> snapshot
        | Some _ -> ComponentHash.reset_private_view session snapshot ~component:entry.component_id
            ~schema:(match base_schema entry.component_id base with Some schema -> schema
              | None -> "uninterpreted-private/0")) original stale in
      let snapshot,outcomes,reused=List.fold_left(fun (snapshot,outcomes,reused) (binding:binding) ->
        let outcome status={component_id=binding.component_id;decoder_id=binding.decoder.id;
          implementation_sha256=binding.decoder.implementation_sha256;status} in
        let retain status=snapshot,outcome status::outcomes,reused in
        match find binding.component_id (ComponentHash.root snapshot) with
        | Some node when List.exists(fun entry -> same entry binding && node.schema=schema entry) reusable ->
          snapshot,outcome Refined::outcomes,binding.component_id::reused
        | None -> retain Unmatched
        | Some node when node.children<>[] -> retain(Unsupported "target is already partitioned")
        | Some node when node.role<>ComponentHash.Private_metadata && node.role<>ComponentHash.Opaque ->
          retain(Unsupported "target is not private or opaque")
        | Some _ ->
          match ComponentHash.apply_plugin session snapshot ~component:binding.component_id
            (private_decoder binding.decoder) with
          | Error reason -> retain(Unsupported reason)
          | Ok next -> next,outcome Refined::outcomes,reused
      ) (pending,[],[]) decoders in
      callback session {snapshot;outcomes=List.rev outcomes;reused=List.rev reused;
        invalidated=List.map(fun (entry:outcome) -> entry.component_id) stale})

type owner_entry = { owner_encoded : string; owner_digest : string;
  owner_binding : string; record_digest : string; checkpoint_digest : string;
  input_digest : string; previous : outcome list;
  owner_root : string; owner_path : string; owner_generation : string }
let owner_entry_bytes entry=entry.owner_encoded
let owner_entry_sha256 entry=entry.owner_digest
let owner_entry_binding entry=entry.owner_binding
let owner_entry_record_sha256 entry=entry.record_digest
let owner_entry_outcomes entry=entry.previous
let owner_entry_max_size=131072
let owner_invalid why=raise(ComponentHash.Invalid("DNG owner entry: "^why))
let owner_number value =
  let bytes=Bytes.create 8 in
  for i=0 to 7 do Bytes.set bytes i (Char.chr(Int64.to_int(Int64.logand 255L
    (Int64.shift_right_logical value (56-8*i))))) done;Bytes.to_string bytes
let owner_string value=owner_number(Int64.of_int(String.length value))^value
let validate_inventory entries =
  if List.length entries>64 then owner_invalid "inventory limit";
  let seen=Hashtbl.create 64 in
  List.iter(fun (entry:outcome) ->
    if not(bounded_id 256 entry.component_id) || String.length entry.component_id<4 ||
      String.sub entry.component_id 0 4<>"dng/" || not(bounded_id 128 entry.decoder_id) ||
      String.length entry.implementation_sha256<>32 || Hashtbl.mem seen entry.component_id then
      owner_invalid "inventory identity";
    Hashtbl.add seen entry.component_id ();
    match entry.status with Unsupported why when String.length why>1024 -> owner_invalid "reason limit"
      | _ -> ()) entries
let owner_inventory entries =
  validate_inventory entries;
  owner_number(Int64.of_int(List.length entries)) ^ String.concat "" (List.map(fun (entry:outcome) ->
    owner_string entry.component_id ^ owner_string entry.decoder_id ^ entry.implementation_sha256 ^
    (match entry.status with Unmatched -> "\000" | Unsupported why -> "\001"^owner_string why | Refined -> "\002")) entries)
let owner_prefix ~root_identity ~path ~generation_sha256 ~input_digest previous =
  if not(bounded_id 4096 root_identity) || not(bounded_id 4096 path) ||
    String.length generation_sha256<>32 || String.length input_digest<>32 then owner_invalid "owner binding";
  "UDI\000\000\000\000\000" ^ owner_string root_identity ^ owner_string path ^
    generation_sha256 ^ input_digest ^ owner_inventory previous
let check_owner_checkpoint checkpoint previous =
  let root=ComponentHash.checkpoint_root checkpoint in
  if root.id<>"dng" || root.schema<>"dng-physical-partition/0" || root.role<>ComponentHash.Structural ||
    root.offset<>0L then owner_invalid "checkpoint format";
  validate_inventory previous;
  let rec safe (node:ComponentHash.node)=
    node.role<>ComponentHash.Encoded_pixels && node.role<>ComponentHash.Standard_metadata &&
    List.for_all safe node.children in
  List.iter(fun (entry:outcome) -> match entry.status with
    | Unmatched | Unsupported _ -> ()
    | Refined -> match find entry.component_id root with
      | Some node when node.schema=entry.decoder_id^"@"^SemanticHash.hex entry.implementation_sha256 &&
          (node.role=ComponentHash.Private_metadata || node.role=ComponentHash.Opaque) && safe node -> ()
      | _ -> owner_invalid "checkpoint/inventory mismatch") previous;
  root.content_sha256
let make_owner_entry ~root_identity ~path ~generation_sha256 ~checkpoint ~outcomes =
  let input_digest=check_owner_checkpoint checkpoint outcomes in
  let prefix=owner_prefix ~root_identity ~path ~generation_sha256 ~input_digest outcomes in
  let owner_binding=SemanticHash.string("unison-dng-owner-binding/0\000"^prefix) in
  let checkpoint_digest=ComponentHash.checkpoint_sha256 checkpoint in
  let record_digest=SemanticHash.string(ComponentHash.checkpoint_record ~binding:owner_binding checkpoint) in
  let owner_encoded=prefix^checkpoint_digest^record_digest in
  {owner_encoded;owner_digest=SemanticHash.string owner_encoded;owner_binding;record_digest;
   checkpoint_digest;input_digest;previous=outcomes;
   owner_root=root_identity;owner_path=path;owner_generation=generation_sha256}
let decode_authenticated_owner_entry ~expected_entry_sha256 encoded =
  if String.length encoded>owner_entry_max_size || String.length expected_entry_sha256<>32 ||
    SemanticHash.string encoded<>expected_entry_sha256 then owner_invalid "digest/size mismatch";
  let at=ref 0 in
  let take n=if n<0 || n>String.length encoded - !at then owner_invalid "truncated entry";
    let value=String.sub encoded !at n in at:= !at+n;value in
  let number maximum =
    let value=ref 0L in
    String.iter(fun c -> value:=Int64.logor(Int64.shift_left !value 8)(Int64.of_int(Char.code c))) (take 8);
    if !value<0L || !value>Int64.of_int maximum then owner_invalid "field limit";
    Int64.to_int !value in
  let string maximum=take(number maximum) in
  if take 8<>"UDI\000\000\000\000\000" then owner_invalid "version";
  let saved_root=string 4096 in let saved_path=string 4096 in
  let generation=take 32 in let input_digest=take 32 in
  let count=number 64 in
  let previous=List.init count(fun _ ->
    let component_id=string 256 in let decoder_id=string 128 in
    let implementation_sha256=take 32 in
    let status=match take 1 with "\000" -> Unmatched | "\001" -> Unsupported(string 1024)
      | "\002" -> Refined | _ -> owner_invalid "status" in
    {component_id;decoder_id;implementation_sha256;status}) in
  let checkpoint_digest=take 32 in let record_digest=take 32 in
  if !at<>String.length encoded then owner_invalid "trailing entry bytes";
  let root_identity=saved_root and path=saved_path and generation_sha256=generation in
  let prefix=owner_prefix ~root_identity ~path ~generation_sha256 ~input_digest previous in
  if encoded<>prefix^checkpoint_digest^record_digest then owner_invalid "noncanonical entry";
  {owner_encoded=encoded;owner_digest=expected_entry_sha256;
   owner_binding=SemanticHash.string("unison-dng-owner-binding/0\000"^prefix);
   record_digest;checkpoint_digest;input_digest;previous;
   owner_root=root_identity;owner_path=path;owner_generation=generation_sha256}
let decode_owner_entry ~root_identity ~path ~generation_sha256 ~expected_entry_sha256 encoded =
  let entry=decode_authenticated_owner_entry ~expected_entry_sha256 encoded in
  if entry.owner_root<>root_identity || entry.owner_path<>path ||
     entry.owner_generation<>generation_sha256 then owner_invalid "root/path/generation mismatch";
  entry
let checkpoint_for_owner_entry entry record =
  let checkpoint=ComponentHash.checkpoint_from_record ~expected_binding:entry.owner_binding
    ~expected_record_sha256:entry.record_digest record in
  if ComponentHash.checkpoint_sha256 checkpoint<>entry.checkpoint_digest ||
    check_owner_checkpoint checkpoint entry.previous<>entry.input_digest then
    owner_invalid "record reference mismatch";
  checkpoint
let write_owner_entry entry output =
  ComponentHash.stage_metadata_bytes ~max_bytes:owner_entry_max_size entry.owner_encoded output
let read_owner_entry ~root_identity ~path ~generation_sha256 ~expected_entry_sha256 file =
  let size=SemanticFile.size file in
  if size<80L || size>Int64.of_int owner_entry_max_size then owner_invalid "input size";
  let bytes=Buffer.create(Int64.to_int size) in
  SemanticFile.iter file 0L size (fun data count -> Buffer.add_subbytes bytes data 0 count);
  SemanticFile.check file;
  decode_owner_entry ~root_identity ~path ~generation_sha256 ~expected_entry_sha256 (Buffer.contents bytes)
let prepare_owner_entry_publication entry ~directory ~stage ~temporary file =
  ComponentHash.prepare_metadata_publication ~directory ~stage ~temporary
    ~max_bytes:owner_entry_max_size ~expected_sha256:entry.owner_digest file

type cache_capture = { record_publication : ComponentHash.record_publication;
  entry_publication : ComponentHash.record_publication; mutable publish_attempted : bool }
let capture_names quota =
  let slot=ComponentHash.metadata_slot_name quota in slot^"-record.tmp",slot^"-entry.tmp"
let stage_cache_capture entry ~checkpoint ~quota ~directory ~record_stage ~entry_stage =
  let record=ComponentHash.checkpoint_record ~binding:entry.owner_binding checkpoint in
  ignore(checkpoint_for_owner_entry entry record);
  if entry.record_digest=entry.owner_digest then owner_invalid "record/index target alias";
  ComponentHash.admit_metadata_stages quota directory ~record_stage ~entry_stage;
  if ComponentHash.write_checkpoint_record ~binding:entry.owner_binding checkpoint record_stage<>entry.record_digest then
    owner_invalid "record staging digest";
  if write_owner_entry entry entry_stage<>entry.owner_digest then owner_invalid "entry staging digest"
let prepare_cache_capture entry ~quota ~directory ~record_stage ~entry_stage ~record_file ~entry_file =
  ComponentHash.seal_metadata_stages quota directory ~record_stage ~entry_stage;
  let record_temporary,entry_temporary=capture_names quota in
  let record_publication=ComponentHash.prepare_record_publication ~directory ~stage:record_stage
    ~temporary:record_temporary ~expected_binding:entry.owner_binding
    ~expected_record_sha256:entry.record_digest record_file in
  let entry_publication=prepare_owner_entry_publication entry ~directory ~stage:entry_stage
    ~temporary:entry_temporary entry_file in
  {record_publication;entry_publication;publish_attempted=false}
let publish_cache_capture capture directory record_stage entry_stage =
  if capture.publish_attempted then owner_invalid "capture publication already attempted";
  capture.publish_attempted<-true;
  ComponentHash.publish_checkpoint_record capture.record_publication directory record_stage;
  ComponentHash.publish_checkpoint_record capture.entry_publication directory entry_stage
let cache_capture_state capture =
  ComponentHash.record_published capture.record_publication,
  ComponentHash.record_published capture.entry_publication

type capture_recovery = Capture_missing | Capture_entry_only
  | Capture_record_only of ComponentHash.checkpoint | Capture_complete of ComponentHash.checkpoint
let inspect_cache_capture entry ~directory ~record ~index =
  let record_name=SemanticHash.hex entry.record_digest and index_name=SemanticHash.hex entry.owner_digest in
  let exists name=ComponentHash.metadata_leaf_present ~directory ~name in
  let supplied = function None -> false | Some _ -> true in
  let record_present=exists record_name and index_present=exists index_name in
  if record_present<>supplied record || index_present<>supplied index then
    owner_invalid "lookup evidence does not match namespace";
  let check name maximum (fd,file) =
    if not(SemanticFile.same_inode file fd) then owner_invalid "lookup reader/descriptor mismatch";
    SemanticFile.check file;
    ComponentHash.check_metadata_leaf ~directory ~name ~max_bytes:maximum fd in
  let checkpoint=match record with
    | None -> None
    | Some pair ->
      check record_name (ComponentHash.max_checkpoint_size+80) pair;
      let checkpoint=ComponentHash.read_checkpoint_record ~expected_binding:entry.owner_binding
        ~expected_record_sha256:entry.record_digest (snd pair) in
      if ComponentHash.checkpoint_sha256 checkpoint<>entry.checkpoint_digest ||
        check_owner_checkpoint checkpoint entry.previous<>entry.input_digest then owner_invalid "lookup record reference";
      Some checkpoint in
  (match index with
    | None -> ()
    | Some pair ->
      check index_name owner_entry_max_size pair;
      let file=snd pair in
      if SemanticFile.size file<>Int64.of_int(String.length entry.owner_encoded) ||
        SemanticFile.read file 0L (String.length entry.owner_encoded)<>entry.owner_encoded then
        owner_invalid "lookup index bytes differ");
  (match record with None -> () | Some pair -> check record_name (ComponentHash.max_checkpoint_size+80) pair);
  (match index with None -> () | Some pair -> check index_name owner_entry_max_size pair);
  if exists record_name<>record_present || exists index_name<>index_present then owner_invalid "lookup namespace changed";
  match checkpoint,index_present with
  | None,false -> Capture_missing | None,true -> Capture_entry_only
  | Some checkpoint,false -> Capture_record_only checkpoint
  | Some checkpoint,true -> Capture_complete checkpoint

let with_cache_capture entry ~directory ~record ~index ~decoders ~max_read_bytes file callback =
  match inspect_cache_capture entry ~directory ~record ~index with
  | Capture_missing -> Error "component cache capture missing"
  | Capture_entry_only -> Error "component cache capture record missing"
  | Capture_record_only _ -> Error "component cache capture index missing"
  | Capture_complete checkpoint ->
    with_refreshed_checkpoint ~previous:entry.previous ~decoders
      ~expected_checkpoint_sha256:entry.checkpoint_digest ~max_read_bytes file
      (ComponentHash.checkpoint_bytes checkpoint) callback


type owner_index = { indexed : ((string * string) * owner_entry) list;
  indexed_bytes : int; entry_limit : int; byte_limit : int }
let empty_owner_index ~max_entries ~max_bytes =
  if max_entries<1 || max_entries>1024 || max_bytes<80 || max_bytes>8388608 then
    invalid_arg "DNG owner index limits";
  {indexed=[];indexed_bytes=0;entry_limit=max_entries;byte_limit=max_bytes}
let owner_index_usage index=List.length index.indexed,index.indexed_bytes
let owner_key ~root_identity ~path =
  if not(bounded_id 4096 root_identity) || not(bounded_id 4096 path) then
    owner_invalid "index root/path";
  root_identity,path
let select_owner_entry index ~root_identity ~path ~generation_sha256 =
  let key=owner_key ~root_identity ~path in
  if String.length generation_sha256<>32 then owner_invalid "index generation";
  match List.assoc_opt key index.indexed with
  | Some entry when entry.owner_generation=generation_sha256 -> Some entry
  | None | Some _ -> None
let owner_entry_reference index ~root_identity ~path =
  let key=owner_key ~root_identity ~path in
  Option.map (fun entry -> entry.owner_digest) (List.assoc_opt key index.indexed)
let replace_owner_entry index ~expected_entry_sha256 entry =
  let key=entry.owner_root,entry.owner_path in
  let old=List.assoc_opt key index.indexed in
  let matches=match old,expected_entry_sha256 with
    | None,None -> true
    | Some old,Some expected -> String.length expected=32 && old.owner_digest=expected
    | _ -> false in
  if not matches then Error "component owner index compare-and-replace refused"
  else
    let remaining=List.remove_assoc key index.indexed in
    let bytes=index.indexed_bytes + String.length entry.owner_encoded -
      (match old with None -> 0 | Some old -> String.length old.owner_encoded) in
    if List.length remaining>=index.entry_limit || bytes>index.byte_limit then
      Error "component owner index capacity exhausted"
    else Ok {index with indexed=List.sort(fun (a,_) (b,_) -> compare a b)
      ((key,entry)::remaining);indexed_bytes=bytes}
let remove_owner_entry index ~root_identity ~path ~expected_entry_sha256 =
  let key=owner_key ~root_identity ~path in
  match List.assoc_opt key index.indexed with
  | Some old when String.length expected_entry_sha256=32 && old.owner_digest=expected_entry_sha256 ->
    Ok {index with indexed=List.remove_assoc key index.indexed;
      indexed_bytes=index.indexed_bytes-String.length old.owner_encoded}
  | None | Some _ -> Error "component owner index compare-and-remove refused"

let with_indexed_capture ledger ~root_identity ~path ~generation_sha256
    ~directory ~record ~index ~decoders ~max_read_bytes file callback =
  match select_owner_entry ledger ~root_identity ~path ~generation_sha256 with
  | None -> Error "component owner index has no current entry"
  | Some entry -> with_cache_capture entry ~directory ~record ~index ~decoders ~max_read_bytes file callback


let max_owner_index_size=80+32*1024
let owner_index_bytes ~binding index =
  if String.length binding<>32 then owner_invalid "index manifest binding";
  "UIX\000\000\000\000\000" ^ binding ^ owner_number(Int64.of_int index.entry_limit) ^
  owner_number(Int64.of_int index.byte_limit) ^ owner_number(Int64.of_int(List.length index.indexed)) ^
  owner_number(Int64.of_int index.indexed_bytes) ^ owner_number 0L ^
  String.concat "" (List.map(fun (_,entry) -> entry.owner_digest) index.indexed)
let restore_owner_index ?(check_cancel=fun () -> ()) ~expected_manifest_sha256 ~binding
    ~max_entries ~max_bytes ~load_entry encoded =
  ignore(empty_owner_index ~max_entries ~max_bytes);
  check_cancel ();
  if String.length encoded<80 || String.length encoded>max_owner_index_size ||
     String.length expected_manifest_sha256<>32 || String.length binding<>32 ||
     SemanticHash.string encoded<>expected_manifest_sha256 then owner_invalid "index manifest digest/size";
  let at=ref 0 in
  let take length =
    if length<0 || length>String.length encoded - !at then owner_invalid "truncated index manifest";
    let value=String.sub encoded !at length in at:= !at+length;value in
  let number maximum =
    let value=ref 0L in
    String.iter(fun c -> value:=Int64.logor(Int64.shift_left !value 8)(Int64.of_int(Char.code c))) (take 8);
    if !value<0L || !value>Int64.of_int maximum then owner_invalid "index manifest integer";
    Int64.to_int !value in
  if take 8<>"UIX\000\000\000\000\000" || take 32<>binding then owner_invalid "index manifest binding/version";
  let entries=number 1024 in let bytes=number 8388608 in
  let count=number max_entries in let payload=number max_bytes in
  let reserved=number 0 in
  if entries<>max_entries || bytes<>max_bytes || reserved<>0 ||
     String.length encoded<>80+32*count then owner_invalid "index manifest policy/framing";
  if payload<count*80 || (count=0 && payload<>0) then owner_invalid "index manifest payload minimum";
  let seen=Hashtbl.create count in
  let references=List.init count(fun _ ->
    let digest=take 32 in
    if Hashtbl.mem seen digest then owner_invalid "duplicate index reference";
    Hashtbl.add seen digest ();digest) in
  let rec load previous total acc = function
    | [] ->
      if total<>payload then owner_invalid "index manifest payload accounting";
      {indexed=List.rev acc;indexed_bytes=total;entry_limit=max_entries;byte_limit=max_bytes}
    | expected_entry_sha256::rest ->
      check_cancel ();
      let entry_bytes=load_entry expected_entry_sha256 in
      let length=String.length entry_bytes in
      if length>owner_entry_max_size || length>payload-total then owner_invalid "index entry payload budget";
      let entry=decode_authenticated_owner_entry ~expected_entry_sha256 entry_bytes in
      let key=entry.owner_root,entry.owner_path in
      (match previous with Some old when compare old key>=0 -> owner_invalid "index entry key order/duplicate"
        | None | Some _ -> ());
      check_cancel ();
      load (Some key) (total+length) ((key,entry)::acc) rest in
  let restored=load None 0 [] references in
  check_cancel ();restored


let write_owner_index ~binding ledger output =
  ComponentHash.stage_metadata_bytes ~max_bytes:max_owner_index_size
    (owner_index_bytes ~binding ledger) output
let read_owner_index ?(check_cancel=fun () -> ()) ~expected_manifest_sha256 ~binding
    ~max_entries ~max_bytes ~load_entry file =
  check_cancel ();
  let size=SemanticFile.size file in
  if size<80L || size>Int64.of_int max_owner_index_size then owner_invalid "index manifest input size";
  let encoded=SemanticFile.read file 0L (Int64.to_int size) in
  SemanticFile.check file;
  let restored=restore_owner_index ~check_cancel ~expected_manifest_sha256 ~binding
    ~max_entries ~max_bytes ~load_entry encoded in
  SemanticFile.check file;check_cancel ();restored

type owner_index_publication = { manifest_publication : ComponentHash.record_publication;
  mutable manifest_attempted : bool; mutable manifest_completed : bool;
  manifest_binding : string; manifest_digest : string }
let prepare_owner_index_publication ~binding ledger ~directory ~stage ~temporary file =
  let encoded=owner_index_bytes ~binding ledger in
  let manifest_digest=SemanticHash.string encoded in
  let manifest_publication=ComponentHash.prepare_metadata_publication ~directory ~stage ~temporary
    ~max_bytes:max_owner_index_size ~expected_sha256:manifest_digest file in
  {manifest_publication;manifest_attempted=false;manifest_completed=false;
   manifest_binding=binding;manifest_digest}
let publish_owner_index publication directory stage =
  if publication.manifest_attempted then owner_invalid "index publication already attempted";
  publication.manifest_attempted<-true;
  ComponentHash.publish_checkpoint_record publication.manifest_publication directory stage;
  publication.manifest_completed<-true
let owner_index_published publication=ComponentHash.record_published publication.manifest_publication

let owner_index_reference publication =
  if not publication.manifest_completed || not(owner_index_published publication) then
    owner_invalid "index publication has not completed normally";
  publication.manifest_binding,publication.manifest_digest
let owner_archive_reference_size=136
let encode_owner_archive_reference ~archive_binding ~binding ~manifest_sha256 =
  if String.length archive_binding<>32 || String.length binding<>32 || String.length manifest_sha256<>32 then
    owner_invalid "archive reference binding";
  let body="UAX\000\000\000\000\000"^archive_binding^binding^manifest_sha256 in
  body^SemanticHash.string body
let decode_owner_archive_reference ~archive_binding encoded =
  if String.length archive_binding<>32 then owner_invalid "archive reference context";
  if String.length encoded<>owner_archive_reference_size ||
     String.sub encoded 0 8<>"UAX\000\000\000\000\000" ||
     String.sub encoded 8 32<>archive_binding ||
     SemanticHash.string(String.sub encoded 0 104)<>String.sub encoded 104 32 then None
  else Some(String.sub encoded 40 32,String.sub encoded 72 32)

(* Optional identity tail binds the namespace to this exact archive/head. *)
let owner_namespace_reference_size=152
let encode_owner_namespace_reference ~archive_binding ~binding ~manifest_sha256 (dev,ino) =
  if String.length archive_binding<>32 || String.length binding<>32 ||
     String.length manifest_sha256<>32 || dev<0 || ino<0 then owner_invalid "namespace reference binding";
  let number n=String.init 8 (fun i -> Char.chr(Int64.to_int(Int64.logand 255L
    (Int64.shift_right_logical (Int64.of_int n) ((7-i)*8))))) in
  let body="UAN\000\000\000\000\000"^archive_binding^binding^manifest_sha256^number dev^number ino in
  body^SemanticHash.string body
let decode_owner_namespace_reference ~archive_binding ~binding ~manifest_sha256 encoded =
  if String.length archive_binding<>32 || String.length binding<>32 || String.length manifest_sha256<>32 then
    owner_invalid "namespace reference context";
  if String.length encoded<>owner_namespace_reference_size ||
     String.sub encoded 0 8<>"UAN\000\000\000\000\000" ||
     String.sub encoded 8 32<>archive_binding || String.sub encoded 40 32<>binding ||
     String.sub encoded 72 32<>manifest_sha256 ||
     SemanticHash.string(String.sub encoded 0 120)<>String.sub encoded 120 32 then None else
  let number at=let n=ref 0L in
    for i=0 to 7 do n:=Int64.logor (Int64.shift_left !n 8)
      (Int64.of_int(Char.code encoded.[at+i])) done;
    if !n<0L || !n>Int64.of_int max_int then None else Some(Int64.to_int !n) in
  match number 104,number 112 with Some dev,Some ino -> Some(dev,ino) | _ -> None

(* Owner-only managed reads. Resource bookkeeping exists before native open;
   borrowed readers never duplicate/close it. Uncertainty never retries a number
   that the OS may already have recycled. *)
external metadata_open : Unix.file_descr -> string -> Unix.file_descr
  = "unison_component_metadata_open"
external metadata_close : Unix.file_descr -> unit = "unison_component_metadata_close"
type cache_descriptor = Unix.file_descr * Unix.LargeFile.stats option
type cache_ownership = { cache_cause : exn option;
  cache_uncertain : (cache_descriptor * exn) list;
  cache_retained : cache_descriptor list;
  cache_directory : cache_descriptor; cache_parents : cache_descriptor list }
exception Cache_ownership_uncertain of cache_ownership
let cache_ownership_cause state=state.cache_cause
let cache_uncertain_descriptors state=state.cache_uncertain
let cache_retained_descriptors state=state.cache_retained
let cache_borrowed_directory state=state.cache_directory
let cache_borrowed_directories state=state.cache_directory::state.cache_parents
type cache_fd_state = Cache_unopened | Cache_held | Cache_uncertain | Cache_closed
type cache_resource = { mutable cache_fd : Unix.file_descr;
  mutable cache_fd_state : cache_fd_state; mutable cache_identity : Unix.LargeFile.stats option }
let cache_identity fd=try Some(Unix.LargeFile.fstat fd) with _ -> None
let with_cache_descriptor ~directory ~allow_missing ~open_descriptor ~validate callback =
  let borrowed=directory,cache_identity directory in
  let resource={cache_fd=Unix.stdin;cache_fd_state=Cache_unopened;cache_identity=None} in
  let evidence ()=resource.cache_fd,resource.cache_identity in
  let close cause =
    (* A failed final stat must not erase the identity already observed at open. *)
    (match cache_identity resource.cache_fd with
     | None -> () | Some _ as observed -> resource.cache_identity <- observed);
    resource.cache_fd_state <- Cache_uncertain;
    try metadata_close resource.cache_fd;resource.cache_fd_state <- Cache_closed
    with error -> raise(Cache_ownership_uncertain {cache_cause=cause;
      cache_uncertain=[evidence (),error];cache_retained=[];cache_directory=borrowed;cache_parents=[]}) in
  try
    let present=try
      resource.cache_fd <- open_descriptor ();
      resource.cache_fd_state <- Cache_held;
      true
    with Unix.Unix_error(Unix.ENOENT,_,_) when allow_missing -> false in
    if not present then None else begin
      resource.cache_identity <- Some(Unix.LargeFile.fstat resource.cache_fd);
      validate resource.cache_fd;
      let result=callback resource.cache_fd in
      validate resource.cache_fd;
      close None;
      Some result
    end
  with
  | Cache_ownership_uncertain state ->
      (* A nested leaf could fail close while this manifest is still held.
         Preserve that known descriptor instead of attempting more cleanup. *)
      let same (a,identity_a) (b,identity_b)=a=b &&
        (match identity_a,identity_b with
         | Some a,Some b -> a.Unix.LargeFile.st_dev=b.Unix.LargeFile.st_dev && a.st_ino=b.st_ino
         | None,None -> true | _ -> false) in
      let parents=if List.exists (same borrowed) (cache_borrowed_directories state)
        then state.cache_parents else borrowed::state.cache_parents in
      let retained=if resource.cache_fd_state=Cache_held &&
        not(List.exists (same(evidence ())) state.cache_retained)
        then evidence ()::state.cache_retained else state.cache_retained in
      raise(Cache_ownership_uncertain {state with cache_retained=retained;cache_parents=parents})
  | error ->
      if resource.cache_fd_state=Cache_held then close (Some error);
      raise error
let with_cache_leaf ~check_cancel ~directory ~digest ~max_bytes callback =
  check_cancel ();
  if String.length digest<>32 then owner_invalid "cache leaf digest";
  let name=SemanticHash.hex digest in
  with_cache_descriptor ~directory ~allow_missing:true
    ~open_descriptor:(fun () -> metadata_open directory name)
    ~validate:(fun fd -> ComponentHash.check_metadata_leaf ~directory ~name ~max_bytes fd)
    (fun fd -> SemanticFile.with_borrowed_fd ~check_cancel fd callback)
let cache_leaf_bytes file =
  let size=SemanticFile.size file in
  let bytes=Buffer.create (Int64.to_int size) in
  SemanticFile.iter file 0L size (fun data count -> Buffer.add_subbytes bytes data 0 count);
  SemanticFile.check file;
  Buffer.contents bytes
let load_owner_index ?(check_cancel=fun () -> ()) ~directory ~expected_manifest_sha256 ~binding ~max_entries ~max_bytes () =
  (* Validate caller bounds even when the selected manifest is absent. *)
  ignore(empty_owner_index ~max_entries ~max_bytes);
  if String.length binding<>32 then owner_invalid "cache manifest binding";
  with_cache_leaf ~check_cancel ~directory ~digest:expected_manifest_sha256 ~max_bytes:max_owner_index_size
    (fun file -> read_owner_index ~check_cancel ~expected_manifest_sha256 ~binding ~max_entries ~max_bytes
      ~load_entry:(fun digest -> match with_cache_leaf ~check_cancel ~directory ~digest
        ~max_bytes:owner_entry_max_size cache_leaf_bytes with
        | Some bytes -> bytes | None -> owner_invalid "selected manifest entry is missing") file)
let load_owner_record ?(check_cancel=fun () -> ()) ~directory ~entry () =
  with_cache_leaf ~check_cancel ~directory ~digest:entry.record_digest
    ~max_bytes:(ComponentHash.max_checkpoint_size+80) (fun file ->
      let bytes=cache_leaf_bytes file in
      ignore(checkpoint_for_owner_entry entry bytes);
      bytes)

type cache_namespace
let cache_namespace_name="component-cache-v0"
external prepare_cache_namespace_raw : Unix.file_descr -> (int * int) option -> cache_namespace
  = "unison_component_namespace_prepare"
external provision_cache_namespace : cache_namespace -> parent:Unix.file_descr -> unit
  = "unison_component_namespace_provision"
external cache_namespace_created : cache_namespace -> bool = "unison_component_namespace_created"
external cache_namespace_identity : cache_namespace -> int * int = "unison_component_namespace_identity"
external open_cache_namespace : cache_namespace -> Unix.file_descr -> Unix.file_descr
  = "unison_component_namespace_open"
external check_cache_namespace : cache_namespace -> Unix.file_descr -> Unix.file_descr -> unit
  = "unison_component_namespace_check"
let prepare_cache_namespace ?expected ~parent ()=prepare_cache_namespace_raw parent expected
let with_cache_namespace ticket ~parent callback =
  match with_cache_descriptor ~directory:parent ~allow_missing:false
    ~open_descriptor:(fun () -> open_cache_namespace ticket parent)
    ~validate:(check_cache_namespace ticket parent) callback with
  | Some result -> result | None -> assert false


(* A store ticket freezes the next manifest before any namespace mutation. The
   completed bit is set only outside every owned descriptor scope. *)
type managed_cache_store = {
  store_entry : owner_entry; store_checkpoint : ComponentHash.checkpoint;
  store_index : owner_index; store_binding : string;
  store_max_bytes : int64; store_max_entries : int;
  mutable store_attempted : bool; mutable store_quota : ComponentHash.metadata_quota option;
  mutable store_capture : cache_capture option;
  mutable store_manifest : owner_index_publication option;
  mutable store_completed : bool; mutable store_namespace : (int * int) option;
}
let prepare_managed_cache_store ~entry ~checkpoint ~index ~expected_entry_sha256
    ~binding ~max_bytes ~max_entries =
  if String.length binding<>32 || max_bytes<2097152L || max_bytes>8589934592L ||
     max_entries<1 || max_entries>4096 then owner_invalid "managed store bounds/binding";
  ignore(checkpoint_for_owner_entry entry
    (ComponentHash.checkpoint_record ~binding:entry.owner_binding checkpoint));
  let next=match replace_owner_entry index ~expected_entry_sha256 entry with
    | Ok next -> next | Error reason -> owner_invalid reason in
  ignore(owner_index_bytes ~binding next);
  {store_entry=entry;store_checkpoint=checkpoint;store_index=next;store_binding=binding;
   store_max_bytes=max_bytes;store_max_entries=max_entries;store_attempted=false;
   store_quota=None;store_capture=None;store_manifest=None;store_completed=false;store_namespace=None}
let execute_managed_cache_store store ~namespace ~parent =
  if store.store_attempted then owner_invalid "managed store already attempted";
  store.store_attempted<-true;
  store.store_namespace<-Some(cache_namespace_identity namespace);
  let committed=with_cache_namespace namespace ~parent (fun directory ->
    let quota=ComponentHash.prepare_metadata_quota ~directory
      ~max_bytes:store.store_max_bytes ~max_entries:store.store_max_entries in
    store.store_quota<-Some quota;
    if not(ComponentHash.reserve_metadata_slot quota directory) then false else
    let stage role callback =
      (* Stage content/name is authenticated by publication preparation. Initial
         generic checks reject altered permissions/type before any writer runs. *)
      match with_cache_descriptor ~directory ~allow_missing:false
        ~open_descriptor:(fun () -> ComponentHash.open_metadata_stage quota directory role)
        ~validate:(fun fd ->
          let stat=Unix.LargeFile.fstat fd in
          if stat.Unix.LargeFile.st_kind<>Unix.S_REG || stat.st_perm<>0o600 ||
             stat.st_uid<>Unix.getuid () || stat.st_nlink<>1 then
            owner_invalid "managed stage identity/permissions") callback with
      | Some result -> result | None -> assert false in
    stage ComponentHash.Record_stage (fun record_stage ->
      stage ComponentHash.Entry_stage (fun entry_stage ->
        stage_cache_capture store.store_entry ~checkpoint:store.store_checkpoint
          ~quota ~directory ~record_stage ~entry_stage;
        let capture=SemanticFile.with_borrowed_fd record_stage (fun record_file ->
          SemanticFile.with_borrowed_fd entry_stage (fun entry_file ->
            prepare_cache_capture store.store_entry ~quota ~directory
              ~record_stage ~entry_stage ~record_file ~entry_file)) in
        store.store_capture<-Some capture;
        publish_cache_capture capture directory record_stage entry_stage));
    stage ComponentHash.Manifest_stage (fun manifest_stage ->
      ignore(write_owner_index ~binding:store.store_binding store.store_index manifest_stage);
      let publication=SemanticFile.with_borrowed_fd manifest_stage (fun file ->
        let temporary=ComponentHash.metadata_slot_name quota^"-manifest.tmp" in
        prepare_owner_index_publication ~binding:store.store_binding
          store.store_index ~directory ~stage:manifest_stage ~temporary file) in
      store.store_manifest<-Some publication;
      publish_owner_index publication directory manifest_stage);
    true) in
  store.store_completed<-committed;
  committed
let managed_cache_store_reference store =
  if not store.store_completed then owner_invalid "managed store has not settled normally";
  match store.store_manifest with Some publication -> owner_index_reference publication
    | None -> assert false
let managed_cache_store_index store =
  ignore(managed_cache_store_reference store);store.store_index
let managed_cache_store_effects store =
  let reserved=match store.store_quota with None -> false
    | Some quota -> ComponentHash.metadata_slot_reserved quota in
  let record,entry=match store.store_capture with None -> false,false
    | Some capture -> cache_capture_state capture in
  let manifest=match store.store_manifest with None -> false
    | Some publication -> owner_index_published publication in
  reserved,record,entry,manifest,store.store_completed

let managed_cache_store_namespace store =
  ignore(managed_cache_store_reference store);
  match store.store_namespace with Some identity -> identity | None -> assert false


(* Explicit asynchronous owner: caller must settle once, including error paths. *)
external cache_parent_open : string -> Unix.file_descr = "unison_component_parent_open"
type cache_parent = { parent_resource : cache_resource; parent_path : string }
let parent_evidence parent =
  let r=parent.parent_resource in r.cache_fd,r.cache_identity
let check_cache_parent parent =
  let r=parent.parent_resource in
  if r.cache_fd_state<>Cache_held then owner_invalid "cache parent is not held";
  let observed=Unix.LargeFile.fstat r.cache_fd in
  r.cache_identity<-Some observed;
  let named=Unix.LargeFile.lstat parent.parent_path in
  if observed.Unix.LargeFile.st_kind<>Unix.S_DIR || observed.st_uid<>Unix.getuid() ||
     observed.st_perm<>0o700 || named.st_kind<>Unix.S_DIR || named.st_dev<>observed.st_dev ||
     named.st_ino<>observed.st_ino || named.st_perm<>observed.st_perm || named.st_uid<>observed.st_uid then
    owner_invalid "cache parent path/descriptor binding"
let settle_owned_component close_descriptor parent cause =
  let r=parent.parent_resource in
  if r.cache_fd_state<>Cache_held then owner_invalid "cache parent settlement already consumed";
  match cause with
  | Some(Cache_ownership_uncertain state) ->
    (* This known descriptor stays open; the carrier is now its sole owner. *)
    r.cache_fd_state<-Cache_uncertain;
    let evidence=parent_evidence parent in
    let retained=if List.exists(fun (fd,_) -> fd=r.cache_fd) state.cache_retained
      then state.cache_retained else evidence::state.cache_retained in
    raise(Cache_ownership_uncertain {state with cache_retained=retained})
  | _ ->
    (match cache_identity r.cache_fd with None -> () | Some _ as identity -> r.cache_identity<-identity);
    r.cache_fd_state<-Cache_uncertain;
    (try close_descriptor r.cache_fd;r.cache_fd_state<-Cache_closed
     with error -> raise(Cache_ownership_uncertain {cache_cause=cause;
       cache_uncertain=[parent_evidence parent,error];cache_retained=[];
       cache_directory=parent_evidence parent;cache_parents=[]}));
    (match cause with None -> () | Some error -> raise error)
let settle_cache_parent parent cause=settle_owned_component metadata_close parent cause
let open_cache_parent path =
  let parent={parent_path=path;parent_resource={cache_fd=Unix.stdin;
    cache_fd_state=Cache_unopened;cache_identity=None}} in
  parent.parent_resource.cache_fd<-cache_parent_open path;
  parent.parent_resource.cache_fd_state<-Cache_held;
  (try check_cache_parent parent with error -> settle_cache_parent parent (Some error));
  parent
let cache_parent_descriptor parent =
  check_cache_parent parent;parent.parent_resource.cache_fd


(* Component source ownership uses the same close-once carrier. Its origin is
   a regular input descriptor, not a borrowed metadata directory. *)
type component_source = cache_parent
external component_source_close : Unix.file_descr -> unit = "unison_component_source_close"
let settle_component_source owner cause =
  let close=if Sys.os_type="Win32" then Unix.close else component_source_close in
  settle_owned_component close owner cause
let open_component_source open_descriptor =
  let owner={parent_path="";parent_resource={cache_fd=Unix.stdin;
    cache_fd_state=Cache_unopened;cache_identity=None}} in
  let r=owner.parent_resource in
  r.cache_fd<-open_descriptor ();r.cache_fd_state<-Cache_held;
  (try
    let stat=Unix.LargeFile.fstat r.cache_fd in r.cache_identity<-Some stat;
    if stat.Unix.LargeFile.st_kind<>Unix.S_REG then owner_invalid "component source is not regular"
   with error -> settle_component_source owner (Some error));
  owner
let component_source_descriptor owner =
  if owner.parent_resource.cache_fd_state<>Cache_held then owner_invalid "component source is not held";
  owner.parent_resource.cache_fd
let cache_origin_descriptor state=state.cache_directory
