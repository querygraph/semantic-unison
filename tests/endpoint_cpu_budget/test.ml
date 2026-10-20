let check value message = if not value then failwith message
let () =
  let mode=Sys.argv.(1) in
  let workers,ceiling,expected,start_pool = match mode with
    | "explicit-uncapped" -> 1,0,1,true
    | "auto-uncapped" -> 0,0,HelperSupervisor.available_physical_cpus (),false
    | "auto-capped" -> 0,2,min 2 (HelperSupervisor.available_physical_cpus ()),true
    | "explicit-high" -> 8,2,2,true
    | "explicit-low" -> 1,8,1,true
    | "auto-one" -> 0,1,1,true
    | "negative-ceiling" -> 1,(-1),0,false
    | "negative-workers" -> (-1),1,0,false
    | "restart-up" -> 1,1,1,false
    | "restart-down" -> 8,2,2,false
    | "same-effective" -> 8,2,2,false
    | _ -> failwith "unknown fixed CPU control" in
  Prefs.loadStrings ["semanticdng = false";"semanticworkers = "^string_of_int workers;
    "semanticcpubudget = "^string_of_int ceiling;"semanticpayloadbudget = 8";
    "semanticdescriptorbudget = 64";"semanticmaxinflight = 2";"semanticvolumejobs = 1"];
  Features.setEnabled (Features.all ());
  if expected=0 then begin
    (try ignore(SemanticRuntime.helper_supervisor ());failwith "invalid CPU preference accepted"
     with Util.Fatal _ -> ())
  end else begin
    let supervisor,budget=SemanticRuntime.helper_supervisor () in
    check (budget=expected) "DESIGNATED effective CPU ceiling incorrect";
    check (HelperSupervisor.usage supervisor=(0,0)) "unused supervisor debited CPU";
    let cancellation=HelperSupervisor.cancellation () in
    let admitted=Lwt_unix.run(HelperSupervisor.with_cpu_permits supervisor ~weight:expected cancellation
      (fun () -> check(HelperSupervisor.usage supervisor=(expected,0))"wrong admitted CPU weight";
        Lwt.return true)) in
    check(admitted=Some true && HelperSupervisor.usage supervisor=(0,0))"CPU permit settlement differs";
    (try ignore(Lwt_unix.run(HelperSupervisor.with_cpu_permits supervisor ~weight:(expected+1)
       cancellation (fun () -> Lwt.return ())));
       failwith "helper weight beyond endpoint ceiling accepted"
     with Invalid_argument _ -> ());
    if start_pool then begin
      let runtime=SemanticRuntime.get () in
      check(runtime.supervisor==supervisor && runtime.cpu_budget=expected)"worker/helper owner diverged";
      check((SemanticWorkers.usage runtime.pool).workers=min expected (SemanticWorkers.recommended_workers ()))
        "pool worker count exceeds effective ceiling";
      Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
      check(HelperSupervisor.usage supervisor=(0,0))"shutdown retained CPU permits"
    end;
    if mode="restart-up" || mode="restart-down" then begin
      Prefs.loadStrings ["semanticworkers = 8";
        "semanticcpubudget = "^(if mode="restart-up" then "2" else "1")];
      (try ignore(SemanticRuntime.helper_supervisor ());failwith "live CPU resize accepted"
       with Util.Fatal _ -> ())
    end;
    if mode="same-effective" then begin
      Prefs.loadStrings ["semanticworkers = 2";"semanticcpubudget = 8"];
      let same,n=SemanticRuntime.helper_supervisor () in
      check(same==supervisor && n=expected)"same effective CPU budget created another owner"
    end
  end;
  Printf.printf "PASS endpoint CPU budget %s effective=%d pool=%b\n%!" mode expected start_pool
