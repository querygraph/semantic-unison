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
