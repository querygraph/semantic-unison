let check value message = if not value then failwith message
let () =
  let mode=Sys.argv.(1) in
  let policy=if mode="off" then "off" else if mode="warn" then "warn" else "require" in
  let workspace=if mode="fits" then 4 else if mode="negative" then -1 else 64 in
  Prefs.loadStrings ["semanticdng = false";"semanticworkers = 1";
    "semanticpayloadbudget = 8";"semanticdescriptorbudget = 64";
    "semanticmaxinflight = 1";"validationtreememory = 0";
    "adobevalidate = " ^ policy;"adobevalidatorworkspace = " ^ string_of_int workspace];
  Features.setEnabled (Features.all ());
  if mode="require" || mode="warn" then begin
    for _=1 to 16 do
      (try ignore(SemanticRuntime.make_publication_reservation());
         failwith "oversized publication reservation accepted"
       with
       | Util.Transient message ->
           check(String.length message>0) "empty admission diagnostic"
       | SemanticAdmission.Failed _ ->
           failwith "DESIGNATED oversized publication reservation escaped as SemanticAdmission.Failed");
      let usage=SemanticRuntime.admission_usage() in
      check(usage.SemanticAdmission.transactions=0 && usage.payload_bytes=0 && usage.descriptors=0)
        "rejected publication reservation debited resources"
    done
  end else if mode="negative" then begin
    (try ignore(SemanticRuntime.make_publication_reservation());
       failwith "negative backend declaration accepted"
     with Util.Fatal _ -> ())
  end else begin
    check(mode="fits" || mode="off") "unknown fixed control";
    let reservation=SemanticRuntime.make_publication_reservation() in
    check(Lwt_unix.run(SemanticAdmission.acquire reservation (HelperSupervisor.cancellation())))
      "fitting reservation refused";
    let usage=SemanticRuntime.admission_usage() in
    let expected=(if mode="off" then 1 else 5)*1048576 in
    check(usage.SemanticAdmission.transactions=1 && usage.payload_bytes=expected && usage.descriptors=24)
      "fitting/off publication cost differs";
    SemanticAdmission.retire reservation;
    let usage=SemanticRuntime.admission_usage() in
    check(usage.transactions=0 && usage.payload_bytes=0 && usage.descriptors=0)
      "fitting reservation did not retire"
  end;
  Printf.printf "PASS publication admission %s\n%!" mode
