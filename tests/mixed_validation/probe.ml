(* Private owner-loop integration harness. Native execution requires a separate
   admitted owner; the original control driver supplies only local fake tools. *)
open Lwt
module H = HelperSupervisor
module W = SemanticWorkers
module R = SemanticRuntime
module D = DngValidation
let check value reason = if not value then failwith reason
let identity s = Printf.sprintf "%d:%d:%Ld:%.17g:%.17g:%d:%d"
  s.Unix.LargeFile.st_dev s.st_ino s.st_size s.st_mtime s.st_ctime s.st_perm s.st_nlink
let status = function None->"none" | Some(Unix.WEXITED n)->"exit:"^string_of_int n
  | Some(Unix.WSIGNALED n)->"signal:"^string_of_int n
  | Some(Unix.WSTOPPED n)->"stopped:"^string_of_int n
let outcome = function H.Completed->"completed" | H.Cancelled->"cancelled"
  | H.Timed_out->"timed-out" | H.Output_limit->"output-limit" | H.Failed _->"failed"
let group = function None->"unobserved" | Some None->"unknown" | Some(Some n)->string_of_int n
let caught f = BorrowedWork.catch
  (fun () -> BorrowedWork.bind f (fun value -> return(Ok value)))
  (fun error -> return(Error error))
let main () =
  check(Array.length Sys.argv=8) "exact mixed-control argv required";
  let driver=Sys.argv.(1) and metadata=Sys.argv.(2) and candidate=Sys.argv.(3)
  and driver_hash=Sys.argv.(4) and build=Sys.argv.(5)
  and expected_hash=Sys.argv.(6) and expected_size=Int64.of_string Sys.argv.(7) in
  Unix.mkdir Util.unisonDir 0o700;
  let initial=Array.length(Sys.readdir "/dev/fd") in
  Prefs.loadStrings ["semanticworkers=6";"semanticvolumejobs=1";"externalhelperthreads=1";
    "externalhelpertimeout=10";"externalhelperoutput=1";"debug=external-process";"log=false"];
  let runtime=R.get () and cancellation=H.cancellation () in
  let inspect path =
    let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
    BorrowedWork.try_bind (fun () -> W.digest runtime.R.pool cancellation fd)
      (fun result -> Unix.close fd; match result with
       | Some result -> return {D.sha256=SemanticHash.hex result.W.digest;
           size=result.stats.Unix.LargeFile.st_size;identity=identity result.stats}
       | None->fail(Failure "mixed inspection cancelled"))
      (fun error -> Unix.close fd;fail error) in
  let expected=Lwt_unix.run(inspect candidate) in
  check(expected.D.sha256=expected_hash && expected.size=expected_size) "prepared candidate differs";
  let source_before=Unix.LargeFile.lstat candidate in
  let observed=ref None in
  let tool={D.executable=driver;executable_sha256=driver_hash;build_id=build;
    arguments=[||];environment=[|"PATH=/usr/bin:/bin";"LANG=C";"LC_ALL=C"|];cpu_weight=1;
    limits={H.timeout=10.;terminate_grace=0.2;stdout_bytes=16384;stderr_bytes=16384}} in
  let validation=caught(fun () -> D.validate_with_execution
    ~observe_group:(fun value -> observed:=Some value) ~execute:(fun run -> run())
    runtime.supervisor cancellation ~policy:D.Require ~tool:(Some tool) ~inspect ~candidate ~expected) in
  let metadata_result=caught(fun () -> SupervisedExternal.runExternalProgramArgs metadata
    [|metadata;"-config";"";"-j";"-s";"-XMP:Rating";"-XMP:Label";"-ExifToolVersion";"--";candidate|]) in
  let jobs=List.init 16(fun _ -> caught(fun () -> inspect candidate)) in
  let verdict=Lwt_unix.run validation and metadata_result=Lwt_unix.run metadata_result in
  let hashes=List.map Lwt_unix.run jobs in
  let hash_ok=List.for_all(function Ok value->value=expected | Error _->false) hashes in
  let sdk_ok,process=match verdict with
    | Ok(D.Passed receipt)->true,Some receipt.D.process
    | Ok(D.Warning(_,process)) | Ok(D.Rejected(_,process))->false,process
    | Ok D.Skipped | Error _->false,None in
  (match process with
   | None->print_endline "SDK_RESULT process=unresolved"
   | Some process ->
       let pid=match process.H.child_pid with None->"none" | Some n->string_of_int n in
       Printf.printf "SDK_RESULT pid=%s status=%s outcome=%s other-members=%s truncated=%b stdout-hex=%s stderr-hex=%s\n%!"
         pid (status process.status) (outcome process.outcome) (group !observed) process.output_truncated
         (SemanticHash.hex process.stdout) (SemanticHash.hex process.stderr));
  let metadata_ok=match metadata_result with
    | Ok(Unix.WEXITED 0,log)->
        Printf.printf "METADATA_RESULT stdout-hex=%s\n%!" (SemanticHash.hex log);true
    | _->false in
  let after=Lwt_unix.run(inspect candidate) in
  check(after=expected && identity(Unix.LargeFile.lstat candidate)=identity source_before)
    "mixed candidate changed";
  check(H.usage runtime.supervisor=(0,0)) "mixed CPU/child ledger not settled";
  let usage=W.usage runtime.pool in
  check(usage.W.pending=0 && usage.running=0 && usage.peak_running<=6) "mixed worker ledger not settled";
  ignore(Lwt_unix.run(W.shutdown runtime.pool));
  check(Array.length(Sys.readdir "/dev/fd")=initial) "mixed owner descriptor baseline differs";
  Printf.printf "MIXED_CLOSED owner=%d sdk-ok=%b metadata-ok=%b hashes-ok=%b hashes=16 cpu=0 children=0 pending=0 running=0 fd-baseline=true\n%!"
    (Unix.getpid()) sdk_ok metadata_ok hash_ok
let () = main ()
