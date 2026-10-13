(* Conservative classic TIFF/DNG XMP locator. This is not a DNG validator
   or raw-image fingerprint. All bytes outside the returned extent are
   independently covered by the semantic transfer core's preservation proof. *)
let profile = "org.firstpair.dng-xmp/0"
exception Unsupported of string
let reject s = raise (Unsupported s)
type directory_kind = Image | Exif | Gps | Interop

(* Values in this deliberately finite profile either live wholly in their
   TIFF value extent or use one of the graph/image-offset rules below.
   Unknown fields are not safe to treat as ordinary values: private LONGs
   and opaque MakerNotes can contain offsets into the proposed XMP packet. *)
let image_value_tag = function
  | 254 | 255 | 256 | 257 | 258 | 259 | 262 | 263 | 264 | 265 | 266
  | 269 | 270 | 271 | 272 | 274 | 277 | 278 | 280 | 281 | 282 | 283
  | 284 | 285 | 286 | 287 | 290 | 291 | 292 | 293 | 296 | 297 | 301
  | 305 | 306 | 315 | 316 | 317 | 318 | 319 | 320 | 321 | 322 | 323
  | 332 | 333 | 334 | 336 | 337 | 338 | 339 | 340 | 341 | 342 | 347
  | 512 | 515 | 517 | 518 | 529 | 530 | 531 | 532
  | 33421 | 33422 | 33432 | 33723 | 34377 | 34675
  | 50741 | 50778 | 50779 | 50780 | 50781 | 50879 | 50931 | 50932
  | 50981 | 50982 | 51008 | 51009 | 51022 | 51041
  | 51089 | 51090 | 51091 | 51125 -> true
  | tag when tag >= 50706 && tag <= 50739 -> true
  | tag when tag >= 50827 && tag <= 50834 -> true
  | tag when tag >= 50934 && tag <= 50942 -> true
  | tag when tag >= 50964 && tag <= 50975 -> true
  | tag when tag >= 51107 && tag <= 51112 -> true
  | _ -> false

let exif_value_tag = function
  | 33434 | 33437 | 34850 | 34852 | 34855 | 34856 | 34864 | 34865
  | 34866 | 34867 | 34868 | 34869 | 36864 | 36867 | 36868 | 36880
  | 36881 | 36882 | 37121 | 37122 | 37377 | 37378 | 37379 | 37380
  | 37381 | 37382 | 37383 | 37384 | 37385 | 37386 | 37396 | 37510
  | 37520 | 37521 | 37522 | 40960 | 40961 | 40962 | 40963 | 40964
  | 41483 | 41484 | 41486 | 41487 | 41488 | 41492 | 41493 | 41495
  | 41728 | 41729 | 41730 | 41985 | 41986 | 41987 | 41988 | 41989
  | 41990 | 41991 | 41992 | 41993 | 41994 | 41995 | 41996 | 42016
  | 42032 | 42033 | 42034 | 42035 | 42036 | 42037 -> true
  | _ -> false

let child_kind kind tag = match kind, tag with
  | Image, 330 -> Some Image
  | Image, 34665 -> Some Exif
  | Image, 34853 -> Some Gps
  | Exif, 40965 -> Some Interop
  | _ -> None

let allowed_tag kind tag = match kind with
  | Image -> image_value_tag tag || exif_value_tag tag ||
      List.mem tag [273;279;324;325;513;514;700;330;34665;34853]
  | Exif -> exif_value_tag tag || tag = 40965
  | Gps -> tag >= 0 && tag <= 31
  | Interop -> List.mem tag [1;2;4096;4097;4098]

let inspect file =
 try
  let size = SemanticFile.size file in
  let header = SemanticFile.read file 0L 8 in
  let little = match String.sub header 0 2 with
    | "II" -> true | "MM" -> false | _ -> reject "not TIFF" in
  let number s pos n =
    let v = ref 0L in
    for j = 0 to n-1 do
      let i = if little then n-1-j else j in
      v := Int64.logor (Int64.shift_left !v 8) (Int64.of_int (Char.code s.[pos+i]))
    done; !v in
  if number header 2 2 <> 42L then reject "unsupported TIFF version (including BigTIFF)";
  let extent offset length =
    if offset < 0L || length < 0L || offset > size || length > Int64.sub size offset then
      reject "TIFF extent outside file";
    (offset, Int64.add offset length) in
  let protected = ref [extent 0L 8L] and extent_count = ref 1 in
  let protect offset length =
    incr extent_count;
    if !extent_count > 131072 then reject "protected extent limit";
    protected := extent offset length :: !protected in
  let seen = Hashtbl.create 32 and queue = Queue.create () in
  let enqueue kind offset = if offset <> 0L then begin
    (* Bound pending work as well as visited nodes. Checking only at dequeue
       allows a small pointer table to enqueue millions of offsets first. *)
    if Queue.length queue + Hashtbl.length seen >= 256 then reject "IFD work limit";
    Queue.add (kind, offset) queue
  end in
  let primary = number header 4 4 in
  enqueue Image primary;
  let entries = ref 0 and xmp = ref None and dng = ref false in
  while not (Queue.is_empty queue) do
    let kind, offset = Queue.take queue in
    if Hashtbl.mem seen offset then reject "repeated or cyclic IFD";
    if Hashtbl.length seen >= 256 then reject "IFD limit";
    Hashtbl.add seen offset ();
    let count = Int64.to_int (number (SemanticFile.read file offset 2) 0 2) in
    entries := !entries + count;
    if !entries > 16384 then reject "TIFF entry limit";
    let length = 2 + 12*count + 4 in
    protect offset (Int64.of_int length);
    let directory = SemanticFile.read file offset length in
    let tags = Hashtbl.create count in
    for i = 0 to count-1 do
      let at = 2+12*i in
      let tag = Int64.to_int (number directory at 2) in
      let typ = Int64.to_int (number directory (at+2) 2) in
      let n = number directory (at+4) 4 in
      if Hashtbl.mem tags tag then reject "duplicate TIFF tag";
      if not (allowed_tag kind tag) then
        reject (Printf.sprintf "unsupported TIFF tag %d (opaque or private graph)" tag);
      let child = child_kind kind tag in
      if typ = 13 && child = None then reject "IFD type on non-pointer field";
      let width = match typ with
        | 1 | 2 | 6 | 7 -> 1 | 3 | 8 -> 2 | 4 | 9 | 11 | 13 -> 4
        | 5 | 10 | 12 -> 8 | _ -> reject "unsupported TIFF field type" in
      let bytes = Int64.mul n (Int64.of_int width) in
      let value_offset = if bytes <= 4L then Int64.add offset (Int64.of_int (at+8))
        else number directory (at+8) 4 in
      ignore (extent value_offset bytes);
      Hashtbl.add tags tag (typ,n,value_offset);
      if tag = 700 then begin
        if !xmp <> None then reject "multiple XMP packets";
        if typ <> 1 || n <= 4L || n > Int64.of_int FormatExtension.max_region then
          reject "unsupported XMP type or packet size";
        xmp := Some {FormatExtension.offset = value_offset; length = Int64.to_int n}
      end else if bytes > 4L then protect value_offset bytes;
      if tag = 50706 then begin
        if typ <> 1 || n <> 4L then reject "invalid DNGVersion";
        let version = SemanticFile.read file value_offset 4 in
        if Char.code version.[0] <> 1 || Char.code version.[1] > 7 then
          reject "unsupported DNG version";
        if kind = Image && offset = primary then dng := true
      end;
      begin match child with
      | None -> ()
      | Some child_kind ->
        if typ <> 4 && typ <> 13 then reject "invalid IFD pointer type";
        if tag <> 330 && n <> 1L then reject "invalid singleton IFD pointer count";
        if n > 256L then reject "IFD pointer limit";
        let pointers = SemanticFile.read file value_offset (4 * Int64.to_int n) in
        for j = 0 to Int64.to_int n - 1 do enqueue child_kind (number pointers (4*j) 4) done
      end
    done;
    let values tag =
      let typ,n,off = Hashtbl.find tags tag in
      if n > 65536L then reject "image extent limit";
      let width = match typ with 3 -> 2 | 4 -> 4 | _ -> reject "invalid image extent type" in
      let data = SemanticFile.read file off (Int64.to_int n * width) in
      (n, fun i -> number data (Int64.to_int i * width) width)
    in
    List.iter (fun (offsets,lengths) ->
      let has_o = Hashtbl.mem tags offsets and has_l = Hashtbl.mem tags lengths in
      if has_o <> has_l then reject "unpaired image extents";
      if has_o then begin
        let n,get_o = values offsets and m,get_l = values lengths in
        if n <> m then reject "mismatched image extents";
        let i = ref 0L in
        while !i < n do protect (get_o !i) (get_l !i); i := Int64.succ !i done
      end) [273,279;324,325;513,514];
    enqueue kind (number directory (2+12*count) 4)
  done;
  if not !dng then reject "missing DNGVersion";
  let region = match !xmp with None -> reject "no embedded XMP" | Some r -> r in
  let stop = Int64.add region.FormatExtension.offset (Int64.of_int region.FormatExtension.length) in
  List.iter (fun (a,b) ->
    if a < stop && region.FormatExtension.offset < b then reject "XMP aliases protected extent") !protected;
  SemanticFile.check file;
  Ok {FormatExtension.regions = [region]}
 with Unsupported s | SemanticFile.Invalid s -> Error s
