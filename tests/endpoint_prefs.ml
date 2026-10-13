(* Exercise the preference wire boundary, including aliases and invalid bodies. *)
let category = `Internal `Devel
let endpoint = Prefs.createString "endpoint-host" "default-host" ~category "" ""
let () = Prefs.alias endpoint "endpoint-alias-before"
let endpoint = Prefs.makeEndpointLocal endpoint
let () = Prefs.alias endpoint "endpoint-alias-after"
let global = Prefs.createString "globalpolicy" "off" ~local:true ~category "" ""

let wire entries =
  let codec = Umarshal.(list (prod3 string bool string id id)) in
  Umarshal.from_string Prefs.mdumpedPrefs (Umarshal.to_string codec entries) 0

let body value =
  Umarshal.to_string Umarshal.(prod2 string (list string) id id) (value, [])

let write name text =
  let file = open_out (Prefs.profilePathname ~add_ext:false name) in
  output_string file text; close_out file

let () =
  Unix.mkdir Util.unisonDir 0o700;
  Prefs.loadStrings ["endpoint-alias-before = host-profile"];
  let dumped = Prefs.dump 1 in
  let raw = Umarshal.from_string
    Umarshal.(list (prod3 string bool string id id))
    (Umarshal.to_string Prefs.mdumpedPrefs dumped) 0 in
  assert (not (List.exists (fun (name, _, _) ->
    List.mem name (Prefs.name endpoint)) raw));
  assert (List.exists (fun (name, _, _) -> name = "globalpolicy") raw);
  Prefs.load (wire ["endpoint-host", false, body "peer-command";
                    "endpoint-alias-before", false, body "peer-before";
                    "endpoint-alias-after", false, body "peer-after";
                    "globalpolicy", false, body "require"]) 1;
  assert (Prefs.read endpoint = "host-profile");
  assert (Prefs.read global = "require");
  (* Neither an unsupported RPC version nor malformed payload may be decoded
     for an endpoint-local setting, under its canonical name or an alias. *)
  Prefs.load (wire ["endpoint-host", false, "bad encoding";
                    "endpoint-alias-before", false, "bad encoding";
                    "endpoint-alias-after", false, "bad encoding"]) 999;
  assert (Prefs.read endpoint = "host-profile");
  let rejected = try
    Prefs.load (wire ["unknown-required-pref", false, "bad encoding"]) 1;
    false
  with Util.Fatal _ -> true in
  assert rejected;
  Prefs.resetToDefaults ();
  write "endpoint.prf" "endpoint-alias-before = endpoint-file\n";
  Prefs.loadEndpointLocal "Endpoint preference test";
  assert (Prefs.read endpoint = "cli-host");
  assert (Prefs.read global = "off");
  Prefs.loadStrings ["endpoint-host = ordinary-profile"];
  assert (Prefs.read endpoint = "ordinary-profile");
  Prefs.parseCmdLine "Endpoint preference test";
  assert (Prefs.read endpoint = "cli-host");
  assert (Prefs.read global = "cli-policy");
  Prefs.set endpoint "untouched-host";
  write "endpoint.prf"
    "endpoint-host = partial-update\ninclude invalid-endpoint\n";
  write "invalid-endpoint.prf" "globalpolicy = require\n";
  let rejected = try Prefs.loadEndpointLocal "Endpoint preference test"; false
    with Util.Fatal _ -> true in
  assert rejected;
  assert (Prefs.read endpoint = "untouched-host");
  Unix.unlink (Prefs.profilePathname ~add_ext:false "endpoint.prf");
  Prefs.resetToDefaults ();
  Prefs.loadEndpointLocal "Endpoint preference test";
  assert (Prefs.read endpoint = "cli-host");
  assert (Prefs.read global = "off");
  print_endline "Endpoint preferences: outgoing omission; alias/incoming protection; local file/CLI precedence; included policy rejection; missing-file defaults."
