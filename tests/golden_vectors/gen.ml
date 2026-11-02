(* Golden vectors for phidentify's SDE/0-preserved digest (P-19).
   Builder.* is tiffgraph's own test builder (test/test_tiffgraph.ml), copied
   verbatim by run.py; the digest and profile come from Unison's SemanticDelta,
   with each DNG profile as Unison registers it (Known_metadata spans,
   max_payload = FormatExtension.max_region = 1 MiB). Synthetic bytes only. *)
open Builder

module OpaqueMaker = struct
  let profile = DngSemantic.opaque_maker_profile
  let inspect = DngSemantic.inspect_opaque_maker
end
let profiles = [
  "org.firstpair.dng-xmp/0", (module DngSemantic : FormatExtension.S);
  "org.firstpair.dng-xmp/1", (module DngExtended : FormatExtension.S);
  "org.firstpair.dng-xmp/2", (module OpaqueMaker : FormatExtension.S) ]

let vectors =
  let probe = build (dng ()) in
  [ "v0-classic-le", build (dng ());
    "v0-classic-be", build ~little:false (dng ~little:false ());
    "v0-trailer", build ~trailer:"trailing bytes after the strip" (dng ~xmp_length:300 ());
    "v1-bigtiff-le", build ~big:true (dng ());
    "v1-bigtiff-be", build ~big:true ~little:false (dng ~little:false ());
    "v2-makernote", build (dng ~extra:[34665, Child [37500, bytes_ 7 "MakerNote-bytes"]] ());
    "v2-unknown-short", build (dng ~extra:[65002, short 7] ());
    "v2-undefined-xmp", build (List.map (fun (tag, v) -> if tag = 700 then xmp ~typ:7 100 else (tag, v)) (dng ()));
    "v2-private-data", build (dng ~extra:[50740, bytes_ 1 "private!"] ());
    "refused-no-xmp", build (dng ~with_xmp:false ());
    "refused-unknown-long", build (dng ~extra:[65001, long 7] ());
    "refused-strip-in-xmp", build (List.map (fun (tag, v) ->
       if tag = 273 then (tag, Long_at (Option.get probe.xmp_at)) else (tag, v)) (dng ()));
    "refused-cyclic-exif", build (dng ~extra:[34665, Long_at 8L] ()) ]

let hex = SemanticHash.hex
let json_string s =
  let b = Buffer.create (String.length s + 2) in
  Buffer.add_char b '"';
  String.iter (function '"' -> Buffer.add_string b "\\\"" | '\\' -> Buffer.add_string b "\\\\"
    | c when Char.code c < 32 -> Printf.bprintf b "\\u%04x" (Char.code c) | c -> Buffer.add_char b c) s;
  Buffer.add_char b '"'; Buffer.contents b

let () =
  let out = Sys.argv.(1) in
  let entries = List.map (fun (name, f) ->
    let path = Filename.concat out (name ^ ".dng") in
    let oc = open_out_bin path in output_string oc f.bytes; close_out oc;
    let fd = Unix.openfile path [Unix.O_RDONLY] 0 in
    let results = List.map (fun (pname, ext) ->
      SemanticFile.with_fd fd (fun file ->
        match SemanticDelta.inspect ~max_payload:FormatExtension.max_region
                ~span_semantics:FormatExtension.Known_metadata ext file with
        | Error why -> pname, Error why
        | Ok proof -> pname, Ok (SemanticDelta.describe proof))) profiles in
    Unix.close fd;
    let strictest = List.find_map (function p, Ok _ -> Some p | _, Error _ -> None) results in
    let one (p, r) = match r with
      | Error why -> Printf.sprintf "%s:{\"refused\":%s}" (json_string p) (json_string why)
      | Ok (d : SemanticDelta.description) ->
          Printf.sprintf "%s:{\"regions\":[%s],\"preserved_digest\":%s}" (json_string p)
            (String.concat "," (List.map (fun (r : FormatExtension.region) ->
               Printf.sprintf "[%Ld,%d]" r.offset r.length) d.regions))
            (json_string (hex d.preserved_digest)) in
    Printf.sprintf "  {\"file\":%s,\"size\":%d,\"sha256\":%s,\"strictest\":%s,\n   \"profiles\":{%s}}"
      (json_string (name ^ ".dng")) (String.length f.bytes) (json_string (hex (SemanticHash.string f.bytes)))
      (match strictest with Some p -> json_string p | None -> "null")
      (String.concat ",\n     " (List.map one results))) vectors in
  print_string ("{\"schema\":\"unison-sde0-preserved-golden/1\",\"vectors\":[\n" ^ String.concat ",\n" entries ^ "\n]}\n")
