(* Policy, registry mutation and feature negotiation belong to the owner.
   Workers receive only the selected immutable extension handle. *)
let known = ref []
let register ?capability ?max_payload ?suffixes ?observer ?span_semantics extension =
  FormatExtension.register ?capability ?max_payload ?suffixes ?observer ?span_semantics extension;
  let module E = (val extension : FormatExtension.S) in
  let handle = match FormatExtension.resolve E.profile with Some h -> h | None -> assert false in
  let capability = FormatExtension.capability handle in
  let feature = match List.find_opt (fun (h,_) -> FormatExtension.capability h = capability) !known with
    | Some (_,f) -> f
    | None -> Features.register capability ~arcFormatChange:false None in
  known := !known @ [handle,feature]

let () =
  register ~span_semantics:FormatExtension.Known_metadata ~capability:"dng-xmp-v1" ~max_payload:FormatExtension.max_region
    ~suffixes:[".dng"] ~observer:DngExtended.observer (module DngExtended);
  register ~span_semantics:FormatExtension.Known_metadata ~capability:"dng-xmp-v0" ~max_payload:FormatExtension.max_region
    ~suffixes:[".dng"] ~observer:DngSemantic.observer (module DngSemantic);
  register ~span_semantics:FormatExtension.Known_metadata ~capability:"jpeg-xmp-v0" ~max_payload:65504
    ~suffixes:[".jpg";".jpeg"] (module JpegSemantic);
  register ~span_semantics:FormatExtension.Opaque_spans ~capability:"dng-layout-exact-v0"
    ~max_payload:FormatExtension.max_region ~suffixes:[".dng"] (module DngLayout);
  (* Reconciliation-only: resolvable by the merge owner, but outside [known],
     so it is neither selectable nor offered as a peer feature. *)
  let module OpaqueMaker = struct
    let profile = DngSemantic.opaque_maker_profile
    let inspect = DngSemantic.inspect_opaque_maker
  end in
  FormatExtension.register ~span_semantics:FormatExtension.Known_metadata ~capability:"dng-xmp-merge-v2"
    ~max_payload:FormatExtension.max_region ~suffixes:[".dng"] ~observer:DngSemantic.observer (module OpaqueMaker)

let validate_selected profiles =
  List.iter (fun profile ->
    if not (List.exists (fun (h,_) -> FormatExtension.profile h = profile) !known) then
      raise (Util.Fatal ("Unknown semantic profile: " ^ profile))) profiles

let dng_enabled = Prefs.createBool "semanticdng" false ~local:true
  ~send_value:(fun _ -> false)
  ~category:(`Advanced `General)
  "use experimental exact DNG metadata transfer"
  "Enable the built-in DNG profiles, preferring strict XMP interpretation \
   before the layout-only exact-byte fallback when negotiated. All transfers preserve exact bytes and full verification."

(* Permissive merge admissions. Sent only when set, so peers built without the
   preference are unaffected; both hosts then inspect with the same list. *)
let dng_merge_admit_set = ref (fun () -> false)
let dng_merge_admit = Prefs.createStringList "dngmergeadmit"
  ~category:(`Advanced `General)
  ~send:(fun () -> !dng_merge_admit_set ())
  "admit a DNG field in the built-in merge (Image|Exif|GPS|Interop:TAG:TYPE, repeatable)"
  "Admit one more TIFF field, named by directory, tag number and type number, \
   as a protected value in the built-in DNG merge. The field's bytes are kept \
   identical and may not overlap the XMP packet, but its contents are not \
   interpreted: only admit fields known not to point into the file. \
   unison-dngscan -tags lists candidates. The merge base is captured with \
   the same admissions, so a newly admitted field takes effect for files \
   whose base is captured after the change."
let () = dng_merge_admit_set := (fun () -> Prefs.read dng_merge_admit <> [])

(* Owner thread only: publish the current admissions before inspecting. *)
let apply_dng_merge_admissions () =
  DngSemantic.admit_fields (List.map (fun spec ->
    match DngSemantic.parse_admission spec with
    | Ok field -> field
    | Error reason -> raise (Util.Fatal ("dngmergeadmit: " ^ reason)))
    (Prefs.read dng_merge_admit))

let outgoing_selected profiles =
  validate_selected profiles;
  (* Expand the shorthand on the client, where the final intersection of all
     roots' features is known. Send the shorthand as false to clear any stale
     server value, so a broader per-connection feature subset cannot expand it.
     Keep incoming bool decoding for the original clients' representation. *)
  let profiles = if Prefs.read dng_enabled then
      List.fold_right (fun profile profiles ->
        if List.mem profile profiles then profiles else profile :: profiles)
        [DngExtended.profile; DngSemantic.profile; DngLayout.profile] profiles
    else profiles in
  List.filter (fun profile -> List.exists (fun (h,feature) ->
    FormatExtension.profile h = profile && Features.enabled feature) !known)
    profiles

(* The outgoing transform adds no framing to the existing string-list wire
   representation. Validate local IDs before omitting capabilities unavailable
   on this connection; preserve local selection for subsequent connections. *)
let selected = Prefs.createStringList "semanticprofile" ~local:true
  ~send_value:outgoing_selected
  ~category:(`Advanced `General)
  "enable a registered exact semantic profile (repeatable)"
  "Explicitly enable a trusted compiled semantic profile by its versioned ID. \
   Remote use additionally requires its separately negotiated capability. \
   No plugin code is received from the peer."
let local_enabled () =
  let profiles = Prefs.read selected in
  validate_selected profiles;
  List.filter_map (fun (handle,_) ->
    let profile = FormatExtension.profile handle in
    if List.mem profile profiles ||
       ((profile = DngExtended.profile || profile = DngSemantic.profile || profile = DngLayout.profile) &&
        Prefs.read dng_enabled)
    then Some handle else None) !known
let peer_enabled () =
  List.filter (fun handle -> List.exists (fun (h,f) ->
    FormatExtension.profile h = FormatExtension.profile handle && Features.enabled f) !known)
    (local_enabled ())
let resolve_peer profile = List.find_opt (fun h -> FormatExtension.profile h = profile) (peer_enabled ())
