external count : unit -> int = "resource_fixture_fd_count"
let check b s=if not b then failwith s
let ()=
 let workers=int_of_string Sys.argv.(1) in
 let overflow=Array.length Sys.argv>2 && Sys.argv.(2)="overflow" in
 Prefs.loadStrings["semanticworkers = "^string_of_int workers;"semanticvolumejobs = 1";
  "semanticdng = true";"adobevalidate = off";"semanticpayloadbudget = 17";
  "semanticdescriptorbudget = "^(if overflow then string_of_int max_int else "32");"semanticmaxinflight = 2"];
 Features.setEnabled(Features.all());
 let initial=count() in
 if overflow then begin
  check((try ignore(SemanticRuntime.resource_accounting());false with Util.Fatal _->true)) "baseline overflow accepted";
  check(count()=initial) "overflow refusal opened descriptors";
  print_endline "PASS Runtime infrastructure overflow refused before acquisition"
 end else begin
  let declared=SemanticWorkers.fixed_resources in
  let planned=SemanticRuntime.resource_accounting() in
  check(planned.baseline=declared && declared.descriptors=2 && declared.payload_bytes=4096 && planned.total_reserved=declared)
    "DESIGNATED Runtime infrastructure not reserved before acquisition";
  check(count()=initial) "accounting preflight started the pool";
  check(planned.capacity.descriptors=34 && planned.capacity.payload_bytes=17*1048576+4096) "legacy workspace budget changed";
  let consumer=SemanticRuntime.make_publication_reservation() in
  check(Lwt_unix.run(SemanticAdmission.acquire consumer(HelperSupervisor.cancellation()))) "consumer refused";
  check(count()=initial) "publication reservation started pool";
  let release=Lwt.wait() in
  let source=SemanticRuntime.with_transaction ~role:SemanticAdmission.Source ~max_payload:FormatExtension.max_region(fun _->release) in
  let full=SemanticRuntime.resource_accounting() in
  check(full.workspace.descriptors=32 && full.total_reserved.descriptors=34) "source stole fixed baseline";
  let runtime=SemanticRuntime.get() in
  let opened=count() in
  check(opened-initial=declared.descriptors) "pool FD delta differs from declaration";
  check((SemanticRuntime.resource_accounting()).total_reserved.descriptors=34) "pool baseline charged twice";
  Lwt.wakeup release ();Lwt_unix.run source;SemanticAdmission.retire consumer;
  let usage=SemanticAdmission.usage runtime.admission in
  check(usage.transactions=0 && usage.pending=0 && usage.descriptors=0 && usage.payload_bytes=0) "workspace admission leaked";
  check((SemanticRuntime.resource_accounting()).total_reserved=declared) "workspace retirement freed infrastructure";
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
  check(count()=initial) "pool baseline did not settle";
  check((SemanticRuntime.resource_accounting()).total_reserved=declared) "lifetime planning allowance changed after shutdown";
  Printf.printf "PASS workers=%d before=%d pool=%d delta=%d workspaceFDcapacity=32 totalFDcapacity=34 closed=%d\n%!" workers initial opened(opened-initial)(count())
 end
