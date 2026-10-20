open Lwt
module V=DngValidation
module H=HelperSupervisor
let check yes why=if not yes then failwith why
let helper=Sys.argv.(1)
let candidate="/synthetic/policy-candidate.dng"
let expected={V.sha256=String.make 64 'a';size=23L;identity="original-policy-candidate"}
let tool_snapshot={expected with V.sha256=String.make 64 'c';identity="original-policy-helper"}
let inspect path=return(if path=helper then tool_snapshot else expected)
let modes=["valid";"missing";"warnings";"raw-mismatch";"raw-unsupported";
  "raw-not-checked";"structure-invalid";"structure-unsupported";"decode-failure";
  "decode-unsupported";"decode-not-checked";"error-zero";"wrong-hash";"wrong-size";
  "wrong-build";"malformed";"trailing";"truncated";"nonzero"]
let () =
 let count=ref 0 in
 List.iter(fun policy -> List.iter(fun mode ->
  let supervisor=H.create ~cpu_permits:2 ~max_children:1 ~max_pending:2 in
  let cancellation=H.cancellation() and groups=ref[] and executions=ref 0 in
  let tool={V.executable=helper;executable_sha256=tool_snapshot.sha256;
    build_id="original-policy-finding-1";arguments=[|mode|];environment=[||];
    cpu_weight=1;limits={H.timeout=5.;terminate_grace=0.1;stdout_bytes=4096;stderr_bytes=4096}} in
  let result=Lwt_unix.run(V.validate_with_execution
    ~observe_group:(fun x->groups:=x::!groups)
    ~execute:(fun run->incr executions;run()) supervisor cancellation
    ~policy ~tool:(Some tool) ~inspect ~candidate ~expected) in
  let passes=List.mem mode ["valid";"missing";"warnings"] in
  let process=match result with
   | V.Passed r when passes ->
      check((mode="missing")=(r.report.raw_digest=V.Missing)) "missing digest relabelled";
      check(r.report.warnings=(if mode="warnings" then 3 else 0)) "warning count lost";
      r.process
   | V.Warning(_,Some child) when not passes && policy=V.Warn -> child
   | V.Rejected(_,Some child) when not passes && policy=V.Require -> child
   | _ -> failwith("incorrect finding policy: "^mode) in
  check(!executions=1 && !groups=[Some 0]) "execution/group-before-reap proof missing";
  check(process.status=Some(Unix.WEXITED(if mode="nonzero" then 4 else 0))) "helper exit changed";
  check(process.outcome=H.Completed && not process.output_truncated) "unexpected supervisor failure";
  (match process.child_pid with None->failwith "helper identity missing"
   | Some pid->check(try ignore(Unix.waitpid [Unix.WNOHANG] pid);false
                    with Unix.Unix_error(Unix.ECHILD,_,_)->true) "helper not actually reaped");
  check(H.usage supervisor=(0,0)) "helper accounting retained";
  incr count;Printf.printf "PASS policy=%s mode=%s finding=%s helper-reaped=true group-before-reap=0\n%!"
    (if policy=V.Require then "require" else "warn") mode
    (if passes then "passed" else if policy=V.Warn then "warning" else "rejected")
 )modes)[V.Require;V.Warn];
 let supervisor=H.create ~cpu_permits:2 ~max_children:1 ~max_pending:2 in
 let forbidden _=failwith "off performed work" in
 check(Lwt_unix.run(V.validate_with_execution ~execute:forbidden supervisor(H.cancellation())
   ~policy:V.Off ~tool:None ~inspect:forbidden ~candidate ~expected)=V.Skipped) "off not skipped";
 check(H.usage supervisor=(0,0)) "off accounting changed";
 Printf.printf "PASS off no-inspection no-execution; %d finding/policy cases\n%!" !count
