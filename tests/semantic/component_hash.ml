let checks=ref 0
let check ok why=incr checks;if not ok then failwith why
let spec ?(children=[]) id schema role offset length : ComponentHash.spec =
  {id;schema;role;offset=Int64.of_int offset;length=Int64.of_int length;children}
let data=String.init 8192 (fun i -> Char.chr((i*37+19) land 255))
let layout=spec "file" "synthetic-layout/0" ComponentHash.Structural 0 8192 ~children:[
  spec "file/pixels" "encoded-synthetic/0" ComponentHash.Encoded_pixels 0 4096;
  spec "file/metadata" "standard-synthetic/0" ComponentHash.Standard_metadata 4096 1024;
  spec "file/private" "opaque-private/0" ComponentHash.Opaque 5120 3072]
let with_input bytes action =
  let path=Filename.temp_file "component-original-" ".bin" in
  let output=open_out_bin path in output_string output bytes;close_out output;
  let fd=Unix.openfile path [Unix.O_RDONLY] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd;Sys.remove path) (fun () -> action path fd)
let find snapshot id =
  let rec walk (node:ComponentHash.node) =
    if node.id=id then Some node else
    List.fold_left(fun result child -> match result with Some _ -> result | None -> walk child) None node.children in
  match walk(ComponentHash.root snapshot) with Some n -> n | None -> failwith "missing test node"
let invalid action = try ignore(action ());false with ComponentHash.Invalid _ -> true
let model_plugin : ComponentHash.plugin = {id="community.test.model/1";
  implementation_sha256=SemanticHash.string "original synthetic model decoder/1";decode=(fun reader ->
  ignore(ComponentHash.read reader 0L 1);
  ComponentHash.with_subreader reader ~offset:16L ~length:3056L (fun child ->
    ignore(ComponentHash.read child 0L 1));
  Ok [spec "file/private/model" "model-field/1" ComponentHash.Private_metadata 0 16;
      spec "file/private/rest" "unknown-private/0" ComponentHash.Opaque 16 3056])}
let () =
  with_input data (fun _ fd ->
    let (),stats=SemanticFile.with_read_stats fd (fun file ->
      ComponentHash.with_snapshot ~max_read_bytes:20000L file layout (fun session initial ->
        check(ComponentHash.bytes_requested session=8192L) "initial read was not one full pass";
        check(ComponentHash.full_sha256 initial=SemanticHash.string data) "full SHA differs";
        let pixel=find initial "file/pixels" in
        let refined=match ComponentHash.apply_plugin session initial ~component:"file/private" model_plugin with
          | Ok value -> value | Error reason -> failwith reason in
        check(ComponentHash.bytes_requested session=11266L) "refinement read outside its parent";
        let pixels=Option.get(ComponentHash.projection initial ComponentHash.Encoded_pixels) in
        check(pixels.components=1 && pixels.bytes=4096L) "pixel coverage counts missing";
        check(ComponentHash.projection initial ComponentHash.Private_metadata=None)
          "unknown private data mislabeled known absence";
        check(find refined "file/pixels" == pixel) "unaffected pixel node not reused";
        check(ComponentHash.projection refined ComponentHash.Encoded_pixels =
              ComponentHash.projection initial ComponentHash.Encoded_pixels) "pixel hash changed on metadata refinement";
        check(ComponentHash.projection refined ComponentHash.Standard_metadata =
              ComponentHash.projection initial ComponentHash.Standard_metadata) "unrelated metadata hash changed";
        check(ComponentHash.projection refined ComponentHash.Private_metadata <>
              ComponentHash.projection initial ComponentHash.Private_metadata) "private interpretation not incorporated";
        check(ComponentHash.full_sha256 refined=ComponentHash.full_sha256 initial) "refinement changed full digest";
        check((ComponentHash.root refined).view_sha256<>(ComponentHash.root initial).view_sha256)
          "view root did not change with decoder version";
        let nested=ComponentHash.refine session refined ~component:"file/private/rest" ~schema:"nested-fields/2"
          [spec "file/private/rest/code" "code-field/2" ComponentHash.Private_metadata 4 4] in
        check(ComponentHash.bytes_requested session=14322L) "nested refinement reread other components";
        check(find nested "file/pixels" == pixel) "nested refinement replaced unrelated pixels";
        check((find nested "file/private/rest").children<>[]) "nested fragment missing";
        check(ComponentHash.layout_sha256 refined<>ComponentHash.layout_sha256 initial) "layout view version unbound";
        check(invalid(fun () -> ComponentHash.refine session nested ~component:"file/private" ~schema:"bad/0" []))
          "nonleaf refinement accepted";
        let alternate={model_plugin with implementation_sha256=String.make 32 'V'} in
        let branch=match ComponentHash.apply_plugin session initial ~component:"file/private" alternate with
          | Ok value -> value | Error why -> failwith why in
        check((ComponentHash.root branch).view_sha256<>(ComponentHash.root refined).view_sha256)
          "implementation provenance missing from refined view";
        check(ComponentHash.projection branch ComponentHash.Encoded_pixels =
              ComponentHash.projection initial ComponentHash.Encoded_pixels) "decoder upgrade invalidated pixels";
        let malformed={model_plugin with implementation_sha256="not-a-digest"} in
        check(invalid(fun () -> ComponentHash.apply_plugin session initial ~component:"file/private" malformed))
          "malformed implementation pin accepted")) in
    check(stats.logical_bytes=17396L && not stats.saturated) "independent delivered-byte accounting differs");
  with_input data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    let session,snapshot=ComponentHash.with_snapshot ~max_read_bytes:8192L file layout (fun s v -> s,v) in
    check(invalid(fun () -> ComponentHash.refine session snapshot ~component:"file/private" ~schema:"late/0"
      [spec "file/private/new" "new/0" ComponentHash.Opaque 0 3072])) "expired session reused";
    ComponentHash.with_snapshot ~max_read_bytes:12000L file layout (fun second _ ->
      check(invalid(fun () -> ComponentHash.refine second snapshot ~component:"file/private" ~schema:"wrong/0"
        [spec "file/private/new" "new/0" ComponentHash.Opaque 0 3072])) "snapshot crossed session identity")));
  with_input data (fun _ fd ->
    let (),stats=SemanticFile.with_read_stats fd (fun file ->
      List.iter(fun bad -> check(invalid(fun () -> ComponentHash.with_snapshot ~max_read_bytes:8192L file bad
        (fun _ _ -> ()))) "bad partition accepted") [
        {layout with offset=1L};
        {layout with children=[spec "file/a" "a/0" ComponentHash.Opaque 0 4096;
                               spec "file/b" "b/0" ComponentHash.Opaque 2048 4096]};
        {layout with children=[spec "file/out" "out/0" ComponentHash.Opaque 8190 8]};
        {layout with children=[spec "other/a" "a/0" ComponentHash.Opaque 0 4]}];
      check(invalid(fun () -> ComponentHash.with_snapshot ~max_read_bytes:8191L file layout (fun _ _ -> ())))
        "insufficient initial budget accepted";
      let rec deep id n = spec id "deep/0" ComponentHash.Opaque 0 8192
        ~children:(if n=0 then [] else [deep (id^"/d") (n-1)]) in
      check(invalid(fun () -> ComponentHash.with_snapshot ~max_read_bytes:8192L file (deep "file" 17)
        (fun _ _ -> ()))) "excessive tree depth accepted";
      let wide={layout with children=List.init 1024 (fun n ->
        spec ("file/"^string_of_int n) "wide/0" ComponentHash.Opaque n 1)} in
      check(invalid(fun () -> ComponentHash.with_snapshot ~max_read_bytes:8192L file wide (fun _ _ -> ())))
        "excessive node count accepted") in
    check(stats.logical_bytes=0L) "invalid layout read payload");
  with_input data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    ComponentHash.with_snapshot ~max_read_bytes:8194L file layout (fun session snapshot ->
      check(invalid(fun () -> ComponentHash.apply_plugin session snapshot ~component:"file/private" model_plugin))
        "plugin escaped shared budget";
      check(ComponentHash.bytes_requested session=8194L) "failed refinement refunded decoder reads";
      let outside : ComponentHash.plugin = {id="bad-reader/0";implementation_sha256=String.make 32 'B';decode=(fun reader ->
        ignore(ComponentHash.read reader 3071L 2);Ok [])} in
      check(invalid(fun () -> ComponentHash.apply_plugin session snapshot ~component:"file/private" outside))
        "reader escaped parent range")));
  with_input data (fun path fd ->
    check(try SemanticFile.with_fd fd (fun file ->
      ComponentHash.with_snapshot ~max_read_bytes:20000L file layout (fun session snapshot ->
        let out=Unix.openfile path [Unix.O_WRONLY] 0 in
        ignore(Unix.LargeFile.lseek out 6000L Unix.SEEK_SET);
        ignore(Unix.write_substring out "changed" 0 7);Unix.close out;
        ignore(ComponentHash.apply_plugin session snapshot ~component:"file/private" model_plugin)));false
      with SemanticFile.Invalid _ | ComponentHash.Invalid _ -> true) "changed source retained old cache authority");
  with_input data (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    ComponentHash.with_snapshot ~max_read_bytes:12000L file layout (fun session snapshot ->
      let expiry : ComponentHash.plugin = {id="reader-expiry/0";implementation_sha256=String.make 32 'E';decode=(fun reader ->
        let old=ComponentHash.with_subreader reader ~offset:0L ~length:1L (fun child -> child) in
        let refused=try ignore(ComponentHash.read old 0L 1);false with ComponentHash.Invalid _ -> true in
        if not refused then failwith "expired child reader read bytes";
        Error "unsupported child format")} in
      check(ComponentHash.apply_plugin session snapshot ~component:"file/private" expiry =
        Error "unsupported child format") "unsupported child became a new snapshot";
      check(ComponentHash.bytes_requested session=8192L) "expired child consumed payload bytes")));
  let relocated=String.sub data 4096 4096 ^ String.sub data 0 4096 in
  let other=spec "file" "synthetic-layout/0" ComponentHash.Structural 0 8192 ~children:[
    spec "file/pixels" "encoded-synthetic/0" ComponentHash.Encoded_pixels 4096 4096] in
  let observe bytes layout = with_input bytes (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    ComponentHash.with_snapshot ~max_read_bytes:8192L file layout (fun _ snapshot ->
      ComponentHash.projection snapshot ComponentHash.Encoded_pixels,ComponentHash.layout_sha256 snapshot))) in
  let first=observe data layout and second=observe relocated other in
  check(fst first=fst second) "pixel view accidentally bound to physical placement";
  check(snd first<>snd second) "physical layout change disappeared";
  with_input "" (fun _ fd -> SemanticFile.with_fd fd (fun file ->
    ComponentHash.with_snapshot ~max_read_bytes:0L file
      (spec "empty" "empty/0" ComponentHash.Opaque 0 0) (fun session snapshot ->
        check(ComponentHash.full_sha256 snapshot=SemanticHash.string "") "empty full hash differs";
        check(ComponentHash.bytes_requested session=0L) "empty file read bytes";
        check(ComponentHash.projection snapshot ComponentHash.Encoded_pixels=None)
          "unknown pixels received a constant identity")));
  Printf.printf "PASS %d component checks: full coverage, nested refinement, exact read budgets, pixel reuse, scope refusal\n%!" !checks
