open FormatExtension
type item = { region : region; digest : string; contents : string }
type proof = { name : string; size : int64; full : string;
               preserved : string; items : item list }
type description = { profile : string; size : int64; digest : string;
                     preserved_digest : string; regions : region list }
type application = { logical_bytes_written : int; write_calls : int;
                     comparison_window : int }
type sample = { region : region; digest : string; prefix : string; truncated : bool }
type patch = { region : region; old_digest : string; data : string }
type t = { profile : string; nonce : string; size : int64;
           base_digest : string; target_digest : string;
           preserved : string; patches : patch list }
let profile t = t.profile
let proof_profile (p:proof) = p.name
let describe (p:proof) = {profile=p.name;size=p.size;digest=p.full;
  preserved_digest=p.preserved;regions=List.map (fun (i:item) -> i.region) p.items}
let samples ?(max_region_bytes=4096) ?(max_total_bytes=8192) (p:proof) =
  if max_region_bytes < 0 || max_region_bytes > 4096 ||
     max_total_bytes < 0 || max_total_bytes > 8192 then
    invalid_arg "SemanticDelta.samples: sample limit exceeded";
  let remaining = ref max_total_bytes in
  List.map (fun (i:item) ->
    let n = min !remaining (min max_region_bytes (String.length i.contents)) in
    remaining := !remaining - n;
    {region=i.region;digest=i.digest;prefix=String.sub i.contents 0 n;
     truncated=n < i.region.length}) p.items
let observe ~extension (p:proof) =
  if p.name <> FormatExtension.profile extension then
    invalid_arg "SemanticDelta.observe: profile mismatch";
  if List.exists (fun (i:item) -> String.length i.contents <> i.region.length) p.items then
    Some (Error "full editable packets are unavailable in a peer proof")
  else FormatExtension.observe extension (List.map (fun (i:item) -> i.contents) p.items)
let target_digest t = t.target_digest
let target_size t = t.size
let payload_size t = List.fold_left (fun n p -> n + String.length p.data) 0 t.patches
let max_request_size = 8192
let max_envelope_size = max_payload + 65536
let u64 n =
  let b = Bytes.create 8 in
  for i = 0 to 7 do Bytes.set b i (Char.chr (Int64.to_int
    (Int64.logand 255L (Int64.shift_right_logical n (56-8*i))))) done;
  Bytes.to_string b
let feed_string h s = SemanticHash.feed h (Bytes.of_string s) 0 (String.length s)
let inspect ?max_payload ((module E : S) as extension) file =
  match FormatExtension.inspect ?max_payload extension file with
  | Error _ as e -> e
  | Ok manifest ->
    let full = SemanticHash.create () and preserved = SemanticHash.create () in
    feed_string preserved "SDE/0-preserved\000";
    feed_string preserved (u64 (SemanticFile.size file));
    feed_string preserved (u64 (Int64.of_int (List.length manifest.regions)));
    List.iter (fun r -> feed_string preserved (u64 r.offset);
      feed_string preserved (u64 (Int64.of_int r.length))) manifest.regions;
    let complement start stop =
      feed_string preserved (u64 start); feed_string preserved (u64 (Int64.sub stop start));
      SemanticFile.iter file start (Int64.sub stop start) (fun b n ->
        SemanticHash.feed full b 0 n; SemanticHash.feed preserved b 0 n)
    in
    let position = ref 0L in
    let items = List.map (fun region ->
      complement !position region.offset;
      let contents = SemanticFile.read file region.offset region.length in
      feed_string full contents;
      position := Int64.add region.offset (Int64.of_int region.length);
      { region; contents; digest = SemanticHash.string contents }) manifest.regions in
    complement !position (SemanticFile.size file);
    SemanticFile.check file;
    Ok {name = E.profile; size = SemanticFile.size file;
        full = SemanticHash.finish full; preserved = SemanticHash.finish preserved; items}
let same_layout a b =
  a.name = b.name && a.size = b.size &&
  List.map (fun (i:item) -> i.region) a.items = List.map (fun (i:item) -> i.region) b.items
let classify ~base ~target =
  if base.full = target.full then Exact_bytes
  else if same_layout base target && base.preserved = target.preserved then Editable_metadata
  else Other_bytes
let plan ~nonce ~(base:proof) ~(target:proof) =
  if String.length nonce <> 32 then Error "nonce must be 32 bytes"
  else if not (same_layout base target) then Error "profile, size or layout changed"
  else if List.exists (fun (item:item) ->
    String.length item.contents <> item.region.length) target.items then
    Error "target metadata contents unavailable"
  else if base.preserved <> target.preserved then Error "bytes outside editable regions changed"
  else Ok { profile = base.name; nonce; size = base.size;
    base_digest = base.full; target_digest = target.full; preserved = base.preserved;
    patches = List.map2 (fun (a:item) (b:item) ->
      {region=a.region; old_digest=a.digest; data=b.contents}) base.items target.items }

(* An explicit locally retained common base is required. This constructs an
   exact target plan; archive-generation authority and publication stay with
   the owner. Peer request proofs have no full packet bytes and are rejected. *)
let reconcile_xmp ?max_payload extension ~nonce ~(base:proof) ~(left:proof)
    ~(right:proof) file =
  let fail reason=Error reason in
  if String.length nonce<>32 then fail "nonce must be32 bytes"
  else if not(List.mem base.name ["org.firstpair.dng-xmp/0";"org.firstpair.dng-xmp/1"])
  then fail "unsupported XMP reconciliation profile"
  else if not(same_layout base left && same_layout base right) then
    fail "reconciliation profile, size or layout changed"
  else if base.preserved<>left.preserved || base.preserved<>right.preserved then
    fail "reconciliation protected bytes changed"
  else match base.items,left.items,right.items with
  | [b],[l],[r] when String.length b.contents=b.region.length &&
      String.length l.contents=l.region.length && String.length r.contents=r.region.length ->
      (match XmpMerge.merge ~base:b.contents ~left:l.contents ~right:r.contents with
       | Error _ as error -> error
       | Ok packet when String.length packet<>l.region.length ->
           fail "merged packet does not fit the fixed metadata region"
       | Ok packet ->
           (match inspect ?max_payload extension file with
            | Error _ as error -> error
            | Ok current when describe current<>describe left ->
                fail "live reconciliation basis changed"
            | Ok _ ->
                let hash=SemanticHash.create () in
                let feed start length=SemanticFile.iter file start length
                  (fun bytes n -> SemanticHash.feed hash bytes 0 n) in
                feed 0L l.region.offset;feed_string hash packet;
                let last=Int64.add l.region.offset(Int64.of_int l.region.length) in
                feed last (Int64.sub left.size last);
                SemanticFile.check file;
                let target={left with full=SemanticHash.finish hash;
                  items=[{region=l.region;contents=packet;digest=SemanticHash.string packet}]} in
                plan ~nonce ~base:left ~target))
  | _ -> fail "full single XMP packets required for reconciliation"

(* Bounded, canonical external encoding. Integers are unsigned big endian;
   file offsets are restricted to the positive signed-int64 range. *)
let magic = "SDE\000\000\000\000\000"
let encode t =
  let b = Buffer.create (256 + payload_size t) in
  let put s = Buffer.add_string b s in
  put magic; put (u64 (Int64.of_int (String.length t.profile))); put t.profile;
  put t.nonce; put (u64 t.size); put t.base_digest; put t.target_digest; put t.preserved;
  put (u64 (Int64.of_int (List.length t.patches)));
  List.iter (fun p -> put (u64 p.region.offset); put (u64 (Int64.of_int p.region.length));
    put p.old_digest; put (SemanticHash.string p.data); put p.data) t.patches;
  Buffer.contents b
exception Bad of string
let decode ?(max_payload=FormatExtension.max_payload) s =
 try
  if max_payload <= 0 || max_payload > FormatExtension.max_payload then
    raise (Bad "invalid declared payload limit");
  if String.length s > max_payload + 65536 then raise (Bad "envelope too large");
  let position = ref 0 in
  let take n =
    if n < 0 || n > String.length s - !position then raise (Bad "truncated envelope");
    let r = String.sub s !position n in position := !position+n; r in
  let integer () =
    let v = ref 0L in
    String.iter (fun c -> v := Int64.logor (Int64.shift_left !v 8) (Int64.of_int (Char.code c))) (take 8);
    if !v < 0L then raise (Bad "integer overflow"); !v in
  let small max = let n = integer () in
    if n > Int64.of_int max then raise (Bad "limit exceeded"); Int64.to_int n in
  if take 8 <> magic then raise (Bad "unknown envelope version");
  let profile = take (small 128) in
  if profile = "" || String.contains profile '\000' then raise (Bad "invalid profile identifier");
  let nonce = take 32 in
  let size = integer () in
  let base_digest = take 32 in let target_digest = take 32 in let preserved = take 32 in
  let count = small 64 in
  if count = 0 then raise (Bad "empty plan");
  let stop = ref 0L and total = ref 0 in
  let patches = List.init count (fun _ ->
    let offset = integer () in let length = small max_region in
    if length = 0 || offset < !stop || offset > size || Int64.of_int length > Int64.sub size offset then
      raise (Bad "invalid patch extent");
    total := !total + length;
    if !total > max_payload then raise (Bad "payload limit");
    stop := Int64.add offset (Int64.of_int length);
    let old_digest = take 32 in let expected = take 32 in let data = take length in
    if SemanticHash.string data <> expected then raise (Bad "payload digest mismatch");
    {region={offset;length};old_digest;data}) in
  if !position <> String.length s then raise (Bad "trailing envelope bytes");
  Ok {profile;nonce;size;base_digest;target_digest;preserved;patches}
 with Bad s -> Error s

(* Receiver descriptions omit metadata contents: only fixed-size digests and
   bounded region records cross to the source. They are claims, not authority;
   the receiver binds the returned plan to its own retained, inspected proof. *)
let request_magic = "SDR\000\000\000\000\000"
let encode_request ~nonce (base:proof) =
  if String.length nonce <> 32 then invalid_arg "semantic request nonce";
  let b = Buffer.create 1024 in
  let put s = Buffer.add_string b s in
  put request_magic; put nonce;
  put (u64 (Int64.of_int (String.length base.name))); put base.name;
  put (u64 base.size); put base.full; put base.preserved;
  put (u64 (Int64.of_int (List.length base.items)));
  List.iter (fun (i:item) -> put (u64 i.region.offset);
    put (u64 (Int64.of_int i.region.length)); put i.digest) base.items;
  let result = Buffer.contents b in
  if String.length result > max_request_size then invalid_arg "semantic request limit";
  result

let decode_request s =
 try
  if String.length s > max_request_size then raise (Bad "request too large");
  let position = ref 0 in
  let take n =
    if n < 0 || n > String.length s - !position then raise (Bad "truncated request");
    let r = String.sub s !position n in position := !position+n; r in
  let integer () =
    let v = ref 0L in
    String.iter (fun c -> v := Int64.logor (Int64.shift_left !v 8)
      (Int64.of_int (Char.code c))) (take 8);
    if !v < 0L then raise (Bad "request integer overflow"); !v in
  let small limit = let v = integer () in
    if v > Int64.of_int limit then raise (Bad "request limit exceeded"); Int64.to_int v in
  if take 8 <> request_magic then raise (Bad "unknown request version");
  let nonce = take 32 in
  let name = take (small 128) in
  if name = "" || String.contains name '\000' then raise (Bad "invalid request profile identifier");
  let size = integer () in let full = take 32 in let preserved = take 32 in
  let count = small 64 in
  if count = 0 then raise (Bad "empty request manifest");
  let stop = ref 0L and total = ref 0 in
  let items = List.init count (fun _ ->
    let offset = integer () in let length = small max_region in
    if length = 0 || offset < !stop || offset > size ||
       Int64.of_int length > Int64.sub size offset || !total > max_payload - length then
      raise (Bad "invalid request region");
    stop := Int64.add offset (Int64.of_int length); total := !total + length;
    let digest = take 32 in
    {region={offset;length}; digest; contents=""}) in
  if !position <> String.length s then raise (Bad "trailing request bytes");
  Ok (nonce, {name;size;full;preserved;items})
 with Bad message -> Error message

(* Lossless local base cache. This is not a network proof or archive authority.
   The owner must bind trusted private storage to the previous common archive. *)
let base_cache_magic = "SDB\000\000\000\000\001"
let base_cache_policy = XmpMerge.policy ^ ";parser=1"
let max_base_cache_size = 1048576 + max_request_size + 256
let base_cache_view packet =
  match XmpObservation.scalar_view packet with
  | Error reason -> invalid_arg ("semantic base cache: " ^ reason)
  | Ok view ->
    let encoded = SemanticHash.string view.XmpObservation.shell ^
      u64 (Int64.of_int (List.length view.scalars)) ^
      String.concat "" (List.map (fun (scalar:XmpObservation.scalar) ->
        u64 (Int64.of_int (String.length scalar.scalar_name)) ^ scalar.scalar_name ^
        SemanticHash.string scalar.value ^ u64 (Int64.of_int scalar.first) ^
        u64 (Int64.of_int scalar.last)) view.scalars) in
    if String.length encoded>4096 then invalid_arg "semantic base cache parsed view limit";
    encoded
let encode_base_cache (base:proof) =
  let invalid reason = invalid_arg ("semantic base cache: " ^ reason) in
  if not (List.mem base.name ["org.firstpair.dng-xmp/0";"org.firstpair.dng-xmp/1"])
  then invalid "unsupported profile";
  let packet = match base.items with
    | [item] when String.length item.contents = item.region.length &&
                  item.region.length <= 1048576 &&
                  SemanticHash.string item.contents = item.digest -> item.contents
    | _ -> invalid "full single metadata packet required" in
  let parsed = base_cache_view packet in
  let request = encode_request ~nonce:(String.make 32 '\000') base in
  let payload = base_cache_magic ^ u64 (Int64.of_int (String.length base_cache_policy)) ^
    base_cache_policy ^ u64 (Int64.of_int (String.length request)) ^ request ^
    u64 (Int64.of_int (String.length packet)) ^ packet ^
    u64 (Int64.of_int (String.length parsed)) ^ parsed in
  let encoded = payload ^ SemanticHash.string payload in
  if String.length encoded > max_base_cache_size then invalid "record limit";
  encoded

let decode_base_cache encoded =
  try
    let length = String.length encoded in
    if length > max_base_cache_size || length < 64 then raise (Bad "base cache size");
    let stop = length - 32 and at = ref 0 in
    let take count =
      if count < 0 || count > stop - !at then raise (Bad "truncated base cache");
      let result = String.sub encoded !at count in at := !at + count; result in
    let small maximum =
      let value = ref 0L in
      String.iter (fun c -> value := Int64.logor (Int64.shift_left !value 8)
        (Int64.of_int (Char.code c))) (take 8);
      if !value < 0L || !value > Int64.of_int maximum then raise (Bad "base cache limit");
      Int64.to_int !value in
    if SemanticHash.string (String.sub encoded 0 stop) <> String.sub encoded stop 32
    then raise (Bad "base cache checksum");
    if take 8 <> base_cache_magic then raise (Bad "unknown base cache version");
    let policy = take (small 128) in
    if policy <> base_cache_policy then raise (Bad "base cache policy/parser mismatch");
    let request = take (small max_request_size) in
    let nonce, claim = match decode_request request with
      | Ok result -> result | Error reason -> raise (Bad reason) in
    if nonce <> String.make 32 '\000' then raise (Bad "base cache nonce");
    let packet = take (small 1048576) in
    let parsed = take (small 4096) in
    if parsed <> base_cache_view packet then raise (Bad "base cache parsed view mismatch");
    if !at <> stop then raise (Bad "trailing base cache bytes");
    let base = match claim.items with
      | [item] when String.length packet = item.region.length &&
                    SemanticHash.string packet = item.digest ->
          {claim with items=[{item with contents=packet}]}
      | _ -> raise (Bad "base cache packet mismatch") in
    (* Re-encode validates supported profile and parser plus canonical form. *)
    if encode_base_cache base <> encoded then raise (Bad "noncanonical base cache");
    Ok base
  with Bad reason | Invalid_argument reason -> Error reason

let binds_request ~nonce ~(base:proof) t =
  t.nonce = nonce && t.profile = base.name && t.size = base.size &&
  t.base_digest = base.full && t.preserved = base.preserved &&
  List.map (fun p -> p.region,p.old_digest) t.patches =
  List.map (fun (i:item) -> i.region,i.digest) base.items

let apply_report_with_extension ?(check_cancel = fun () -> ()) ?max_payload
    ((module E : FormatExtension.S) as extension) t ~basis ~output =
  let invalid s = raise (SemanticFile.Invalid s) in
  check_cancel ();
  if E.profile <> t.profile then invalid "semantic profile mismatch";
  let checked file = match inspect ?max_payload extension file with
    | Error reason -> invalid reason
    | Ok p ->
      if p.size <> t.size || p.full <> t.base_digest || p.preserved <> t.preserved ||
         List.map (fun (i:item) -> i.region,i.digest) p.items <>
         List.map (fun p -> p.region,p.old_digest) t.patches then
        invalid "basis proof mismatch";
      p in
  if SemanticFile.same_inode basis output then invalid "basis and staging are the same inode";
  let verified_basis = checked basis in
  let basis_stat = Unix.LargeFile.fstat output in
  if basis_stat.Unix.LargeFile.st_nlink <> 1 then invalid "staging file has multiple links";
  let writer = SemanticFile.prepare_writer ~check_cancel output in
  ignore (SemanticFile.with_fd ~check_cancel output checked);
  let comparison_window = 4096 in
  let logical_bytes_written = ref 0 and write_calls = ref 0 in
  List.iter2 (fun p (old:item) ->
    check_cancel ();
    let length = String.length p.data in
    let write start stop =
      if start < stop then begin
        let rec loop off = if off < stop then begin
          check_cancel ();
          let count = min 65536 (stop-off) in
          let position = Int64.add p.region.offset (Int64.of_int off) in
          let rec retry () =
            check_cancel ();
            incr write_calls;
            try SemanticFile.write_at writer p.data off count position
            with Unix.Unix_error (Unix.EINTR,_,_) -> retry () in
          let n = retry () in
          if n = 0 then invalid "metadata write made no progress";
          if n < 0 || n > count then invalid "metadata write returned invalid progress";
          logical_bytes_written := !logical_bytes_written + n;
          loop (off+n)
        end in loop start
      end in
    let rec differs off stop = off < stop &&
      (old.contents.[off] <> p.data.[off] || differs (off+1) stop) in
    (* Absolute 4 KiB comparison windows are a logical write policy, not a
       claim about filesystem allocation size. Clip at metadata boundaries,
       skip identical windows, and combine adjacent changed windows. *)
    let start = ref None in
    let rec scan off =
      check_cancel ();
      if off = length then begin
        match !start with None -> () | Some first -> write first off
      end else begin
        let absolute = Int64.add p.region.offset (Int64.of_int off) in
        let within = Int64.to_int (Int64.logand absolute 4095L) in
        let stop = off + min (comparison_window-within) (length-off) in
        if differs off stop then begin
          if !start = None then start := Some off
        end else begin
          (match !start with None -> () | Some first -> write first off);
          start := None
        end;
        scan stop
      end in scan 0) t.patches verified_basis.items;
  check_cancel ();
  (* Verified staging already has the exact length, and all writes are inside
     the verified regions. Avoid touching EOF for an unchanged packet. *)
  SemanticFile.with_fd ~check_cancel output (fun f ->
    if SemanticFile.digest f <> t.target_digest then invalid "target SHA-256 mismatch");
  SemanticFile.check basis;
  {logical_bytes_written = !logical_bytes_written; write_calls = !write_calls;
   comparison_window}

let apply_with_extension ?check_cancel ?max_payload extension t ~basis ~output =
  ignore (apply_report_with_extension ?check_cancel ?max_payload extension t ~basis ~output)

let apply_report t ~basis ~output =
  let extension = match FormatExtension.resolve t.profile with
    | Some e -> e | None -> raise (SemanticFile.Invalid "unknown semantic profile") in
  apply_report_with_extension ~max_payload:(FormatExtension.payload_limit extension)
    (FormatExtension.implementation extension) t ~basis ~output

let apply t ~basis ~output = ignore (apply_report t ~basis ~output)
