(* DNG XMP inspectors over phidentify-tiff's bounded TIFF/DNG walker. This is
   not a DNG validator or raw-image fingerprint. All bytes outside the returned
   extent are independently covered by the semantic transfer core's
   preservation proof. The grammars live in Phidentify_tiff; this module binds
   them to the negotiated profile names and to SemanticFile. *)
let profile = "org.firstpair.dng-xmp/0"
let opaque_maker_profile = "org.firstpair.dng-xmp/2"

type component_role = Phidentify_tiff.component_role =
  Image_bytes | Standard_value | Private_value | Structure
type component_region = Phidentify_tiff.component_region = {
  logical_id : string; schema : string; role : component_role;
  offset : int64; length : int64 }

let max_xmp = FormatExtension.max_region

(* SemanticFile.Invalid from a read or the final stability check is an
   ordinary refusal, as it was when the walk lived here. *)
let guarded f file =
  try
    f { Phidentify_tiff.size = SemanticFile.size file;
        read = SemanticFile.read file;
        check = (fun () -> SemanticFile.check file) }
  with SemanticFile.Invalid s -> Error s

let manifest policy =
  guarded (fun reader ->
    match Phidentify_tiff.walk (policy ~max_xmp) reader with
    | Error reason -> Error reason
    | Ok packet ->
        let regions = match packet with
          | None -> []
          | Some {Phidentify_tiff.offset; length} -> [{FormatExtension.offset; length}] in
        Ok {FormatExtension.regions})

let inspect file = manifest Phidentify_tiff.v0 file
let inspect_extended file = manifest Phidentify_tiff.v1 file
let inspect_opaque_maker file = manifest Phidentify_tiff.merge_only file

(* Geometry-only exact transfer: private contents remain part of complete and
   complement hashes. This grants no pointer-independence or merge authority. *)
let inspect_layout file = manifest Phidentify_tiff.layout file

let admit_fields = Phidentify_tiff.admit_fields
let parse_admission = Phidentify_tiff.parse_admission

(* A read failure ends the survey like any other stop; fields noted before it
   are kept. *)
let unknown_fields file =
  let found = ref [] in
  let note directory tag typ n = found := (directory, tag, typ, n) :: !found in
  let stop = match guarded (Phidentify_tiff.walk ~unknown:note
                              (Phidentify_tiff.merge_only ~max_xmp)) file with
    | Ok _ -> None | Error reason -> Some reason in
  List.rev !found, stop

let component_regions file = guarded (Phidentify_tiff.component_regions ~max_xmp) file

let observer : FormatExtension.observer = {
  schema = "dng-xmp-property-encoding-v0";
  observe = (function
    | [packet] ->
        (match XmpObservation.observe packet with
         | Error why -> Error why
         | Ok observation ->
             Ok (List.map (fun (property:XmpObservation.property) ->
               let category = match property.category with
                 | XmpObservation.Descriptive -> FormatExtension.Descriptive
                 | XmpObservation.Rendering -> FormatExtension.Rendering
                 | XmpObservation.Identity -> FormatExtension.Identity
                 | XmpObservation.Workflow -> FormatExtension.Workflow
                 | XmpObservation.Opaque -> FormatExtension.Opaque in
               {FormatExtension.name=property.name;category;digest=property.digest}) observation.properties))
    | _ -> Error "DNG observation requires exactly one XMP packet")
}
