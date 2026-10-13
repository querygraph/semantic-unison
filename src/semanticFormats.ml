(* Policy, registry mutation and feature negotiation belong to the owner.
   Workers receive only the selected immutable extension handle. *)
let known = ref []
let register ?capability ?max_payload ?suffixes ?observer extension =
  FormatExtension.register ?capability ?max_payload ?suffixes ?observer extension;
  let module E = (val extension : FormatExtension.S) in
  let handle = match FormatExtension.resolve E.profile with Some h -> h | None -> assert false in
  let capability = FormatExtension.capability handle in
  let feature = match List.find_opt (fun (h,_) -> FormatExtension.capability h = capability) !known with
    | Some (_,f) -> f
    | None -> Features.register capability ~arcFormatChange:false None in
  known := !known @ [handle,feature]

let () =
  register ~capability:"dng-xmp-v1" ~max_payload:FormatExtension.max_region
    ~suffixes:[".dng"] ~observer:DngExtended.observer (module DngExtended);
  register ~capability:"dng-xmp-v0" ~max_payload:FormatExtension.max_region
    ~suffixes:[".dng"] ~observer:DngSemantic.observer (module DngSemantic)

let validate_selected profiles =
  List.iter (fun profile ->
    if not (List.exists (fun (h,_) -> FormatExtension.profile h = profile) !known) then
      raise (Util.Fatal ("Unknown semantic profile: " ^ profile))) profiles

let dng_enabled = Prefs.createBool "semanticdng" false ~local:true
  ~send_value:(fun _ -> false)
  ~category:(`Advanced `General)
  "use experimental exact DNG metadata transfer"
  "Enable both built-in DNG XMP profile versions, preferring the extended \
   profile when negotiated. All transfers preserve exact bytes and full verification."

let outgoing_selected profiles =
  validate_selected profiles;
  (* Expand the shorthand on the client, where the final intersection of all
     roots' features is known. Send the shorthand as false to clear any stale
     server value, so a broader per-connection feature subset cannot expand it.
     Keep incoming bool decoding for the original clients' representation. *)
  let profiles = if Prefs.read dng_enabled then
      List.fold_right (fun profile profiles ->
        if List.mem profile profiles then profiles else profile :: profiles)
        [DngExtended.profile; DngSemantic.profile] profiles
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
       ((profile = DngExtended.profile || profile = DngSemantic.profile) &&
        Prefs.read dng_enabled)
    then Some handle else None) !known
let peer_enabled () =
  List.filter (fun handle -> List.exists (fun (h,f) ->
    FormatExtension.profile h = FormatExtension.profile handle && Features.enabled f) !known)
    (local_enabled ())
let resolve_peer profile = List.find_opt (fun h -> FormatExtension.profile h = profile) (peer_enabled ())
