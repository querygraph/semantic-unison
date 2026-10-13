(* Linked by test_local_clone.py with a private copy of Copy's implementation,
   exposing the bounded producer without adding a public testing API. Fixture
   helpers come from semantic/test.ml. All paths are disposable fixtures. *)
let () =
  let directory = Fspath.canonize (Some (Sys.getcwd ())) in
  let path s = Fspath.concat directory (Path.fromString s) in
  let basis = String.init 524288 (fun n -> Char.chr ((n * 197 + n / 251) land 255)) in
  let targets = [
    "same offset", String.sub basis 0 15000 ^ "CHANGED!" ^ String.sub basis 15008 (String.length basis - 15008);
    "shifted", "prefix" ^ basis;
    "shortened", String.sub basis 0 170000;
    "extended", basis ^ String.make 200000 'E';
    "all literal", String.make (String.length basis) 'X'] in
  List.iter (fun (label,target) ->
    write "basis" basis; write "source" target;
    require (CopyForTest.copyLocalCloned (path "source") (path "basis")
      directory (Path.fromString "output") (Uutil.Filesize.ofInt (String.length target)) None)
      "APFS clone staging unavailable";
    require (read "output" = target) ("local " ^ label ^ " exact bytes");
    require (read "basis" = basis) "local producer changed live basis";
    Sys.remove "output";
    print_endline ("local bounded producer: " ^ label)) targets;
  write "source" "short";
  (try ignore (CopyForTest.copyLocalCloned (path "source") (path "basis")
       directory (Path.fromString "output") (Uutil.Filesize.ofInt 100) None);
       failwith "short source accepted"
   with End_of_file -> ());
  require (not (Sys.file_exists "output")) "failed producer exposed candidate";
  require (read "basis" = basis) "failed producer changed basis";
  Prefs.loadStrings ["semanticdng = true"];
  List.iter (fun little ->
    let a = fixture ~little () and b = fixture ~little ~xmp:"<x>two</x>      " () in
    write "basis" a; write "source" b;
    require (SemanticSync.try_local ~source:(path "source") ~basis:(path "basis")
      ~directory ~staging:(Path.fromString "output")) "semantic clone declined fixture";
    require (read "output" = b && read "basis" = a) "semantic clone exactness";
    Sys.remove "output";
    write "source" (fixture ~little ~opaque:'Z' ());
    require (not (SemanticSync.try_local ~source:(path "source") ~basis:(path "basis")
      ~directory ~staging:(Path.fromString "output"))) "semantic opaque change accepted";
    require (not (Sys.file_exists "output")) "declined semantic clone exposed output") [true;false];
  require (Array.length (Sys.readdir ".") = 2) "temporary staging leaked";
  print_endline "local semantic clone: exact LE/BE XMP patches, opaque fallback, cleanup";
  Prefs.loadStrings ["semanticworkers = 8"];
  let runtime = SemanticRuntime.get () in
  let tail = String.make (32 * 1024 * 1024) 'Q' in
  let large_base = fixture () ^ tail
  and large_target = fixture ~xmp:"<x>two</x>      " () ^ tail in
  write "basis" large_base; write "source" large_target;
  let beats = ref 0 and finished = ref false in
  let rec heartbeat () =
    let open Lwt in
    if !finished then return () else Lwt_unix.sleep 0.001 >>= fun () ->
      incr beats; heartbeat () in
  Lwt.ignore_result (heartbeat ());
  require (Lwt_unix.run (SemanticSync.try_local_async ~source:(path "source")
    ~basis:(path "basis") ~directory ~staging:(Path.fromString "output")))
    "async semantic clone declined";
  finished := true;
  require (!beats > 0) "async semantic work blocked owner loop";
  require ((SemanticWorkers.usage runtime.pool).peak_running >= 2) "source/basis did not run concurrently";
  require (read "output" = large_target && read "basis" = large_base) "async exact output";
  Sys.remove "output";
  print_endline "async local semantic: concurrent proofs, owner heartbeat, exact materialization";
  let candidates = List.init 8 (fun i ->
    let name = "parallel-output-" ^ string_of_int i in
    name,SemanticSync.try_local_async ~source:(path "source") ~basis:(path "basis")
      ~directory ~staging:(Path.fromString name)) in
  let rec settle acc = function
    | [] -> Lwt.return (List.rev acc)
    | (name,job)::rest -> Lwt.try_bind (fun () -> job)
        (fun result -> settle ((name,Ok result)::acc) rest)
        (fun error -> settle ((name,Error error)::acc) rest) in
  List.iter (fun (name,result) ->
    (match result with Ok true -> () | Ok false -> failwith "parallel local fixture declined"
      | Error error -> raise error);
    require (read name = large_target) "parallel local output differs";
    Sys.remove name) (Lwt_unix.run (settle [] candidates));
  let admitted = SemanticAdmission.usage runtime.admission in
  require (admitted.peak_transactions >= 8 && admitted.peak_transactions <= 9)
    "global admission did not dispatch eight local candidates";
  require ((SemanticWorkers.usage runtime.pool).peak_running > 4)
    "production local dispatch retained old four-proof ceiling";
  require (admitted.transactions=0 && admitted.pending=0 && admitted.payload_bytes=0 && admitted.descriptors=0)
    "parallel local resources leaked";
  require (HelperSupervisor.usage runtime.supervisor = (0,0)) "parallel local CPU permits leaked";
  require (read "basis" = large_base) "parallel local path changed live basis";
  print_endline "async local semantic: eight candidates exceed old admission ceiling with exact output";
  Unix.mkdir "bad-source" 0o700;
  (try ignore (Lwt_unix.run (SemanticSync.try_local_async ~source:(path "bad-source")
       ~basis:(path "basis") ~directory ~staging:(Path.fromString "output")));
       failwith "directory source accepted"
   with Util.Transient _ -> ());
  Unix.rmdir "bad-source";
  require ((SemanticWorkers.usage runtime.pool).pending = 0) "failed sibling job still pending";
  require (not (Sys.file_exists "output")) "failed async transfer published output";
  let interrupted = SemanticSync.try_local_async ~source:(path "source")
    ~basis:(path "basis") ~directory ~staging:(Path.fromString "output") in
  Lwt.ignore_result (let open Lwt in Lwt_unix.sleep 0.001 >>= fun () ->
    Remote.clientCloseRootConnection (Common.Local,directory); return ());
  (try ignore (Lwt_unix.run interrupted); failwith "interrupted async transfer succeeded"
   with Util.Transient _ -> ());
  require (not (Sys.file_exists "output")) "interrupted async transfer published output";
  require ((SemanticWorkers.usage runtime.pool).pending = 0) "cancelled jobs still pending";
  require (HelperSupervisor.usage runtime.supervisor = (0,0)) "cancelled permit leaked";
  require (Array.length (Sys.readdir ".") = 2) "async staging leaked";
  require (read "basis" = large_base) "async failure changed live basis";
  Prefs.loadStrings ["semanticdng = false"; "semanticprofile = org.unison.test-fixed/0"];
  write "basis" "TOY0aaaaopaque"; write "source" "TOY0bbbbopaque";
  require (Lwt_unix.run (SemanticSync.try_local_async ~source:(path "source")
    ~basis:(path "basis") ~directory ~staging:(Path.fromString "output")))
    "registered second local profile declined";
  require (read "output" = "TOY0bbbbopaque" && read "basis" = "TOY0aaaaopaque")
    "registered second local profile changed opaque bytes";
  Sys.remove "output";
  Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
  print_endline "async local semantic: sibling failure and connection cancellation discard staging";
  print_endline "async local semantic: registered second format, no dispatcher changes"
