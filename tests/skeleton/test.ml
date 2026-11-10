(* Skeleton versions (docs/skeleton-versions.md): the walkers' cuts, the
   delta, the store, and a synchronization that keeps and restores versions.

   Every file is synthetic and built here; everything is written under a
   disposable directory that is removed at the end.

     test.exe [--unison UNISON --tool UNISON-SKELETON] [--dump DIR]

   --dump writes the fixtures to DIR and prints their cuts, for comparison
   with another implementation of the same cutting rules. *)

let ( // ) = Filename.concat
let failures = ref 0 and checks = ref 0

let check name ok =
  incr checks;
  if not ok then begin incr failures; Printf.printf "FAIL %s\n%!" name end
  else Printf.printf "ok   %s\n%!" name

let section name = Printf.printf "\n== %s\n%!" name

(* ---- Synthetic files ---- *)

(* [n] bytes that depend on [seed] only. *)
let noise n seed =
  let x = ref (seed * 2654435761 land 0x7fffffff) in
  String.init n (fun _ ->
    x := (!x * 1103515245 + 12345) land 0x7fffffff;
    Char.chr ((!x lsr 16) land 0xff))

let u16 be b v =
  if be then (Buffer.add_char b (Char.chr (v lsr 8)); Buffer.add_char b (Char.chr (v land 255)))
  else (Buffer.add_char b (Char.chr (v land 255)); Buffer.add_char b (Char.chr (v lsr 8)))

let u32 be b v =
  if be then (u16 be b (v lsr 16); u16 be b (v land 0xffff))
  else (u16 be b (v land 0xffff); u16 be b (v lsr 16))

(* A small classic TIFF laid out as a raw file with embedded metadata:
     header, IFD 0, a SubIFD, the XMP packet, a private tag's value, the
     SubIFD's JPEG preview, one strip, and optionally bytes no tag points at.
   Growing the XMP moves every block after it. *)
let tiff ?(be = false) ?(gap = 0) ~xmp ~priv ~preview ~strip () =
  let ifd0 = 8 and sub = 8 + 2 + 7 * 12 + 4 in
  let xmp_at = sub + 2 + 4 * 12 + 4 in
  let priv_at = xmp_at + String.length xmp in
  let preview_at = priv_at + String.length priv in
  let strip_at = preview_at + String.length preview in
  let b = Buffer.create 65536 in
  Buffer.add_string b (if be then "MM\000*" else "II*\000");
  u32 be b ifd0;
  let short tag v = u16 be b tag; u16 be b 3; u32 be b 1; u16 be b v; u16 be b 0 in
  let long tag v = u16 be b tag; u16 be b 4; u32 be b 1; u32 be b v in
  let bytes tag typ n at = u16 be b tag; u16 be b typ; u32 be b n; u32 be b at in
  u16 be b 7;
  short 256 64; short 257 48; long 273 strip_at; long 279 (String.length strip); long 330 sub;
  bytes 700 1 (String.length xmp) xmp_at; bytes 50740 7 (String.length priv) priv_at;
  u32 be b 0;
  u16 be b 4;
  short 256 16; short 257 12; long 513 preview_at; long 514 (String.length preview);
  u32 be b 0;
  assert (Buffer.length b = xmp_at);
  Buffer.add_string b xmp; Buffer.add_string b priv; Buffer.add_string b preview; Buffer.add_string b strip;
  Buffer.add_string b (noise gap 77);
  Buffer.contents b

let segment marker payload =
  let n = String.length payload + 2 in
  Printf.sprintf "\xff%c%c%c%s" (Char.chr marker) (Char.chr (n lsr 8)) (Char.chr (n land 255)) payload

(* A small JPEG: XMP in APP1, a profile in APP2, a table, the scan. *)
let jpeg ~xmp ~profile ~scan =
  "\xff\xd8" ^ segment 0xe1 ("http://ns.adobe.com/xap/1.0/\000" ^ xmp) ^ segment 0xe2 profile
  ^ segment 0xdb (noise 65 5) ^ segment 0xda "\001\001\000\000\063\000" ^ scan ^ "\xff\xd9"

(* An XMP packet for edit number [k]: its rating differs, and it has [k] more
   history lines than the first, so it grows with every edit. *)
let xmp k =
  let b = Buffer.create 8192 in
  Buffer.add_string b "<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>\n<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n";
  Printf.bprintf b " <rdf:Description xmp:Rating='%d' crs:Exposure2012='%+.2f' crs:Blacks2012='%+d'>\n"
    (k mod 6) (float_of_int k *. 0.35) (-3 * k);
  for i = 0 to 119 do Printf.bprintf b "  <crs:Setting%03d>%d</crs:Setting%03d>\n" i (i * 7919 mod 1000) i done;
  for i = 1 to k do
    Printf.bprintf b "  <stEvt:action when='2026-01-%02dT10:00:00'>saved</stEvt:action>\n" i
  done;
  Buffer.add_string b " </rdf:Description>\n</x:xmpmeta>\n";
  Buffer.add_string b (String.make 1024 ' ');
  Buffer.add_string b "<?xpacket end='w'?>";
  Buffer.contents b

let priv = noise 800 1
let preview = noise 6000 2
let strip = noise 20000 3
let photo ?(preview = preview) ?(strip = strip) k = tiff ~xmp:(xmp k) ~priv ~preview ~strip ()
let picture k = jpeg ~xmp:(xmp k) ~profile:(noise 600 4) ~scan:(noise 5000 6)
let sidecar k = "<?xml version='1.0'?>\n" ^ xmp k

(* ---- Files and a store in a disposable directory ---- *)

let top =
  let dir = Filename.get_temp_dir_name () // Printf.sprintf "unison-skeleton-test-%d" (Unix.getpid ()) in
  Unix.mkdir dir 0o700;
  dir

let rec remove_tree path =
  match Unix.lstat path with
  | { Unix.st_kind = Unix.S_DIR; _ } ->
      Array.iter (fun name -> remove_tree (path // name)) (Sys.readdir path);
      Unix.rmdir path
  | _ -> Unix.unlink path
  | exception Unix.Unix_error _ -> ()

let write_file file content =
  let oc = open_out_bin (file ^ ".new") in
  output_string oc content;
  close_out oc;
  Unix.rename (file ^ ".new") file

let read_file file =
  let ic = open_in_bin file in
  let s = really_input_string ic (in_channel_length ic) in
  close_in ic;
  s

let sha s = SemanticHash.hex (SemanticHash.string s)

let store = top // "store"
let root = top // "replica"
let () = Unix.mkdir root 0o700

(* What a synchronization does to a file it replaces: take the old one,
   put the new one in place, settle. *)
let replace ?(depth = 3) path content =
  let file = root // path in
  ignore (SkeletonStore.stash ~store ~root ~path ~file ~how:`Copy ~depth ());
  write_file file content;
  SkeletonStore.settle ~store ~root ~path ~live:file ~depth ()

let live path = let file = root // path in if Sys.file_exists file then Some file else None

let restored path seq =
  let b = Buffer.create 65536 in
  match
    SkeletonStore.restore ~store ~root ~path ~live:(live path) ~seq
      ~write:(Buffer.add_substring b) ~reset:(fun () -> Buffer.clear b)
  with
  | () -> Ok (Buffer.contents b)
  | exception Failure why -> Error why

let versions path =
  match SkeletonStore.chain ~store ~root ~path with
  | Some chain -> chain.SkeletonStore.versions
  | None -> []

let seqs path = List.map (fun (v : SkeletonStore.version) -> v.SkeletonStore.seq) (versions path)
let all_ok path =
  List.for_all (fun (_, r) -> r = None) (SkeletonStore.verify ~store ~root ~path ~live:(live path))
let total path = let (r, b, w) = SkeletonStore.stored_bytes ~store ~root ~path in r + b + w
let kept_blocks path = let (_, b, _) = SkeletonStore.stored_bytes ~store ~root ~path in b
let whole_bytes path = let (_, _, w) = SkeletonStore.stored_bytes ~store ~root ~path in w
let is_whole path seq =
  List.exists (fun (v : SkeletonStore.version) ->
    v.SkeletonStore.seq = seq && v.SkeletonStore.kind = SkeletonStore.Whole) (versions path)

(* ---- The cuts ---- *)

let cut_fixtures = [
  "photo.dng", photo 0;
  "photo-edited.dng", photo 3;
  "motorola.tif", tiff ~be:true ~xmp:(xmp 1) ~priv ~preview ~strip ();
  "gap.dng", tiff ~gap:70000 ~xmp:(xmp 0) ~priv ~preview ~strip ();
  "picture.jpg", picture 0;
  "sidecar.xmp", sidecar 0;
]

let describe name content =
  let file = top // ("cut-" ^ name) in
  write_file file content;
  let sk = Skeleton.build file in
  sk.Skeleton.format, sha sk.Skeleton.bytes,
  List.map (fun (b : Skeleton.block) -> b.Skeleton.at, b.Skeleton.len, b.Skeleton.mark, b.Skeleton.role)
    sk.Skeleton.blocks

(* What dng-compare's skeleton.py gives for the same bytes (format, SHA-256 of
   the skeleton bytes, blocks as offset, length, mark, role). *)
let expected_cuts = [
  "photo.dng", ("tiff", "8d73066a8496c177eb76b28e36afb18e2f352267803a7f0b05e8f081c4383aac",
    [ (6058, 800, "d3a9fc53cbc6b97431e5577bbb8fc643", "0/tag50740");
      (6858, 6000, "eb005cd72d6acafe9e8320a59d19db34", "0/330.0/jpeg");
      (12858, 20000, "67e256c2486d93b24d0ae59ca8487b8b", "0/strips") ]);
  "photo-edited.dng", ("tiff", "6acaf399e3bdfebbca4ae97f399ccaf43b81b8bc42820cca9766b1bc1e01baf6",
    [ (6250, 800, "d3a9fc53cbc6b97431e5577bbb8fc643", "0/tag50740");
      (7050, 6000, "eb005cd72d6acafe9e8320a59d19db34", "0/330.0/jpeg");
      (13050, 20000, "67e256c2486d93b24d0ae59ca8487b8b", "0/strips") ]);
  "motorola.tif", ("tiff", "6e46edbb7ab650e6133d26ff3f70b2d715b4ac7a8afc60145ef1b6a196c74ee3",
    [ (6122, 800, "d3a9fc53cbc6b97431e5577bbb8fc643", "0/tag50740");
      (6922, 6000, "eb005cd72d6acafe9e8320a59d19db34", "0/330.0/jpeg");
      (12922, 20000, "67e256c2486d93b24d0ae59ca8487b8b", "0/strips") ]);
  "gap.dng", ("tiff", "8d73066a8496c177eb76b28e36afb18e2f352267803a7f0b05e8f081c4383aac",
    [ (6058, 800, "d3a9fc53cbc6b97431e5577bbb8fc643", "0/tag50740");
      (6858, 6000, "eb005cd72d6acafe9e8320a59d19db34", "0/330.0/jpeg");
      (12858, 20000, "67e256c2486d93b24d0ae59ca8487b8b", "0/strips");
      (32858, 70000, "2d57368436f228dcefaffcbcd733da7b", "gap") ]);
  "picture.jpg", ("jpeg", "5f76777714f1c93e64dc463130dbd861e19cc845e168b63d5ff580db3a772b7e",
    [ (5941, 604, "ee1b3151f19afd34d7660851c01db562", "sege2");
      (6614, 5012, "9ecd768d535bdc2be659bf8bebcc942c", "scan") ]);
  "sidecar.xmp", ("whole", "9dbd8c9a9c64cf65929feaecc0f60a3c4b8d8ad60e71f5bf403d59a8cc6cbba3",
    [  ]);
]

let dump dir =
  List.iter (fun (name, content) ->
    write_file (dir // name) content;
    let format, skeleton, blocks = describe name content in
    Printf.printf "%s %s %s\n" name format skeleton;
    List.iter (fun (at, len, mark, role) -> Printf.printf "  %d %d %s %s\n" at len mark role) blocks)
    cut_fixtures

let test_cuts () =
  section "walker cuts";
  List.iter (fun (name, content) ->
    let got = describe name content in
    match List.assoc_opt name expected_cuts with
    | Some want -> check ("cuts of " ^ name) (got = want)
    | None -> check ("expected cuts for " ^ name) false) cut_fixtures;
  let big = top // "big.bin" in
  write_file big (String.make (Skeleton.whole + 1) 'x');
  check "a large file without a walker has no skeleton"
    (match Skeleton.build big with _ -> false | exception Failure _ -> true)

(* ---- The delta ---- *)

let test_delta () =
  section "delta";
  let round name base target =
    let delta = SkeletonDelta.make ~base ~target in
    check (Printf.sprintf "round trip: %s (%d -> %d bytes, delta %d)" name (String.length base)
             (String.length target) (String.length delta))
      (SkeletonDelta.apply ~base ~delta = target);
    delta in
  ignore (round "empty to empty" "" "");
  ignore (round "empty base" "" (noise 300 1));
  ignore (round "empty target" (noise 300 1) "");
  ignore (round "short strings" "abc" "abd");
  ignore (round "unrelated" (noise 5000 1) (noise 5000 2));
  let same = round "identical" (noise 9000 3) (noise 9000 3) in
  check "an identical target is one copy" (String.length same < 32);
  let a = xmp 2 and b = xmp 3 in
  let d = round "successive packets" a b in
  check "successive packets give a small delta" (String.length d < String.length b / 10);
  let shifted = round "insertion in the middle" (noise 4000 4 ^ noise 4000 5) (noise 4000 4 ^ "inserted" ^ noise 4000 5) in
  check "an insertion costs little" (String.length shifted < 64);
  ignore (round "repeated bytes" (String.make 5000 ' ') (String.make 4000 ' ' ^ "x" ^ String.make 3000 ' '));
  let big = noise 300000 9 in
  ignore (round "large, one byte changed" big (String.mapi (fun i c -> if i = 150000 then 'Z' else c) big));
  let rejects name base delta =
    check ("rejected: " ^ name)
      (match SkeletonDelta.apply ~base ~delta with
       | _ -> false
       | exception SkeletonDelta.Corrupt _ -> true) in
  rejects "another base" (a ^ "x") d;
  rejects "truncated" a (String.sub d 0 (String.length d - 1));
  rejects "not a delta" a "junk";
  rejects "trailing bytes" a (d ^ "x");
  rejects "copy out of range" "abc" "SKD1\003\005\001\002\005\000"

(* ---- The store ---- *)

let test_chain () =
  section "a chain of metadata edits, three versions kept";
  let path = "chain/photo.dng" in
  Unix.mkdir (root // "chain") 0o700;
  write_file (root // path) (photo 0);
  let skeleton_bytes = String.length (Skeleton.build (root // path)).Skeleton.bytes in
  let sizes = List.map (fun k ->
      let outcome = replace path (photo k) in
      check (Printf.sprintf "edit %d keeps a skeleton and no blocks" k)
        (match outcome with SkeletonStore.Kept_skeleton (_, 0) -> true | _ -> false);
      total path) [ 1; 2; 3; 4; 5 ] in
  check "versions 3, 4 and 5 are kept" (seqs path = [ 3; 4; 5 ]);
  List.iter (fun seq ->
    check (Printf.sprintf "version %d restores byte for byte" seq) (restored path seq = Ok (photo (seq - 1))))
    [ 3; 4; 5 ];
  List.iter (fun seq ->
    check (Printf.sprintf "pruned version %d is gone" seq)
      (match restored path seq with Error _ -> true | Ok _ -> false)) [ 1; 2 ];
  check "no block and no whole file is stored" (kept_blocks path = 0 && whole_bytes path = 0);
  (match sizes with
   | [ s1; s2; s3; s4; s5 ] ->
       Printf.printf "     file %d bytes, skeleton %d bytes; store after each edit: %d %d %d %d %d bytes\n"
         (String.length (photo 0)) skeleton_bytes s1 s2 s3 s4 s5;
       Printf.printf "     growth per edit: %d, %d (chain filling); %d, %d (oldest pruned)\n"
         (s2 - s1) (s3 - s2) (s4 - s3) (s5 - s4);
       check "the first version costs about one skeleton" (s1 < skeleton_bytes + 1024);
       check "each further version costs far less than a skeleton"
         (s2 - s1 < skeleton_bytes / 5 && s3 - s2 < skeleton_bytes / 5);
       check "a full chain stops growing" (s4 - s3 < skeleton_bytes / 5 && s5 - s4 < skeleton_bytes / 5)
   | _ -> check "five sizes" false);
  check "only the newest record is stored in full"
    (List.map (fun (v : SkeletonStore.version) -> v.SkeletonStore.stored) (versions path)
     = [ SkeletonStore.Delta 4; SkeletonStore.Delta 5; SkeletonStore.Full ]);
  check "verify finds every version exact" (all_ok path);
  let jpg = "chain/picture.jpg" in
  write_file (root // jpg) (picture 0);
  List.iter (fun k -> ignore (replace jpg (picture k))) [ 1; 2; 3; 4 ];
  check "a JPEG chain restores too"
    (seqs jpg = [ 2; 3; 4 ] && List.for_all (fun seq -> restored jpg seq = Ok (picture (seq - 1))) [ 2; 3; 4 ])

let test_lost_block () =
  section "an edit that replaces a block";
  let path = "preview.dng" in
  write_file (root // path) (photo 0);
  ignore (replace path (photo 1));
  let outcome = replace path (photo ~preview:(noise 6100 42) 2) in
  check "the replaced preview is captured" (outcome = SkeletonStore.Kept_skeleton (2, 6000));
  check "the store holds that block and nothing else of the image" (kept_blocks path = 6000);
  check "the version before the new preview restores" (restored path 2 = Ok (photo 1));
  check "so does the one before it, which shares the block" (restored path 1 = Ok (photo 0));
  ignore (replace path (photo ~preview:(noise 6100 42) 3));
  check "a later metadata edit keeps one copy of the block" (kept_blocks path = 6000 && all_ok path);
  check "all three restore"
    (restored path 1 = Ok (photo 0) && restored path 2 = Ok (photo 1)
     && restored path 3 = Ok (photo ~preview:(noise 6100 42) 2));
  ignore (replace path (photo ~preview:(noise 6100 42) 4));
  ignore (replace path (photo ~preview:(noise 6100 42) 5));
  check "the block goes when no kept version needs it" (seqs path = [ 3; 4; 5 ] && kept_blocks path = 0);
  check "what is left still restores" (all_ok path)

let test_middle_change () =
  section "an edit that changes the middle of a block";
  let path = "middle.dng" in
  let changed = String.mapi (fun i c -> if i = 10000 then Char.chr (Char.code c lxor 1) else c) strip in
  write_file (root // path) (photo 0);
  ignore (replace path (photo 1));
  let sk1 = Skeleton.build (root // path) in
  write_file (top // "probe.dng") (photo ~strip:changed 1);
  let sk2 = Skeleton.build (top // "probe.dng") in
  check "the marks cannot tell the two strips apart"
    (List.map (fun (b : Skeleton.block) -> b.Skeleton.mark) sk1.Skeleton.blocks
     = List.map (fun (b : Skeleton.block) -> b.Skeleton.mark) sk2.Skeleton.blocks);
  let outcome = replace path (photo ~strip:changed 2) in
  check "the changed strip is captured whole" (outcome = SkeletonStore.Kept_skeleton (2, 20000));
  check "the version before the change restores" (restored path 2 = Ok (photo 1));
  check "and the one before that" (restored path 1 = Ok (photo 0));
  ignore (replace path (photo ~strip:changed 3));
  check "after a further edit all three restore"
    (restored path 1 = Ok (photo 0) && restored path 2 = Ok (photo 1)
     && restored path 3 = Ok (photo ~strip:changed 2));
  (* A version whose skeleton does not rebuild it is kept as a whole file. *)
  let path = "distrusted.dng" in
  write_file (root // path) (photo 0);
  ignore (replace path (photo 1));
  SkeletonStore.before_check := (fun () -> failwith "made to fail");
  let outcome = replace path (photo 2) in
  SkeletonStore.before_check := (fun () -> ());
  check "a version that fails its check is kept whole"
    (match outcome with SkeletonStore.Kept_whole (2, _) -> true | _ -> false);
  check "it is a whole file in the store" (is_whole path 2 && whole_bytes path = String.length (photo 1));
  check "it restores, and so does the version before it"
    (restored path 2 = Ok (photo 1) && restored path 1 = Ok (photo 0));
  ignore (replace path (photo 3));
  ignore (replace path (photo 4));
  ignore (replace path (photo 5));
  check "it is pruned by depth like any version" (seqs path = [ 3; 4; 5 ] && whole_bytes path = 0 && all_ok path)

let test_sidecar () =
  section "a sidecar chain";
  let path = "photo.xmp" in
  write_file (root // path) (sidecar 0);
  let sizes = List.map (fun k -> ignore (replace path (sidecar k)); total path) [ 1; 2; 3; 4 ] in
  check "three versions, all of format whole"
    (seqs path = [ 2; 3; 4 ]
     && List.for_all (fun (v : SkeletonStore.version) ->
          v.SkeletonStore.kind = SkeletonStore.Skel && v.SkeletonStore.format = "whole") (versions path));
  check "they restore" (List.for_all (fun seq -> restored path seq = Ok (sidecar (seq - 1))) [ 2; 3; 4 ]);
  (match sizes with
   | s1 :: s2 :: s3 :: _ ->
       Printf.printf "     sidecar %d bytes; store after each edit: %s bytes\n" (String.length (sidecar 0))
         (String.concat " " (List.map string_of_int sizes));
       check "each further sidecar version is a small delta"
         (s2 - s1 < String.length (sidecar 0) / 5 && s3 - s2 < String.length (sidecar 0) / 5)
   | _ -> check "sizes" false);
  Sys.remove (root // path);
  check "a sidecar's versions need no current file" (all_ok path)

let test_pending () =
  section "pending items";
  let path = "pending.dng" in
  let file = root // path in
  write_file file (photo 0);
  ignore (replace path (photo 1));
  (* An interrupted run: the old file was taken, the new one put in place,
     and nothing settled. *)
  ignore (SkeletonStore.stash ~store ~root ~path ~file ~how:`Copy ~depth:3 ());
  write_file file (photo 2);
  check "the item is pending" (SkeletonStore.pending_paths ~store ~root = [ path ] && seqs path = [ 1 ]);
  check "versions restore while it is pending" (restored path 1 = Ok (photo 0));
  let settled, failed = SkeletonStore.settle_all ~store ~root ~live:(fun p -> root // p) ~depth:3 () in
  check "the next start settles it"
    (failed = [] && settled = [ path, SkeletonStore.Kept_skeleton (2, 0) ]
     && SkeletonStore.pending_paths ~store ~root = [] && seqs path = [ 1; 2 ]);
  check "and it restores" (restored path 2 = Ok (photo 1));
  (* Or the next replacement of the same path settles it. *)
  ignore (SkeletonStore.stash ~store ~root ~path ~file ~how:`Copy ~depth:3 ());
  write_file file (photo 3);
  ignore (replace path (photo 4));
  check "a leftover item is settled by the next stash of its path"
    (seqs path = [ 2; 3; 4 ] && restored path 3 = Ok (photo 2) && restored path 4 = Ok (photo 3));
  (* A replacement that did not happen leaves no version. *)
  ignore (SkeletonStore.stash ~store ~root ~path ~file ~how:`Copy ~depth:3 ());
  check "a file that was not replaced after all gives no version"
    (SkeletonStore.settle ~store ~root ~path ~live:file ~depth:3 () = SkeletonStore.Unchanged
     && seqs path = [ 2; 3; 4 ] && SkeletonStore.pending_paths ~store ~root = []);
  (* A run that stopped after keeping a version whole, before the index. *)
  let cut = "cut.dng" in
  write_file (root // cut) (photo 0);
  ignore (SkeletonStore.stash ~store ~root ~path:cut ~file:(root // cut) ~how:`Move ~depth:3 ());
  let pdir = ref "" in
  let rec find d =
    Array.iter (fun name ->
      let f = d // name in
      if Sys.is_directory f then find f else if name = "1.pending" then pdir := d) (Sys.readdir d) in
  find (SkeletonStore.root_dir ~store ~root);
  Unix.rename (!pdir // "1.pending") (!pdir // "1.whole");
  let settled, _ = SkeletonStore.settle_all ~store ~root ~live:(fun p -> root // p) ~depth:3 () in
  check "a whole version renamed before the index was written is not lost"
    (List.map fst settled = [ cut ] && is_whole cut 1 && restored cut 1 = Ok (photo 0));
  let under = "sub/inner.dng" in
  Unix.mkdir (root // "sub") 0o700;
  write_file (root // under) (photo 0);
  ignore (SkeletonStore.stash ~store ~root ~path:under ~file:(root // under) ~how:`Copy ~depth:3 ());
  write_file (root // under) (photo 1);
  let settled, _ = SkeletonStore.settle_all ~store ~root ~under:"other" ~live:(fun p -> root // p) ~depth:3 () in
  check "settling under another path leaves it" (settled = [] && SkeletonStore.pending_paths ~store ~root = [ under ]);
  let settled, _ = SkeletonStore.settle_all ~store ~root ~under:"sub" ~live:(fun p -> root // p) ~depth:3 () in
  check "settling under its directory settles it"
    (List.map fst settled = [ under ] && restored under 1 = Ok (photo 0))

let test_whole () =
  section "what cannot be a skeleton";
  let path = "deleted.dng" in
  let file = root // path in
  write_file file (photo 0);
  ignore (replace path (photo 1));
  let moved = SkeletonStore.stash ~store ~root ~path ~file ~how:`Move ~depth:3 () in
  let outcome = SkeletonStore.settle ~store ~root ~path ~live:file ~gone:true ~depth:3 () in
  check "a deleted file is moved into the store and kept whole"
    (moved && not (Sys.file_exists file) && is_whole path 2
     && (match outcome with SkeletonStore.Kept_whole (2, _) -> true | _ -> false));
  check "it restores" (restored path 2 = Ok (photo 1));
  check "the version before it rebuilds from the whole file" (restored path 1 = Ok (photo 0));
  let path = "small.xmp" in
  write_file (root // path) (sidecar 0);
  ignore (SkeletonStore.stash ~store ~root ~path ~file:(root // path) ~how:`Move ~depth:3 ());
  ignore (SkeletonStore.settle ~store ~root ~path ~live:(root // path) ~gone:true ~depth:3 ());
  check "a deleted sidecar is its own skeleton" (not (is_whole path 1) && restored path 1 = Ok (sidecar 0));
  let path = "movie.bin" in
  let old = noise (Skeleton.whole + 4096) 8 in
  write_file (root // path) old;
  let outcome = replace path (noise (Skeleton.whole + 4096) 9) in
  check "a large file without a walker is kept whole"
    (match outcome with SkeletonStore.Kept_whole (1, _) -> restored path 1 = Ok old | _ -> false);
  let path = "depth.dng" in
  write_file (root // path) (photo 0);
  ignore (replace ~depth:1 path (photo 1));
  ignore (replace ~depth:1 path (photo 2));
  check "a depth of one keeps one" (seqs path = [ 2 ] && restored path 2 = Ok (photo 1))

let test_damage () =
  section "damage is reported, never restored";
  let path = "damage.dng" in
  write_file (root // path) (photo 0);
  List.iter (fun k -> ignore (replace path (photo k))) [ 1; 2; 3 ];
  check "the chain is sound" (all_ok path);
  (* The limit: a local edit that destroys a block between synchronizations. *)
  let current = read_file (root // path) in
  write_file (root // path) (photo ~preview:(noise 6000 99) 3);
  check "after a local edit that regenerates the preview, no version rebuilds"
    (List.for_all (fun (_, r) -> r <> None) (SkeletonStore.verify ~store ~root ~path ~live:(live path)));
  check "and restore refuses" (match restored path 3 with Error _ -> true | Ok _ -> false);
  write_file (root // path) current;
  check "with the block back they rebuild" (all_ok path);
  (* A damaged delta breaks the versions that depend on it, visibly. *)
  let dir = ref "" in
  let rec find d =
    Array.iter (fun name ->
      let f = d // name in
      if Sys.is_directory f then find f
      else if name = "index" && (let s = read_file f in
                                 let needle = "path " ^ path ^ "\n" in
                                 let n = String.length needle in
                                 let rec has i = i + n <= String.length s && (String.sub s i n = needle || has (i + 1)) in
                                 has 0) then dir := d) (Sys.readdir d) in
  find (SkeletonStore.root_dir ~store ~root);
  let delta = !dir // "2.delta" in
  let good = read_file delta in
  write_file delta (String.mapi (fun i c -> if i = String.length good / 2 then Char.chr (Char.code c lxor 0x55) else c) good);
  let results = SkeletonStore.verify ~store ~root ~path ~live:(live path) in
  check "a damaged delta fails the versions that need it and no other"
    (List.map (fun ((v : SkeletonStore.version), r) -> v.SkeletonStore.seq, r = None) results
     = [ 1, false; 2, false; 3, true ]);
  write_file delta good;
  check "restored delta, sound chain" (all_ok path)

(* ---- A synchronization ---- *)

let run ?(env = []) prog args out =
  let fd = Unix.openfile out [ Unix.O_WRONLY; Unix.O_CREAT; Unix.O_TRUNC ] 0o600 in
  let env = Array.append (Array.of_list env) (Unix.environment ()) in
  let pid = Unix.create_process_env prog (Array.of_list (prog :: args)) env Unix.stdin fd fd in
  Unix.close fd;
  match snd (Unix.waitpid [] pid) with Unix.WEXITED n -> n | _ -> 255

let test_sync unison tool =
  section "a synchronization";
  let a = top // "a" and b = top // "b" and dir = top // "sync-store" and out = top // "out.txt" in
  Unix.mkdir a 0o700; Unix.mkdir b 0o700; Unix.mkdir (top // "unisondir") 0o700;
  let env = [ "UNISON=" ^ (top // "unisondir"); "HOME=" ^ top ] in
  let sync () =
    run ~env unison
      [ a; b; "-batch"; "-ui"; "text"; "-skeleton"; "Name *.dng"; "-skeleton"; "Name *.xmp";
        "-skeletonnot"; "Name unkept.xmp"; "-maxskeletons"; "3"; "-skeletondir"; dir;
        "-logfile"; top // "unison.log" ] out in
  let tool_run args = run ~env tool (args @ [ "--skeletondir"; dir ]) out in
  write_file (a // "photo.dng") (photo 0);
  write_file (a // "photo.xmp") (sidecar 0);
  write_file (a // "unkept.xmp") (sidecar 0);
  check "first synchronization" (sync () = 0);
  check "a first copy keeps nothing" (not (Sys.file_exists dir) || tool_run [ "verify"; b ] = 0);
  List.iter (fun k ->
    write_file (a // "photo.dng") (photo k);
    write_file (a // "photo.xmp") (sidecar k);
    write_file (a // "unkept.xmp") (sidecar k);
    check (Printf.sprintf "synchronization after edit %d" k) (sync () = 0)) [ 1; 2; 3; 4 ];
  check "the replica received the last edit" (read_file (b // "photo.dng") = photo 4);
  check "list succeeds" (tool_run [ "list"; b ] = 0);
  let listing = read_file out in
  print_string listing;
  let count needle =
    let n = String.length needle in
    let rec go i acc =
      if i + n > String.length listing then acc
      else go (i + 1) (if String.sub listing i n = needle then acc + 1 else acc) in
    go 0 0 in
  check "three versions of the photo and three of its sidecar, none of the excluded file"
    (count "  version " = 6 && count "unkept" = 0 && count "pending" = 0);
  check "verify rebuilds all of them" (tool_run [ "verify"; b ] = 0);
  check "the sending replica kept nothing" (tool_run [ "list"; a ] = 0 && read_file out = "");
  List.iter (fun k ->
    let target = top // Printf.sprintf "restored-%d.dng" k in
    check (Printf.sprintf "restore of the photo before edit %d" (k + 1))
      (tool_run [ "restore"; b; "photo.dng"; "--sha256"; sha (photo k); "--out"; target ] = 0
       && read_file target = photo k)) [ 1; 2; 3 ];
  check "the pruned first version is not restorable"
    (tool_run [ "restore"; b; "photo.dng"; "--sha256"; sha (photo 0); "--out"; top // "no.dng" ] <> 0
     && not (Sys.file_exists (top // "no.dng")));
  check "restore refuses to write inside the replica"
    (tool_run [ "restore"; b; "photo.dng"; "--sha256"; sha (photo 3); "--out"; b // "old.dng" ] <> 0
     && not (Sys.file_exists (b // "old.dng")));
  check "restore refuses to overwrite a file"
    (tool_run [ "restore"; b; "photo.dng"; "--sha256"; sha (photo 3); "--out"; top // "restored-1.dng" ] <> 0
     && read_file (top // "restored-1.dng") = photo 1);
  let target = top // "restored.xmp" in
  check "restore of a sidecar version by number"
    (tool_run [ "restore"; b; "photo.xmp"; "--version"; "3"; "--out"; target ] = 0
     && read_file target = sidecar 2);
  Sys.remove (a // "photo.dng");
  check "synchronization after deleting the photo" (sync () = 0 && not (Sys.file_exists (b // "photo.dng")));
  let target = top // "restored-deleted.dng" in
  check "the deleted photo restores"
    (tool_run [ "restore"; b; "photo.dng"; "--sha256"; sha (photo 4); "--out"; target ] = 0
     && read_file target = photo 4);
  check "and every kept version still rebuilds" (tool_run [ "verify"; b ] = 0);
  print_string (read_file out)

let () =
  let unison = ref None and tool = ref None and dump_dir = ref None in
  let rec parse = function
    | "--unison" :: v :: rest -> unison := Some v; parse rest
    | "--tool" :: v :: rest -> tool := Some v; parse rest
    | "--dump" :: v :: rest -> dump_dir := Some v; parse rest
    | [] -> ()
    | arg :: _ -> prerr_endline ("unknown argument " ^ arg); exit 2 in
  parse (List.tl (Array.to_list Sys.argv));
  let absolute f = if Filename.is_relative f then Sys.getcwd () // f else f in
  Fun.protect ~finally:(fun () -> remove_tree top) (fun () ->
    match !dump_dir with
    | Some dir -> dump dir
    | None ->
        test_cuts ();
        test_delta ();
        test_chain ();
        test_lost_block ();
        test_middle_change ();
        test_sidecar ();
        test_pending ();
        test_whole ();
        test_damage ();
        (match !unison, !tool with
         | Some unison, Some tool -> test_sync (absolute unison) (absolute tool)
         | _ -> Printf.printf "\n== a synchronization: skipped (needs --unison and --tool)\n");
        Printf.printf "\n%d checks, %d failed\n" !checks !failures);
  if !failures > 0 then exit 1
