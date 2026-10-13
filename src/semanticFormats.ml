(* Policy, registry mutation and feature negotiation belong to the owner.
   Workers receive only the selected immutable extension handle. *)
let known = ref []
let register ?capability ?max_payload ?suffixes extension =
  FormatExtension.register ?capability ?max_payload ?suffixes extension;
  let module E = (val extension : FormatExtension.S) in
  let handle = match FormatExtension.resolve E.profile with Some h -> h | None -> assert false in
  let capability = FormatExtension.capability handle in
  let feature = match List.find_opt (fun (h,_) -> FormatExtension.capability h = capability) !known with
    | Some (_,f) -> f
    | None -> Features.register capability ~arcFormatChange:false None in
  known := !known @ [handle,feature]

let () = register ~capability:"dng-xmp-v0" ~max_payload:FormatExtension.max_region
  ~suffixes:[".dng"] (module DngSemantic)

let dng_enabled = Prefs.createBool "semanticdng" false ~local:true
  ~category:(`Advanced `General)
  "use experimental exact DNG metadata transfer"
  "Enable the built-in DNG XMP profile. Equivalent to selecting its profile \
   with semanticprofile. All transfers preserve exact bytes and full verification."
let selected = Prefs.createStringList "semanticprofile" ~local:true
  ~category:(`Advanced `General)
  "enable a registered exact semantic profile (repeatable)"
  "Explicitly enable a trusted compiled semantic profile by its versioned ID. \
   Remote use additionally requires its separately negotiated capability. \
   No plugin code is received from the peer."
let local_enabled () =
  let profiles = Prefs.read selected in
  List.iter (fun profile ->
    if not (List.exists (fun (h,_) -> FormatExtension.profile h = profile) !known) then
      raise (Util.Fatal ("Unknown semantic profile: " ^ profile))) profiles;
  List.filter_map (fun (handle,_) ->
    let profile = FormatExtension.profile handle in
    if List.mem profile profiles || (profile = DngSemantic.profile && Prefs.read dng_enabled)
    then Some handle else None) !known
let peer_enabled () =
  List.filter (fun handle -> List.exists (fun (h,f) ->
    FormatExtension.profile h = FormatExtension.profile handle && Features.enabled f) !known)
    (local_enabled ())
let resolve_peer profile = List.find_opt (fun h -> FormatExtension.profile h = profile) (peer_enabled ())
