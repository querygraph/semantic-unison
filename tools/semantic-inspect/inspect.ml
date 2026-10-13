(* Read-only developer inspection: no roots, archives, clones or output files. *)
let quote s =
  let b = Buffer.create (String.length s + 2) in
  Buffer.add_char b '"';
  String.iter (fun c -> match c with
    | '"' -> Buffer.add_string b "\\\""
    | '\\' -> Buffer.add_string b "\\\\"
    | c when Char.code c < 32 ->
        Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char b c) s;
  Buffer.add_char b '"'; Buffer.contents b
let object_ fields = "{" ^ String.concat "," (List.map (fun (k,v) -> quote k ^ ":" ^ v) fields) ^ "}"
let array xs = "[" ^ String.concat "," xs ^ "]"
let category = function
  | FormatExtension.Descriptive -> "descriptive" | Rendering -> "rendering"
  | Identity -> "identity" | Workflow -> "workflow" | Opaque -> "opaque"
let meanings extension proof = match SemanticDelta.observe ~extension proof with
  | None -> []
  | Some (Error why) -> ["interpretation_unavailable",quote why]
  | Some (Ok value) -> ["interpretation_schema",quote value.FormatExtension.schema;
      "properties",array (List.map (fun (p:FormatExtension.property) -> object_
        ["name",quote p.name;"category",quote (category p.category);
         "encoding_context_sha256",quote (SemanticHash.hex p.digest)]) value.properties)]
let report extension path = function
  | Error reason -> object_ ["path",quote path; "status",quote "unsupported";
                             "reason",quote reason]
  | Ok proof ->
    let d = SemanticDelta.describe proof in
    object_ (["path",quote path; "status",quote "supported";
      "profile",quote d.profile; "size",Int64.to_string d.size;
      "sha256",quote (SemanticHash.hex d.digest);
      "preserved_sha256",quote (SemanticHash.hex d.preserved_digest);
      "editable_regions",array (List.map (fun (r:FormatExtension.region) ->
        object_ ["offset",Int64.to_string r.offset; "length",string_of_int r.length]) d.regions)] @ meanings extension proof)
let inspect extension path =
  let fd = Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    SemanticFile.with_fd fd (SemanticDelta.inspect extension))
let compare base target = match base,target with
  | Error reason,_ -> ["classification",quote "unavailable"; "fallback_reason",quote ("basis: " ^ reason)]
  | _,Error reason -> ["classification",quote "unavailable"; "fallback_reason",quote ("target: " ^ reason)]
  | Ok base,Ok target ->
    let classification = match SemanticDelta.classify ~base ~target with
      | FormatExtension.Exact_bytes -> "exact_bytes"
      | FormatExtension.Editable_metadata -> "editable_metadata"
      | FormatExtension.Other_bytes -> "other_bytes" in
    let fields = ["classification",quote classification] in
    (* This nonce is only for measuring the encoded plan. No envelope is emitted
       or transmitted; a real transaction must obtain a fresh random nonce. *)
    match SemanticDelta.plan ~nonce:(String.make 32 '\000') ~base ~target with
    | Error reason -> fields @ ["patch_eligible","false"; "fallback_reason",quote reason]
    | Ok plan -> fields @ ["patch_eligible","true";
        "metadata_payload_bytes",string_of_int (SemanticDelta.payload_size plan);
        "envelope_bytes",string_of_int (String.length (SemanticDelta.encode plan));
        "request_bytes",string_of_int (String.length (SemanticDelta.encode_request
          ~nonce:(String.make 32 '\000') base))]
let main () =
  FormatExtension.register ~observer:DngSemantic.observer (module DngSemantic);
  let selected = ref DngSemantic.profile and base = ref None and target = ref None in
  Arg.parse ["--profile",Arg.Set_string selected,"ID Compiled format profile";
             "--base",Arg.String (fun p -> base := Some p),"FILE Compare against a basis"]
    (fun p -> match !target with None -> target := Some p
      | Some _ -> raise (Arg.Bad "exactly one target file is required"))
    "semantic-inspect [--profile ID] [--base FILE] TARGET";
  let path = match !target with Some p -> p | None -> failwith "a target file is required" in
  let handle = match FormatExtension.resolve !selected with Some e -> e
    | None -> failwith ("unknown compiled profile: " ^ !selected) in
  let extension = FormatExtension.implementation handle in
  let target = inspect extension path in
  let fields = ["schema",quote "unison-semantic-inspect/1"; "target",report handle path target] in
  let fields = match !base with None -> fields | Some path ->
    let base = inspect extension path in
    fields @ ["basis",report handle path base] @ compare base target in
  print_endline (object_ (fields @ ["verification",quote
    "Supported inputs were fully read and SHA-256 hashed. This is a read-only observation, not a commit authorization or Adobe validation."]))
let () = try main () with error ->
  prerr_endline (object_ ["error",quote (Printexc.to_string error)]); exit 2
