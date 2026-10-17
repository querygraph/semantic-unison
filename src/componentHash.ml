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
type checkpoint = { encoded : string; digest : string }
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

let max_checkpoint_size=1048576
let checkpoint_magic="UCH\000\000\000\000\000"
let checkpoint_bytes value=value.encoded
let checkpoint_sha256 value=value.digest
let role_code = function Encoded_pixels -> '\000' | Standard_metadata -> '\001'
  | Private_metadata -> '\002' | Structural -> '\003' | Opaque -> '\004'
let checkpoint session snapshot =
  bound session snapshot;
  let output=Buffer.create 1024 in
  let put value=Buffer.add_string output value in
  let number value=put(integer value) in
  let string value=number(Int64.of_int(String.length value));put value in
  put checkpoint_magic;number(Int64.of_int(fold(fun n _ -> n+1) 0 snapshot.tree));
  let rec write (node:node) =
    string node.id;string node.schema;Buffer.add_char output (role_code node.role);
    number node.offset;number node.length;put node.content_sha256;
    number(Int64.of_int(List.length node.children));List.iter write node.children in
  write snapshot.tree;
  let encoded=Buffer.contents output in
  if String.length encoded>max_checkpoint_size then invalid "component checkpoint size limit";
  bound session snapshot;{encoded;digest=SemanticHash.string encoded}

let decode_checkpoint encoded =
  if String.length encoded>max_checkpoint_size then invalid "component checkpoint size limit";
  let position=ref 0 and remaining=ref 0 in
  let take n=if n<0 || n>String.length encoded - !position then invalid "truncated component checkpoint";
    let value=String.sub encoded !position n in position:= !position+n;value in
  let number () =
    let value=ref 0L in
    String.iter(fun c -> value:=Int64.logor(Int64.shift_left !value 8)
      (Int64.of_int(Char.code c))) (take 8);
    if !value<0L then invalid "component checkpoint integer overflow";!value in
  let small limit=let value=number () in
    if value>Int64.of_int limit then invalid "component checkpoint field limit";Int64.to_int value in
  let string ()=let value=take(small 256) in require_id value;value in
  if take 8<>checkpoint_magic then invalid "unknown component checkpoint version";
  remaining:=small 1024;
  let rec node depth =
    if depth>16 || !remaining<=0 then invalid "component checkpoint node/depth limit";
    decr remaining;
    let id=string () in let schema=string () in
    let role=match take 1 with "\000" -> Encoded_pixels | "\001" -> Standard_metadata
      | "\002" -> Private_metadata | "\003" -> Structural | "\004" -> Opaque
      | _ -> invalid "component checkpoint role" in
    let offset=number () in let length=number () in let content_sha256=take 32 in
    let count=small 1024 in
    if count> !remaining then invalid "component checkpoint child count";
    let children=List.init count (fun _ -> node(depth+1)) in
    {id;schema;role;offset;length;content_sha256;children;
     view_sha256=view id schema role length content_sha256 children} in
  let tree=node 0 in
  if !remaining<>0 || !position<>String.length encoded then invalid "component checkpoint count/trailing data";
  tree

let checkpoint_record ~binding checkpoint =
  if String.length binding<>32 then invalid "component record binding must be raw SHA256";
  "UCR\000\000\000\000\000" ^ binding ^ checkpoint.digest ^
    integer(Int64.of_int(String.length checkpoint.encoded)) ^ checkpoint.encoded

let checkpoint_from_record ~expected_binding ~expected_record_sha256 encoded =
  let size=String.length encoded in
  if String.length expected_binding<>32 || String.length expected_record_sha256<>32 ||
    size<80 || size>max_checkpoint_size+80 ||
    SemanticHash.string encoded<>expected_record_sha256 then invalid "component record digest/size mismatch";
  if String.sub encoded 0 8<>"UCR\000\000\000\000\000" ||
    String.sub encoded 8 32<>expected_binding then invalid "component record version/owner binding mismatch";
  let length=ref 0L in
  for i=72 to 79 do length:=Int64.logor(Int64.shift_left !length 8)
    (Int64.of_int(Char.code encoded.[i])) done;
  if !length<>Int64.of_int(size-80) then invalid "component record payload length mismatch";
  let payload=String.sub encoded 80 (size-80) and digest=String.sub encoded 40 32 in
  if SemanticHash.string payload<>digest then invalid "component record checkpoint digest mismatch";
  ignore(decode_checkpoint payload);
  {encoded=payload;digest}

let write_checkpoint_record ~binding checkpoint output =
  let encoded=checkpoint_record ~binding checkpoint in
  let before=Unix.LargeFile.fstat output in
  if before.Unix.LargeFile.st_kind<>Unix.S_REG || before.st_size<>0L ||
    before.st_nlink<>1 || before.st_uid<>Unix.getuid () || before.st_perm land 0o777<>0o600 then
    invalid "component record output must be fresh private owned regular file";
  let writer=SemanticFile.prepare_writer output in
  let rec write at = if at<String.length encoded then begin
    let count=try SemanticFile.write_at writer encoded at
      (min 65536 (String.length encoded-at)) (Int64.of_int at)
      with Unix.Unix_error (Unix.EINTR,_,_) -> -1 in
    if count=0 then invalid "zero-length component record write";
    write (if count<0 then at else at+count)
  end in
  write 0;Unix.fsync output;
  let after=Unix.LargeFile.fstat output in
  if after.st_dev<>before.st_dev || after.st_ino<>before.st_ino ||
    after.st_size<>Int64.of_int(String.length encoded) || after.st_nlink<>1 ||
    after.st_uid<>before.st_uid || after.st_perm land 0o777<>0o600 then
    invalid "component record output changed";
  SemanticHash.string encoded

let read_checkpoint_record ~expected_binding ~expected_record_sha256 file =
  let size=SemanticFile.size file in
  if size<80L || size>Int64.of_int(max_checkpoint_size+80) then
    invalid "component record input size limit";
  let output=Buffer.create(Int64.to_int size) in
  SemanticFile.iter file 0L size (fun bytes count -> Buffer.add_subbytes output bytes 0 count);
  SemanticFile.check file;
  checkpoint_from_record ~expected_binding ~expected_record_sha256 (Buffer.contents output)

type record_publication
external record_publication_available : unit -> bool = "unison_component_record_publication_available"
external prepare_record_publication_raw : Unix.file_descr -> Unix.file_descr -> string -> string ->
  record_publication = "unison_component_record_publication_prepare"
external publish_checkpoint_record : record_publication -> Unix.file_descr -> Unix.file_descr -> unit
  = "unison_component_record_publication_publish"
external record_published : record_publication -> bool = "unison_component_record_publication_published"
let prepare_record_publication ~directory ~stage ~temporary ~expected_binding
    ~expected_record_sha256 file =
  if not(record_publication_available ()) then
    raise(Unix.Unix_error(Unix.ENOSYS,"component record publication",""));
  if not(SemanticFile.same_inode file stage) then invalid "component record readback/stage mismatch";
  ignore(read_checkpoint_record ~expected_binding ~expected_record_sha256 file);
  let ticket=prepare_record_publication_raw directory stage temporary
    (SemanticHash.hex expected_record_sha256) in
  SemanticFile.check file;ticket

let with_checkpoint ~expected_checkpoint_sha256 ~expected_root_schema ~max_read_bytes file encoded callback =
  if max_read_bytes<0L then invalid "negative component read budget";
  require_id expected_root_schema;
  if String.length expected_checkpoint_sha256<>32 || String.length encoded>max_checkpoint_size ||
     SemanticHash.string encoded<>expected_checkpoint_sha256 then invalid "component checkpoint digest mismatch";
  let tree=decode_checkpoint encoded in
  if tree.offset<>0L || tree.length<>SemanticFile.size file || tree.schema<>expected_root_schema then
    invalid "component checkpoint root binding mismatch";
  let rec spec origin (node:node) : spec =
    {id=node.id;schema=node.schema;role=node.role;offset=Int64.sub node.offset origin;
     length=node.length;children=List.map(spec node.offset) node.children} in
  let normalized=normalize ~origin:0L ~length:tree.length ~existing:0 ~depth:0 (spec 0L tree) in
  let rec same (node:node) (spec:spec) =
    node.id=spec.id && node.schema=spec.schema && node.role=spec.role &&
    node.offset=spec.offset && node.length=spec.length && List.length node.children=List.length spec.children &&
    List.for_all2 same node.children spec.children in
  if not(same tree normalized) then invalid "component checkpoint partition is not canonical";
  let session={token=ref ();file;active=true;remaining=max_read_bytes;requested=0L} in
  Fun.protect ~finally:(fun () -> session.active<-false) (fun () ->
    live session;charge session tree.length;
    if SemanticFile.digest file<>tree.content_sha256 then invalid "component checkpoint input bytes changed";
    live session;let result=callback session {token=session.token;tree} in live session;result)

let validate_base session snapshot (base:spec) =
  bound session snapshot;
  if base.offset<>0L || base.length<>snapshot.tree.length then
    invalid "component base root extent mismatch";
  let base=normalize ~origin:0L ~length:snapshot.tree.length ~existing:0 ~depth:0 base in
  let private_role = function Private_metadata | Opaque -> true | _ -> false in
  let safe_private tree = fold (fun safe (node:node) -> safe &&
    node.role<>Encoded_pixels && node.role<>Standard_metadata) true tree in
  let rec compatible (node:node) (spec:spec) =
    node.id=spec.id && node.role=spec.role && node.offset=spec.offset && node.length=spec.length &&
    (if spec.children=[] && private_role spec.role && node.children<>[] then safe_private node
     else node.schema=spec.schema && List.length node.children=List.length spec.children &&
       List.for_all2 compatible node.children spec.children) in
  if not(compatible snapshot.tree base) then invalid "component checkpoint differs from current base partition"

let reset_private_view session snapshot ~component ~schema =
  bound session snapshot;require_id schema;
  let old=find snapshot component in
  if old.role<>Private_metadata && old.role<>Opaque then
    invalid "private view reset requires a private/opaque component";
  ignore(fold(fun () (node:node) ->
    if node.role=Encoded_pixels || node.role=Standard_metadata then
      invalid "private view reset cannot discard pixel/standard claims") () old);
  let replacement={old with schema;children=[];
    view_sha256=view old.id schema old.role old.length old.content_sha256 []} in
  let rec replace (node:node) =
    if node.id=component then replacement,true else
    let changed=List.map replace node.children in
    if not(List.exists snd changed) then node,false else
    let children=List.map fst changed in
    {node with children;view_sha256=view node.id node.schema node.role node.length node.content_sha256 children},true in
  {snapshot with tree=fst(replace snapshot.tree)}
