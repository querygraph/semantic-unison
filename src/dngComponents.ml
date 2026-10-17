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
