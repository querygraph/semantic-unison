type role = Encoded_pixels | Standard_metadata | Private_metadata | Structural | Opaque
type spec = { id : string; schema : string; role : role;
              offset : int64; length : int64; children : spec list }
type node = { id : string; schema : string; role : role;
              offset : int64; length : int64; content_sha256 : string;
              view_sha256 : string; children : node list }
type token = unit ref
type snapshot = { token : token; tree : node }
type session = { token : token; file : SemanticFile.t; mutable active : bool;
                 mutable remaining : int64; mutable requested : int64 }
type reader = { session : session; origin : int64; length : int64; mutable active : bool;
                parent : reader option; level : int }
type plugin = { id : string; implementation_sha256 : string;
                decode : reader -> (spec list, string) result (* ox-portable-field *) }
type projection = { sha256 : string; components : int; bytes : int64 }
exception Invalid of string
let invalid reason = raise (Invalid reason)
let valid_id value = value<>"" && String.length value<=256 && not(String.contains value '\000')
let require_id value = if not(valid_id value) then invalid "bounded nonempty component identifier required"
let role_id = function Encoded_pixels -> "encoded-pixels" | Standard_metadata -> "standard-metadata"
  | Private_metadata -> "private-metadata" | Structural -> "structural" | Opaque -> "opaque"
let feed hash text = SemanticHash.feed hash (Bytes.of_string text) 0 (String.length text)
let integer value =
  let bytes=Bytes.create 8 in
  for j=0 to 7 do Bytes.set bytes j (Char.chr(Int64.to_int(Int64.logand 255L
    (Int64.shift_right_logical value (56-8*j))))) done;
  Bytes.to_string bytes
let field hash text = feed hash (integer(Int64.of_int(String.length text))); feed hash text
let view id schema role length content children =
  let hash=SemanticHash.create () in
  field hash "unison-component-view/0"; field hash id; field hash schema;
  field hash (role_id role); feed hash (integer length);
  feed hash (integer(Int64.of_int(List.length children)));
  if children=[] then field hash content
  else List.iter (fun (child:node) -> field hash child.view_sha256) children;
  SemanticHash.finish hash
let root snapshot = snapshot.tree
let full_sha256 snapshot = snapshot.tree.content_sha256
let rec fold f acc node = List.fold_left (fold f) (f acc node) node.children
let layout_sha256 snapshot =
  let hash=SemanticHash.create () in field hash "unison-component-layout/0";
  ignore(fold (fun () (node:node) -> field hash node.id;field hash node.schema;
    field hash (role_id node.role);feed hash(integer node.offset);feed hash(integer node.length);
    feed hash(integer(Int64.of_int(List.length node.children)));field hash node.view_sha256) () snapshot.tree);
  SemanticHash.finish hash
let projection snapshot role =
  let selected=fold (fun acc (node:node) ->
    if node.children=[] && node.role=role && node.length>0L then node::acc else acc) [] snapshot.tree in
  let selected=List.sort(fun (a:node) b -> String.compare a.id b.id) selected in
  if selected=[] then None else
  let hash=SemanticHash.create () in field hash "unison-component-projection/0";
  field hash (role_id role);feed hash(integer(Int64.of_int(List.length selected)));
  List.iter(fun (node:node) -> field hash node.view_sha256) selected;
  Some {sha256=SemanticHash.finish hash;components=List.length selected;
        bytes=List.fold_left(fun sum (node:node) -> Int64.add sum node.length) 0L selected}
let live (session:session) =
  if not session.active then invalid "component session expired";
  SemanticFile.check session.file
let bound (session:session) (snapshot:snapshot) =
  live session;
  if session.token != snapshot.token then invalid "component snapshot belongs to another session"
let charge session bytes =
  if bytes<0L || bytes>session.remaining then invalid "component shared read budget exceeded";
  session.remaining<-Int64.sub session.remaining bytes;
  session.requested<-Int64.add session.requested bytes
let bytes_requested session = session.requested
(* Specs are relative to their parent; normalization makes absolute physical
   extents, opaque gaps, bounded canonical order and globally unique IDs. *)
let normalize ~origin ~length ~existing ~depth (spec:spec) =
  let ids=Hashtbl.create 32 and count=ref existing in
  let add id =
    require_id id;incr count;
    if !count>1024 then invalid "component node limit";
    if Hashtbl.mem ids id then invalid "duplicate component identifier";
    Hashtbl.add ids id () in
  let rec node level origin limit (item:spec) =
    if level>16 then invalid "component depth limit";
    add item.id;require_id item.schema;
    if item.offset<0L || item.length<0L || item.offset>limit || item.length>Int64.sub limit item.offset
    then invalid "component extent outside parent";
    let start=Int64.add origin item.offset in
    let rec bounded_list count = function
      | [] -> ()
      | _::rest -> if count>=1024 then invalid "component child limit" else bounded_list (count+1) rest in
    bounded_list 0 item.children;
    let children=List.sort(fun (a:spec) b -> Int64.compare a.offset b.offset) item.children in
    let position=ref 0L in
    let gap at length =
      let id=item.id^"/@opaque:"^Int64.to_string at in
      node (level+1) start item.length
        {id;schema="opaque-bytes/0";role=Opaque;offset=at;length;children=[]} in
    let children = if children=[] then [] else
      let groups=List.map(fun (child:spec) ->
        if child.length<=0L || child.offset< !position then invalid "overlapping or empty component child";
        let prefix=item.id^"/" in
        if String.length child.id<=String.length prefix ||
           String.sub child.id 0 (String.length prefix)<>prefix then invalid "child identifier outside parent namespace";
        let before=if child.offset> !position then [gap !position (Int64.sub child.offset !position)] else [] in
        let child_node=node (level+1) start item.length child in
        position:=Int64.add child.offset child.length;
        before@[child_node]) children in
      List.concat groups @ (if !position<item.length then [gap !position (Int64.sub item.length !position)] else []) in
    {item with offset=start;children} in
  node depth origin length spec
let rec hash_node session ancestors (spec:spec) =
  let own=SemanticHash.create () in
  let children=if spec.children=[] then begin
    SemanticFile.iter session.file spec.offset spec.length (fun bytes n ->
      List.iter(fun hash -> SemanticHash.feed hash bytes 0 n) (own::ancestors));[]
  end else List.map(hash_node session (own::ancestors)) spec.children in
  let content=SemanticHash.finish own in
  {id=spec.id;schema=spec.schema;role=spec.role;offset=spec.offset;length=spec.length;
   content_sha256=content;view_sha256=view spec.id spec.schema spec.role spec.length content children;children}
let with_snapshot ~max_read_bytes file (spec:spec) callback =
  if max_read_bytes<0L then invalid "negative component read budget";
  if spec.offset<>0L || spec.length<>SemanticFile.size file then invalid "component root must cover entire file";
  let spec=normalize ~origin:0L ~length:spec.length ~existing:0 ~depth:0 spec in
  let session={token=ref ();file;active=true;remaining=max_read_bytes;requested=0L} in
  Fun.protect ~finally:(fun () -> session.active<-false) (fun () ->
    live session;charge session spec.length;
    let tree=hash_node session [] spec in live session;
    let value=callback session {token=session.token;tree} in live session;value)
let find snapshot id =
  match fold(fun found (node:node) -> if node.id=id then Some node else found) None snapshot.tree with
  | Some node -> node | None -> invalid "component identifier not found"
let refine session snapshot ~component ~schema children =
  bound session snapshot;require_id schema;
  let old=find snapshot component in
  if old.children<>[] then invalid "refinement requires a leaf component";
  if children=[] then invalid "nonempty component refinement required";
  let count=fold(fun n _ -> n+1) 0 snapshot.tree in
  let rec depth level (node:node) =
    if node.id=component then Some level else
    List.fold_left(fun found child -> match found with Some _ -> found | None -> depth (level+1) child)
      None node.children in
  let level=match depth 0 snapshot.tree with Some n -> n | None -> assert false in
  let spec=normalize ~origin:old.offset ~length:old.length ~existing:(count-1) ~depth:level
    {id=old.id;schema;role=old.role;offset=0L;length=old.length;children} in
  let siblings=fold(fun ids node -> if node.id=component then ids else node.id::ids) [] snapshot.tree in
  let rec check_ids (spec:spec) =
    if List.mem spec.id siblings then invalid "refinement identifier collides with another component";
    List.iter check_ids spec.children in check_ids spec;
  charge session old.length;
  let replacement=hash_node session [] spec in live session;
  if replacement.content_sha256<>old.content_sha256 then invalid "refined component bytes changed";
  let rec replace (node:node) =
    if node.id=component then replacement,true else
    let changed=List.map replace node.children in
    if not(List.exists snd changed) then node,false else
    let children=List.map fst changed in
    {node with children;view_sha256=view node.id node.schema node.role node.length node.content_sha256 children},true in
  {snapshot with tree=fst(replace snapshot.tree)}
let reader_live reader =
  live reader.session;
  let rec ancestors reader =
    if not reader.active then invalid "component plugin reader expired";
    match reader.parent with None -> () | Some parent -> ancestors parent in
  ancestors reader
let read reader offset count =
  reader_live reader;
  if offset<0L || count<0 || count>1048576 || offset>reader.length ||
     Int64.of_int count>Int64.sub reader.length offset then invalid "component plugin read outside parent";
  charge reader.session (Int64.of_int count);
  let result=SemanticFile.read reader.session.file (Int64.add reader.origin offset) count in
  live reader.session;result
let with_subreader reader ~offset ~length callback =
  reader_live reader;
  if reader.level>=16 || offset<0L || length<0L || offset>reader.length ||
     length>Int64.sub reader.length offset then invalid "nested component reader outside parent/depth";
  let child={session=reader.session;origin=Int64.add reader.origin offset;length;active=true;
             parent=Some reader;level=reader.level+1} in
  Fun.protect ~finally:(fun () -> child.active<-false) (fun () ->
    let value=callback child in reader_live child;value)
let apply_plugin session snapshot ~component plugin =
  bound session snapshot;require_id plugin.id;
  if String.length plugin.id>128 || String.length plugin.implementation_sha256<>32 then
    invalid "bounded plugin ID and raw implementation SHA256 required";
  let node=find snapshot component in
  if node.children<>[] then invalid "plugin refinement requires a leaf component";
  let reader={session;origin=node.offset;length=node.length;active=true;parent=None;level=0} in
  let decoded=Fun.protect ~finally:(fun () -> reader.active<-false) (fun () -> plugin.decode reader) in
  live session;
  match decoded with
  | Error reason -> if String.length reason>1024 then Error(String.sub reason 0 1024) else Error reason
  | Ok children -> Ok(refine session snapshot ~component
      ~schema:(plugin.id^"@"^SemanticHash.hex plugin.implementation_sha256) children)
