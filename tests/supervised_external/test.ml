open Lwt
module S = SupervisedExternal
module H = HelperSupervisor
module R = SemanticRuntime
module W = SemanticWorkers
let checks = ref 0
let check condition message = incr checks; if not condition then failwith message
let has text part = Util.findsubstring part text <> None
let write path data = let out=open_out_bin path in output_string out data;close_out out
let read path = let c=open_in_bin path in
  Fun.protect ~finally:(fun()->close_in c) (fun()->really_input_string c (in_channel_length c))
let case=Sys.argv.(1) and helper=Sys.argv.(2)
let pid=Filename.concat (Sys.getcwd ()) "helper.pid"
let call mode args = S.runExternalProgramArgs helper
  (Array.of_list ("custom invocation name" :: mode :: pid :: args))
let wait_for_file path =
  let rec wait n =
    if Sys.file_exists path then return ()
    else if n=0 then fail (Failure "helper did not start")
    else Lwt_unix.sleep 0.001 >>= fun () -> wait (n-1) in wait 5000
let expect_failure start =
  try ignore (Lwt_unix.run (start ())); failwith "expected helper failure"
  with Util.Transient _ | Util.Fatal _ | Invalid_argument _ -> ()
let main () =
  Unix.mkdir Util.unisonDir 0o700;
  Prefs.loadStrings ["semanticworkers=2";"semanticvolumejobs=1";"externalhelperthreads=1";
    "externalhelpertimeout=10";"externalhelperoutput=1";"log=false"];
  let first,budget=R.helper_supervisor () in
  check (budget=2 && H.usage first=(0,0)) "helper-only CPU owner invalid";
  let runtime=R.get () in
  check (first==runtime.R.supervisor) "worker runtime created a second helper CPU budget";
  Fun.protect ~finally:(fun () -> Abort.reset (); ignore (Lwt_unix.run (W.shutdown runtime.R.pool))) (fun () ->
    begin match case with
    | "observed" ->
        Prefs.loadStrings ["debug=external-process"];
        let status,_=Lwt_unix.run(call "echo" ["private argument not logged"]) in
        check(status=Unix.WEXITED 0) "observed helper changed exit policy"
    | "exiftool-readonly" ->
        Prefs.loadStrings ["debug=external-process"];
        let path=Filename.concat(Sys.getcwd()) "private.xmp" in
        let packet="<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\"><rdf:Description rdf:about=\"\" xmp:Rating=\"3\" xmp:Label=\"Blue\"/></rdf:RDF>" in
        write path packet;
        let stamp ()=let s=Unix.LargeFile.lstat path in
          s.Unix.LargeFile.st_dev,s.st_ino,s.st_kind,s.st_size,s.st_mtime,s.st_ctime,s.st_perm,s.st_nlink in
        let before=stamp() in
        let args=[|helper;"-config";"";"-j";"-s";"-XMP:Rating";"-XMP:Label";"-ExifToolVersion";"--";path|] in
        let running=S.runExternalProgramArgs helper args in
        let file=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
        Fun.protect ~finally:(fun () -> Unix.close file) (fun () ->
          let jobs=List.init 16(fun _ -> W.digest runtime.pool (H.cancellation()) file) in
          let expected=SemanticHash.string packet in
          List.iter(fun job -> match Lwt_unix.run job with
            | Some value -> check(value.W.digest=expected) "ExifTool mixed hash differs"
            | None -> failwith "ExifTool mixed hash cancelled") jobs;
          let status,log=Lwt_unix.run running in
          check(status=Unix.WEXITED 0) "ExifTool readonly request failed";
          check(has log "\"Rating\": 3" && has log "\"Label\": \"Blue\"" && has log "\"ExifToolVersion\":")
            "ExifTool returned unexpected metadata";
          check(stamp()=before && read path=packet) "ExifTool changed private source";
          check((W.usage runtime.pool).peak_running<=2) "ExifTool mixed worker budget exceeded";
          Printf.printf "EXIFTOOL_REPORT %s\n%!" log)
    | "argv" ->
        let status,log=Lwt_unix.run (call "echo" ["a b";"quote'\"$(`literal`)";"雪";"-option"]) in
        check (status=Unix.WEXITED 0) "argv helper status";
        check (has log "argv0=\"custom invocation name\"") "argv0 changed";
        check (has log "env=\"inherited value\"") "environment changed";
        List.iter (fun arg->check (has log (Printf.sprintf "arg=%S" arg)) "argument boundary changed")
          ["a b";"quote'\"$(`literal`)";"雪";"-option"]
    | "shell" ->
        let status,log=Lwt_unix.run (S.runExternalProgram "printf 'stdout literal\\n';\nprintf 'stderr literal\\n' >&2; exit 7") in
        check (status=Unix.WEXITED 7) "ordinary nonzero exit not returned";
        check (has log "stdout literal\n\nError Output:stderr literal") "legacy stream formatting changed"
    | "empty-argv" -> expect_failure (fun () -> S.runExternalProgramArgs helper [||]); check (not (Sys.file_exists pid)) "empty argv spawned"
    | "nul-argv0" -> expect_failure (fun () -> S.runExternalProgramArgs helper [|"bad\000name";"echo";pid|]); check (not (Sys.file_exists pid)) "NUL argv0 spawned"
    | "nul-argument" -> expect_failure (fun () -> call "echo" ["x\000y"]); check (not (Sys.file_exists pid)) "NUL argument spawned"
    | "missing" -> expect_failure (fun () -> S.runExternalProgramArgs "unison-no-such-helper-7d102e" [|"missing"|]); check (not (Sys.file_exists pid)) "missing helper spawned"
    | "weight" ->
        Prefs.loadStrings ["externalhelperthreads=3"];
        expect_failure (fun () -> call "echo" []);check (not (Sys.file_exists pid)) "oversized weight spawned"
    | "timeout" ->
        Prefs.loadStrings ["externalhelpertimeout=1"];
        expect_failure (fun () -> call "hang" [])
    | "stdout-limit" -> expect_failure (fun () -> call "stdout-flood" [])
    | "stderr-limit" -> expect_failure (fun () -> call "stderr-flood" [])
    | "signal" -> expect_failure (fun () -> call "signal" [])
    | "active-cancel" ->
        let running=call "hang" [] in
        Lwt.ignore_result (wait_for_file pid >>= fun () -> Abort.all ();return ());
        expect_failure (fun () -> running)
    | "queued-cancel" ->
        let release=Lwt.wait () in
        let held=H.with_cpu_permits runtime.R.supervisor ~weight:2 (H.cancellation ()) (fun ()->release) in
        let running=call "echo" [] in
        Lwt_unix.run (Lwt_unix.sleep 0.03);
        check (H.usage runtime.supervisor=(2,0)) "queued child consumed a slot";
        Abort.all (); expect_failure (fun () -> running);
        check (not (Sys.file_exists pid)) "cancelled queued helper spawned";
        Lwt.wakeup release ();ignore (Lwt_unix.run held)
    | "mixed" ->
        Prefs.loadStrings ["externalhelperthreads=2";"externalhelpertimeout=10"];
        let release=Filename.concat (Sys.getcwd ()) "release" in
        let data=Filename.concat (Sys.getcwd ()) "source" in write data "independent mixed hash bytes";
        let running=call "hold" [release] in Lwt_unix.run (wait_for_file pid);
        check (H.usage runtime.supervisor=(2,1)) "helper did not reserve declared CPU weight";
        let fd=Unix.openfile data [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
        Fun.protect ~finally:(fun ()->Unix.close fd) (fun () ->
          let hashing=W.digest runtime.pool (H.cancellation ()) fd in
          Lwt_unix.run (Lwt_unix.sleep 0.03);
          check (Lwt.poll hashing=None) "worker bypassed active helper CPU weight";
          check ((W.usage runtime.pool).W.running=0) "worker executed without CPU admission";
          write release "release";
          let status,_=Lwt_unix.run running in check (status=Unix.WEXITED 0) "held helper failed";
          let hashed=Lwt_unix.run hashing in
          check (match hashed with Some h->h.W.digest=SemanticHash.string (read data)|None->false) "mixed worker hash differs")
    | _ -> failwith "unknown case"
    end;
    if Sys.file_exists pid then begin
      let child=int_of_string (read pid) in
      check (try ignore (Unix.waitpid [Unix.WNOHANG] child);false
        with Unix.Unix_error (Unix.ECHILD,_,_)->true) "external child not independently reaped"
    end;
    check (H.usage runtime.supervisor=(0,0)) "helper CPU/child ledger leaked";
    let w=W.usage runtime.pool in check (w.W.pending=0 && w.running=0) "worker ledger leaked";
    Printf.printf "PASS %s checks=%d\n%!" case !checks)
let () = main ()
