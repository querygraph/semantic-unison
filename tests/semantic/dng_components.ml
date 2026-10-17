let checks=ref 0
let check test reason = incr checks;if not test then failwith reason
let describe file = match DngComponents.describe file with
  | Ok spec -> spec | Error reason -> failwith reason
let digest bytes = Layout_only.with_input bytes (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:8192L file (describe file)
    (fun session snapshot ->
      check (ComponentHash.bytes_requested session=8192L) "DNG hash budget";
      snapshot))
let projection snapshot role = match ComponentHash.projection snapshot role with
  | Some value -> value | None -> failwith "missing expected DNG projection"
let with_capture_directory action =
 let folder=Filename.temp_file "dng-cache-capture-" "" in
 Sys.remove folder;Unix.mkdir folder 0o700;
 let directory=Unix.openfile folder [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 Fun.protect ~finally:(fun () -> Unix.close directory;
   Array.iter(fun name -> let leaf=Filename.concat folder name in
     if (Unix.lstat leaf).Unix.st_kind=Unix.S_DIR then Unix.rmdir leaf else Sys.remove leaf) (Sys.readdir folder);
   Unix.rmdir folder) (fun () -> action folder directory)
let () =
 List.iter (fun little -> List.iter (fun big ->
  let bytes=Layout_only.fixture little big (String.make 64 'A') in
  let snapshot=digest bytes in
  check (ComponentHash.full_sha256 snapshot=SemanticHash.string bytes) "full DNG SHA";
  let pixel=projection snapshot ComponentHash.Encoded_pixels in
  check (pixel.bytes=512L && pixel.components=1) "encoded strip coverage";
  check ((projection snapshot ComponentHash.Private_metadata).bytes=132L) "private value coverage";
  check ((projection snapshot ComponentHash.Standard_metadata).bytes=76L) "XMP value coverage";
  let changed=Bytes.of_string bytes in Bytes.set changed 3076 'Z';
  let private_change=digest (Bytes.to_string changed) in
  check ((projection private_change ComponentHash.Encoded_pixels).sha256=pixel.sha256)
    "private change invalidated pixel projection";
  check ((projection private_change ComponentHash.Private_metadata).sha256<>
    (projection snapshot ComponentHash.Private_metadata).sha256) "private bytes ignored";
  let changed=Bytes.of_string bytes in Bytes.set changed 2050 'P';
  check ((projection (digest (Bytes.to_string changed)) ComponentHash.Encoded_pixels).sha256<>
    pixel.sha256) "pixel change ignored";
  let primary,cw,ew,va,iw = if big then 16,8,20,12,8 else 8,2,12,8,4 in
  let no_xmp=Bytes.of_string bytes in
  Layout_only.put no_xmp little (primary+cw+ew) 2 65001;
  Layout_only.with_input (Bytes.to_string no_xmp) (fun file ->
    check (match DngLayout.inspect file with Error _ -> true | _ -> false)
      "transfer profile lost XMP prerequisite";
    let spec=describe file in
    ComponentHash.with_snapshot ~max_read_bytes:8192L file spec (fun _ snapshot ->
      check ((projection snapshot ComponentHash.Standard_metadata).bytes=12L)
        "unknown tag gained standard authority";
      check ((projection snapshot ComponentHash.Private_metadata).bytes=196L)
        "XMP-free private coverage"));
  let alias=Bytes.of_string bytes in
  Layout_only.put alias little (primary+cw+ew*2+va) iw 3072;
  Layout_only.with_input (Bytes.to_string alias) (fun file ->
    check (DngComponents.describe file=Error "DNG component physical aliases unsupported")
      "private/pixel alias claimed independent");
  let gap=Bytes.of_string bytes in Bytes.set gap 7000 'G';
  let gap_change=digest (Bytes.to_string gap) in
  check ((projection gap_change ComponentHash.Encoded_pixels).sha256=pixel.sha256)
    "residual change invalidated pixel bytes";
  check ((projection gap_change ComponentHash.Opaque).sha256<>
    (projection snapshot ComponentHash.Opaque).sha256) "gap disappeared"
 ) [false;true]) [false;true];
 let private_id="dng/ifd/0/tag/50740/value" in
 let fragment id role offset length : ComponentHash.spec =
   {id;schema="original-test-field/1";role;offset;length;children=[]} in
 let plugin name decode : ComponentHash.plugin =
   {id=name;implementation_sha256=SemanticHash.string name;decode} in
 let parent=plugin "original.parent/1" (fun reader ->
   ignore(ComponentHash.read reader 0L 2);
   Ok [fragment (private_id^"/known") ComponentHash.Private_metadata 0L 16L;
       fragment (private_id^"/nested") ComponentHash.Opaque 16L 112L]) in
 let child=plugin "original.child/1" (fun reader ->
   ignore(ComponentHash.read reader 0L 1);
   Ok [fragment (private_id^"/nested/code") ComponentHash.Private_metadata 0L 1L]) in
 let unsupported=plugin "original.unsupported/1" (fun _ -> Error "not learned yet") in
 let forbidden=plugin "original.invalid-role/1" (fun _ ->
   Ok [fragment (private_id^"/known/pixels") ComponentHash.Encoded_pixels 0L 1L]) in
 let never=plugin "original.never/1" (fun _ -> failwith "standard target invoked private decoder") in
 let bind component_id decoder : DngComponents.binding = {component_id;decoder} in
 let bindings=[bind private_id parent;bind (private_id^"/nested") child;
   bind "dng/absent" unsupported;bind "dng/ifd/0/tag/50706/value" never;
   bind "dng/ifd/0/tag/65000/value" unsupported;bind (private_id^"/known") forbidden] in
 let frozen=match DngComponents.freeze_decoders bindings with
   | Ok value -> value | Error reason -> failwith reason in
 check (match DngComponents.freeze_decoders [bind private_id parent;bind private_id child] with
   Error _ -> true | _ -> false) "duplicate decoder target";
 check (match DngComponents.freeze_decoders [bind (private_id^"/nested") child;bind private_id parent] with
   Error _ -> true | _ -> false) "child before parent refused";
 check (match DngComponents.freeze_decoders [bind (private_id^"/nested/code") child;bind private_id parent] with
   Error _ -> true | _ -> false) "descendant before ancestor refused";
 check (match DngComponents.freeze_decoders [bind (private_id^"-sibling") child;bind private_id parent] with
   Ok _ -> true | _ -> false) "textual prefix is not a component ancestor";
 check (match DngComponents.freeze_decoders [bind "outside/target" parent] with
   Error _ -> true | _ -> false) "decoder target namespace";
 check (match DngComponents.freeze_decoders [bind private_id {parent with implementation_sha256="bad"}] with
   Error _ -> true | _ -> false) "decoder provenance binding";
 check (match DngComponents.freeze_decoders (List.init 65 (fun n -> bind ("dng/"^string_of_int n) parent)) with
   Error _ -> true | _ -> false) "decoder binding bound";
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   match DngComponents.with_snapshot ~decoders:frozen ~max_read_bytes:8435L file
     (fun session ~initial ~refined outcomes ->
       check (List.map (fun (o:DngComponents.outcome) -> o.status) outcomes=
         [DngComponents.Refined;Refined;Unmatched;Unsupported "target is not private or opaque";
          Unsupported "not learned yet";Unsupported "private decoder fragment role/count/depth refused"])
         "nested decoder outcomes/order";
       check (List.map (fun (o:DngComponents.outcome) -> o.decoder_id,o.implementation_sha256) outcomes=
         List.map (fun (b:DngComponents.binding) -> b.decoder.id,b.decoder.implementation_sha256) bindings)
         "decoder outcome provenance missing";
       check (ComponentHash.bytes_requested session=8435L) "DNG nested refinement locality";
       check (ComponentHash.full_sha256 initial=ComponentHash.full_sha256 refined) "DNG refinement full SHA";
       check (ComponentHash.projection initial ComponentHash.Encoded_pixels=
         ComponentHash.projection refined ComponentHash.Encoded_pixels) "DNG decoder changed pixel identity";
       check (ComponentHash.projection initial ComponentHash.Standard_metadata=
         ComponentHash.projection refined ComponentHash.Standard_metadata) "DNG decoder changed standard lane";
       check (ComponentHash.layout_sha256 initial<>ComponentHash.layout_sha256 refined)
         "DNG decoder provenance/view root unchanged") with
   | Ok () -> () | Error reason -> failwith reason);
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   let encoded,digest,pixels,layout,previous=match DngComponents.with_snapshot ~decoders:frozen
     ~max_read_bytes:8435L file (fun session ~initial:_ ~refined outcomes ->
       let checkpoint=ComponentHash.checkpoint session refined in
       ComponentHash.checkpoint_bytes checkpoint,ComponentHash.checkpoint_sha256 checkpoint,
       ComponentHash.projection refined ComponentHash.Encoded_pixels,ComponentHash.layout_sha256 refined,outcomes) with
     | Ok value -> value | Error reason -> failwith reason in
   let refresh decoders limit action=match DngComponents.with_refreshed_checkpoint ~previous ~decoders
     ~expected_checkpoint_sha256:digest ~max_read_bytes:limit file encoded action with
     | Ok value -> value | Error reason -> failwith reason in
   refresh frozen 8192L (fun session result ->
     check(result.reused=[private_id;private_id^"/nested"] && result.invalidated=[])
       "unchanged decoder inventory not reused";
     check(ComponentHash.layout_sha256 result.snapshot=layout && ComponentHash.bytes_requested session=8192L)
       "unchanged inventory rehashed private components");
   let upgraded=match DngComponents.freeze_decoders
     [bind private_id parent;bind (private_id^"/nested") {child with implementation_sha256=SemanticHash.string "child-upgrade"}] with
     | Ok value -> value | Error reason -> failwith reason in
   refresh upgraded 8305L (fun session result ->
     check(result.reused=[private_id] && result.invalidated=[private_id^"/nested"])
       "child upgrade invalidated unrelated parent binding";
     check(ComponentHash.bytes_requested session=8305L &&
       ComponentHash.projection result.snapshot ComponentHash.Encoded_pixels=pixels)
       "child upgrade reread unrelated pixels");
   let upgraded_parent=match DngComponents.freeze_decoders
     [bind private_id {parent with implementation_sha256=SemanticHash.string "parent-upgrade"};
      bind (private_id^"/nested") child] with
     | Ok value -> value | Error reason -> failwith reason in
   refresh upgraded_parent 8435L (fun session result ->
     check(result.reused=[] && result.invalidated=[private_id])
       "parent upgrade reused an invalidated descendant";
     check(ComponentHash.bytes_requested session=8435L &&
       ComponentHash.projection result.snapshot ComponentHash.Encoded_pixels=pixels)
       "parent upgrade charged unrelated pixel reads");
   let forged=List.map(fun (entry:DngComponents.outcome) ->
     if entry.component_id=private_id then {entry with implementation_sha256=String.make 32 'X'}
     else entry) previous in
   check(try ignore(DngComponents.with_refreshed_checkpoint ~previous:forged ~decoders:frozen
     ~expected_checkpoint_sha256:digest ~max_read_bytes:8192L file encoded
     (fun _ _ -> failwith "forged provenance callback"));false
     with ComponentHash.Invalid _ -> true) "historical provenance mismatch accepted";
   let none=match DngComponents.freeze_decoders [] with Ok value -> value | Error reason -> failwith reason in
   let removed=refresh none 8192L (fun session result ->
     check(result.reused=[] && List.length result.invalidated=2 && ComponentHash.bytes_requested session=8192L)
       "removed decoders retained private interpretations or read input";
     let checkpoint=ComponentHash.checkpoint session result.snapshot in
     ComponentHash.checkpoint_bytes checkpoint,ComponentHash.checkpoint_sha256 checkpoint) in
   (match DngComponents.with_checkpoint ~expected_checkpoint_sha256:(snd removed) ~max_read_bytes:8192L
     file (fst removed) (fun _ snapshot ->
       check(ComponentHash.projection snapshot ComponentHash.Encoded_pixels=pixels)
         "decoder removal checkpoint could not restore base") with
     | Ok () -> () | Error reason -> failwith reason);
   (match DngComponents.with_checkpoint ~expected_checkpoint_sha256:digest ~max_read_bytes:8435L
     file encoded (fun session snapshot ->
       check(ComponentHash.projection snapshot ComponentHash.Encoded_pixels=pixels)
         "DNG restored pixels differ";
       check(ComponentHash.layout_sha256 snapshot=layout) "DNG historical private view differs";
       check(ComponentHash.bytes_requested session=8192L) "DNG restore full verification budget";
       let schema=parent.id^"@"^SemanticHash.hex parent.implementation_sha256 in
       check(match DngComponents.replace_private_view session snapshot ~component:private_id
         ~expected_schema:"stale/0" parent with Error _ -> true | _ -> false)
         "stale private replacement accepted";
       check(match DngComponents.replace_private_view session snapshot ~component:private_id
         ~expected_schema:schema unsupported with Error _ -> true | _ -> false)
         "unsupported replacement published";
       check(ComponentHash.layout_sha256 snapshot=layout && ComponentHash.bytes_requested session=8192L)
         "failed replacement mutated old view or read bytes";
       let replacement={parent with implementation_sha256=SemanticHash.string "replacement/2"} in
       let updated=match DngComponents.replace_private_view session snapshot ~component:private_id
         ~expected_schema:schema replacement with Ok value -> value | Error reason -> failwith reason in
       check(ComponentHash.layout_sha256 updated<>layout && ComponentHash.layout_sha256 snapshot=layout)
         "successful replacement lost provenance or mutated old view";
       check(ComponentHash.projection updated ComponentHash.Encoded_pixels=pixels)
         "private replacement changed pixels";
       check(ComponentHash.bytes_requested session=8322L) "private replacement read unrelated bytes";
       let pending=ComponentHash.reset_private_view session snapshot ~component:private_id
         ~schema:"uninterpreted-private/0" in
       check(ComponentHash.projection pending ComponentHash.Encoded_pixels=pixels)
         "DNG decoder invalidation changed pixels") with
     | Ok () -> () | Error reason -> failwith reason);
   check(try ignore(DngComponents.with_checkpoint ~expected_checkpoint_sha256:(String.make 32 'X')
     ~max_read_bytes:8192L file encoded (fun _ _ -> failwith "untrusted checkpoint callback"));false
     with ComponentHash.Invalid _ -> true) "DNG untrusted checkpoint accepted");
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   let sibling_id="dng/ifd/0/tag/65000/value" in
   let sibling=plugin "original.sibling/1" (fun reader ->
     ignore(ComponentHash.read reader 0L 1);
     Ok [fragment (sibling_id^"/field") ComponentHash.Private_metadata 0L 1L]) in
   let a=bind private_id parent and b=bind sibling_id sibling in
   let a2=bind private_id {parent with implementation_sha256=SemanticHash.string "sibling-A-upgrade"}
   and b2=bind sibling_id {sibling with implementation_sha256=SemanticHash.string "sibling-B-upgrade"} in
   let freeze bindings=match DngComponents.freeze_decoders bindings with
     | Ok value -> value | Error why -> failwith why in
   let capture session snapshot outcomes=
     let checkpoint=ComponentHash.checkpoint session snapshot in
     ComponentHash.checkpoint_bytes checkpoint,ComponentHash.checkpoint_sha256 checkpoint,outcomes,
     ComponentHash.layout_sha256 snapshot,ComponentHash.projection snapshot ComponentHash.Encoded_pixels in
   let initial bindings=match DngComponents.with_snapshot ~decoders:(freeze bindings)
     ~max_read_bytes:8327L file (fun session ~initial:_ ~refined outcomes -> capture session refined outcomes) with
     | Ok value -> value | Error why -> failwith why in
   let first=initial [a;b] and reversed=initial [b;a] in
   let equal (bytes,_,_,layout,pixels) (other,_,_,other_layout,other_pixels)=
     bytes=other && layout=other_layout && pixels=other_pixels in
   check(equal first reversed) "sibling extraction order changed canonical checkpoint roots";
   let step (encoded,digest,previous,_,_) bindings budget=
     match DngComponents.with_refreshed_checkpoint ~previous ~decoders:(freeze bindings)
       ~expected_checkpoint_sha256:digest ~max_read_bytes:budget file encoded (fun session result ->
         check(ComponentHash.bytes_requested session=budget) "sibling upgrade read outside its target";
         check(List.length result.reused=1 && List.length result.invalidated=1)
           "sibling upgrade invalidated an independent binding";
         capture session result.snapshot result.outcomes) with
     | Ok value -> value | Error why -> failwith why in
   let a_then_b=step (step first [a2;b] 8322L) [a2;b2] 8197L in
   let b_then_a=step (step first [a;b2] 8197L) [a2;b2] 8322L in
   check(equal a_then_b b_then_a) "independent incremental upgrades do not commute";
   let _,_,_,_,before_pixels=first and _,_,_,_,after_pixels=a_then_b in
   check(before_pixels=after_pixels) "sibling composition changed pixel identity");
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   let root_identity="original-local-root" and path="camera/example.dng"
   and generation_sha256=SemanticHash.string "original-generation/1" in
   match DngComponents.with_snapshot ~decoders:frozen ~max_read_bytes:8435L file
     (fun session ~initial:_ ~refined outcomes ->
       let checkpoint=ComponentHash.checkpoint session refined in
       let entry=DngComponents.make_owner_entry ~root_identity ~path ~generation_sha256 ~checkpoint ~outcomes in
       let encoded=DngComponents.owner_entry_bytes entry and digest=DngComponents.owner_entry_sha256 entry in
       check(String.length encoded<=DngComponents.owner_entry_max_size && SemanticHash.string encoded=digest &&
         String.sub encoded 0 8="UDI\000\000\000\000\000") "owner index framing/digest differs";
       let decode bytes sha=DngComponents.decode_owner_entry ~root_identity ~path ~generation_sha256
         ~expected_entry_sha256:sha bytes in
       let loaded=decode encoded digest in
       let record=ComponentHash.checkpoint_record ~binding:(DngComponents.owner_entry_binding entry) checkpoint in
       check(DngComponents.owner_entry_record_sha256 loaded=SemanticHash.string record &&
         DngComponents.owner_entry_outcomes loaded=outcomes) "owner entry lost record/inventory binding";
       let recovered=DngComponents.checkpoint_for_owner_entry loaded record in
       check(ComponentHash.checkpoint_bytes recovered=ComponentHash.checkpoint_bytes checkpoint)
         "owner entry did not recover original checkpoint";
       List.iter(fun (root_identity,path,generation_sha256) ->
         check(try ignore(DngComponents.decode_owner_entry ~root_identity ~path ~generation_sha256
           ~expected_entry_sha256:digest encoded);false with ComponentHash.Invalid _ -> true)
           "owner entry accepted changed root/path/generation")
         [("other-root",path,generation_sha256);(root_identity,"other.dng",generation_sha256);
          (root_identity,path,SemanticHash.string "other-generation")];
       check(try ignore(decode (encoded^"x") (SemanticHash.string(encoded^"x")));false
         with ComponentHash.Invalid _ -> true) "owner entry accepted trailing bytes";
       for count=0 to String.length encoded-1 do
         let bytes=String.sub encoded 0 count in
         check(try ignore(decode bytes (SemanticHash.string bytes));false
           with ComponentHash.Invalid _ -> true) "owner entry accepted truncated framing"
       done;
       let tampered=Bytes.of_string encoded in Bytes.set tampered (String.length encoded-1) 'X';
       check(try ignore(decode (Bytes.to_string tampered) digest);false
         with ComponentHash.Invalid _ -> true) "owner index accepted tampering under trusted digest";
       check(try ignore(DngComponents.checkpoint_for_owner_entry loaded (record^"x"));false
         with ComponentHash.Invalid _ -> true) "owner entry accepted wrong record";
       let wrong=List.map(fun (entry:DngComponents.outcome) ->
         if entry.status=DngComponents.Refined then {entry with implementation_sha256=String.make 32 'X'}
         else entry) outcomes in
       check(try ignore(DngComponents.make_owner_entry ~root_identity ~path ~generation_sha256
         ~checkpoint ~outcomes:wrong);false with ComponentHash.Invalid _ -> true)
         "owner capture accepted inconsistent decoder inventory";
       if ComponentHash.record_publication_available () then begin
         let directory_path=Filename.temp_file "dng-owner-entry-" "" in
         Sys.remove directory_path;Unix.mkdir directory_path 0o700;
         let directory=Unix.openfile directory_path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
         Fun.protect ~finally:(fun () -> Unix.close directory;
           Array.iter(fun name -> Sys.remove(Filename.concat directory_path name)) (Sys.readdir directory_path);
           Unix.rmdir directory_path) (fun () ->
           let stage=Unix.openfile (Filename.concat directory_path "stage")
             [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
           Fun.protect ~finally:(fun () -> Unix.close stage) (fun () ->
             check(DngComponents.write_owner_entry entry stage=digest) "staged owner entry digest differs";
             let read ()=SemanticFile.with_fd stage (fun file -> DngComponents.read_owner_entry
               ~root_identity ~path ~generation_sha256 ~expected_entry_sha256:digest file) in
             check(DngComponents.owner_entry_bytes(read())=encoded) "staged owner entry readback differs";
             let ticket=SemanticFile.with_fd stage (fun file -> DngComponents.prepare_owner_entry_publication
               entry ~directory ~stage ~temporary:"stage" file) in
             check(not(ComponentHash.record_published ticket)) "owner entry published before explicit call";
             ComponentHash.publish_checkpoint_record ticket directory stage;
             check(ComponentHash.record_published ticket &&
               not(Sys.file_exists(Filename.concat directory_path "stage")) &&
               (Unix.stat(Filename.concat directory_path (SemanticHash.hex digest))).Unix.st_ino=
                 (Unix.fstat stage).Unix.st_ino) "owner entry publication identity differs";
             check(DngComponents.owner_entry_bytes(read())=encoded) "published owner entry readback differs";
             check(try ignore(DngComponents.write_owner_entry entry stage);false
               with ComponentHash.Invalid _ -> true) "published owner entry overwritten");
           let stage=Unix.openfile (Filename.concat directory_path "wrong")
             [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
           Fun.protect ~finally:(fun () -> Unix.close stage) (fun () ->
             ignore(ComponentHash.stage_metadata_bytes ~max_bytes:DngComponents.owner_entry_max_size
               (String.make(String.length encoded) 'X') stage);
             check(try ignore(SemanticFile.with_fd stage (fun file -> DngComponents.prepare_owner_entry_publication
               entry ~directory ~stage ~temporary:"wrong" file));false with ComponentHash.Invalid _ -> true)
               "owner entry publisher accepted unrelated stage bytes"))
       end;
       if ComponentHash.record_publication_available () then with_capture_directory(fun folder directory ->
         let quota ()=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
         let run entry collision =
           let quota=quota () in check(ComponentHash.reserve_metadata_slot quota directory) "capture quota unavailable";
           let slot=ComponentHash.metadata_slot_name quota in
           let record_name=slot^"-record.tmp" and entry_name=slot^"-entry.tmp" in
           let record_stage=Unix.openfile (Filename.concat folder record_name)
             [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
           Fun.protect ~finally:(fun () -> Unix.close record_stage) (fun () ->
             let entry_stage=Unix.openfile (Filename.concat folder entry_name)
               [Unix.O_CREAT;Unix.O_EXCL;Unix.O_RDWR;Unix.O_CLOEXEC] 0o600 in
             Fun.protect ~finally:(fun () -> Unix.close entry_stage) (fun () ->
               check(try DngComponents.stage_cache_capture entry ~checkpoint ~quota ~directory
                 ~record_stage ~entry_stage:record_stage;false with Unix.Unix_error(Unix.EINVAL,_,_) -> true)
                 "aliased capture stages admitted";
               check((Unix.fstat record_stage).Unix.st_size=0 && (Unix.fstat entry_stage).Unix.st_size=0)
                 "failed paired admission wrote a partial stage";
               DngComponents.stage_cache_capture entry ~checkpoint ~quota ~directory ~record_stage ~entry_stage;
               check(try DngComponents.stage_cache_capture entry ~checkpoint ~quota ~directory
                 ~record_stage ~entry_stage;false with Invalid_argument _ -> true) "capture staging replayed";
               let capture=SemanticFile.with_fd record_stage (fun record_file -> SemanticFile.with_fd entry_stage
                 (fun entry_file -> DngComponents.prepare_cache_capture entry ~quota ~directory
                   ~record_stage ~entry_stage ~record_file ~entry_file)) in
               check(DngComponents.cache_capture_state capture=(false,false)) "capture published during preparation";
               let entry_target=Filename.concat folder (SemanticHash.hex(DngComponents.owner_entry_sha256 entry)) in
               if collision then begin
                 let foreign=Unix.openfile entry_target [Unix.O_CREAT;Unix.O_EXCL;Unix.O_WRONLY] 0o600 in
                 Fun.protect ~finally:(fun () -> Unix.close foreign) (fun () ->
                   check(Unix.write_substring foreign "foreign" 0 7=7) "collision fixture write failed")
               end;
               if collision then check(try DngComponents.publish_cache_capture capture directory record_stage entry_stage;
                 false with Unix.Unix_error(Unix.EEXIST,_,_) -> true) "capture collision overwritten"
               else DngComponents.publish_cache_capture capture directory record_stage entry_stage;
               check(DngComponents.cache_capture_state capture=(true,not collision))
                 "capture lost actual partial publication effects";
               check(not(Sys.file_exists(Filename.concat folder record_name)) &&
                 Sys.file_exists(Filename.concat folder entry_name)=collision) "capture stage ownership changed incorrectly";
               let record_target=Filename.concat folder (SemanticHash.hex(DngComponents.owner_entry_record_sha256 entry)) in
               check((Unix.stat record_target).Unix.st_ino=(Unix.fstat record_stage).Unix.st_ino)
                 "published capture record identity differs";
               if collision then check((Unix.stat entry_target).Unix.st_size=7) "foreign entry target changed"
               else check((Unix.stat entry_target).Unix.st_ino=(Unix.fstat entry_stage).Unix.st_ino)
                 "published capture entry identity differs";
               let recovered=SemanticFile.with_fd record_stage (fun file -> ComponentHash.read_checkpoint_record
                 ~expected_binding:(DngComponents.owner_entry_binding entry)
                 ~expected_record_sha256:(DngComponents.owner_entry_record_sha256 entry) file) in
               check(ComponentHash.checkpoint_bytes recovered=ComponentHash.checkpoint_bytes checkpoint)
                 "capture record bytes changed";
               let with_record action=SemanticFile.with_fd record_stage (fun file -> action(record_stage,file)) in
               let with_index action=SemanticFile.with_fd entry_stage (fun file -> action(entry_stage,file)) in
               if collision then begin
                 check(try with_record(fun record -> ignore(DngComponents.inspect_cache_capture entry ~directory
                   ~record:(Some record) ~index:None));false with ComponentHash.Invalid _ -> true)
                   "foreign index presence downgraded to absent";
                 check(try with_record(fun record -> with_index(fun index ->
                   ignore(DngComponents.inspect_cache_capture entry ~directory ~record:(Some record) ~index:(Some index))));false
                   with Unix.Unix_error _ -> true) "unpublished stage mistaken for published index";
                 (* Remove only this original fixture's deliberately created collision. *)
                 Unix.unlink entry_target;
                 with_record(fun record -> check(match DngComponents.inspect_cache_capture entry ~directory
                   ~record:(Some record) ~index:None with
                   | DngComponents.Capture_record_only value -> ComponentHash.checkpoint_bytes value=ComponentHash.checkpoint_bytes checkpoint
                   | _ -> false) "record-only orphan misclassified")
               end else begin
                 with_record(fun record -> with_index(fun index ->
                   check(match DngComponents.inspect_cache_capture entry ~directory ~record:(Some record) ~index:(Some index) with
                     | DngComponents.Capture_complete value -> ComponentHash.checkpoint_bytes value=ComponentHash.checkpoint_bytes checkpoint
                     | _ -> false) "complete cache capture not authenticated";
                   check(try ignore(DngComponents.inspect_cache_capture entry ~directory
                     ~record:(Some(entry_stage,snd record)) ~index:(Some index));false
                     with ComponentHash.Invalid _ -> true) "lookup reader/FD mismatch accepted"));
                 (* Redirect a real digest leaf to an equal-byte original fixture backup.
                    Following symlinks would wrongly accept this exact-content alias. *)
                 let backup=Filename.concat folder "original-record-backup" in
                 Unix.rename record_target backup;Unix.symlink "original-record-backup" record_target;
                 check(try with_record(fun record -> with_index(fun index ->
                   ignore(DngComponents.inspect_cache_capture entry ~directory ~record:(Some record) ~index:(Some index))));false
                   with Unix.Unix_error _ -> true) "lookup followed equal-byte metadata symlink";
                 check((Unix.lstat record_target).Unix.st_kind=Unix.S_LNK) "lookup mutated refused symlink";
                 Unix.unlink record_target;
                 with_index(fun index -> check(DngComponents.inspect_cache_capture entry ~directory
                   ~record:None ~index:(Some index)=DngComponents.Capture_entry_only)
                   "dangling index reference misclassified";
                   check(try ignore(DngComponents.inspect_cache_capture entry ~directory ~record:None ~index:None);false
                     with ComponentHash.Invalid _ -> true) "present index hidden by missing reader");
                 Unix.unlink entry_target;
                 check(DngComponents.inspect_cache_capture entry ~directory ~record:None ~index:None=DngComponents.Capture_missing)
                   "missing expected leaves misclassified"
               end;
               check(try DngComponents.publish_cache_capture capture directory record_stage entry_stage;false
                 with ComponentHash.Invalid _ -> true) "capture publication replayed")) in
         run entry false;
         let entry2=DngComponents.make_owner_entry ~root_identity ~path
           ~generation_sha256:(SemanticHash.string "original-generation/2") ~checkpoint ~outcomes in
         run entry2 true;
         check(not(ComponentHash.reserve_metadata_slot (quota()) directory)) "partial capture silently refunded quota");
       check(ComponentHash.bytes_requested session=8435L) "owner entry encoding reread input") with
   | Ok () -> () | Error why -> failwith why);
 let failing=plugin "original.operational-failure/1" (fun _ ->
   raise (ComponentHash.Invalid "original injected decoder failure")) in
 let failed=match DngComponents.freeze_decoders [bind private_id failing] with
   | Ok value -> value | Error reason -> failwith reason in
 Layout_only.with_input (Layout_only.fixture true false (String.make 64 'A')) (fun file ->
   check (try ignore(DngComponents.with_snapshot ~decoders:failed ~max_read_bytes:8192L file
     (fun _ ~initial:_ ~refined:_ _ -> ()));false with
     ComponentHash.Invalid "original injected decoder failure" -> true)
     "operational decoder failure downgraded to unsupported");
 Printf.printf "DNG component controls: %d checks PASS\n%!" !checks
