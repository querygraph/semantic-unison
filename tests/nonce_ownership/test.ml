module H = Harness
module N = NonceFunction
let check value reason = if not value then failwith reason
let caught f = try ignore (f ()); None with error -> Some error
let same actual expected = match actual with Some error -> error==expected | None -> false
let random_closed () =
  check (not !(H.owns_random) && !(H.close_calls)=1 && !(H.actual_closes)=1 &&
         H.fd_closed !(H.random_fd)) "random descriptor did not settle exactly once"
let sentinel_preserved () =
  check (not !(H.owns_random) && !(H.close_calls)=1 && !(H.actual_closes)=1)
    "nonce performed repeated native close on the reused number";
  H.verify_sentinel ()
let count = ref 0
let test ~work name mode f =
  let selected = if Array.length Sys.argv>2 then Sys.argv.(2) else "all" in
  if selected="all" || selected=name then begin
    H.reset ~work mode;
    match f () with
    | () -> H.print_observation name; H.cleanup (); H.verify_fixture_settled name; incr count;
        Printf.printf "PASS %s\n%!" name
    | exception error ->
        H.print_observation name;
        (try H.cleanup (); H.verify_fixture_settled name
         with cleanup -> Printf.eprintf "Secondary fixture cleanup error: %s\n%!" (Printexc.to_string cleanup));
        raise error
  end
let () =
  let work = Sys.argv.(1) in
  test ~work "success" H.Success (fun () ->
    let result = N.nonce () in
    check (String.length result=32 && !(H.actual_opens)=1 && !(H.actual_bytes)=32)
      "nonce success changed length or failed to read OS bytes";
    random_closed ());
  test ~work "constructor-oom-pre-open" H.Constructor_oom (fun () ->
    check (same (caught N.nonce) Out_of_memory && !(H.constructor_faults)=1) "constructor OOM was lost";
    check (!(H.actual_opens)=0 && !(H.open_attempts)=0 && not !(H.owns_random))
      "constructor OOM opened random fd");
  test ~work "native-open-error" H.Open_error (fun () ->
    check (same (caught N.nonce) H.open_marker && !(H.open_attempts)=1 && !(H.actual_opens)=0)
      "native open failure changed exception or created a descriptor");
  test ~work "post-open-read-dispatch-oom" H.Read_oom (fun () ->
    check (same (caught N.nonce) Out_of_memory && !(H.read_faults)=1 && !(H.actual_reads)=0)
      "post-open OOM changed primary exception";
    random_closed ());
  test ~work "read-error" H.Read_error (fun () ->
    check (same (caught N.nonce) H.read_marker && !(H.read_faults)=1) "read error identity changed";
    random_closed ());
  test ~work "eof" H.Eof (fun () ->
    let failed = match caught N.nonce with Some (H.Util.Transient _) -> true | _ -> false in
    check (failed && !(H.actual_reads)=0) "EOF was accepted"; random_closed ());
  test ~work "prefix-then-eof" H.Prefix_eof (fun () ->
    let failed = match caught N.nonce with Some (H.Util.Transient _) -> true | _ -> false in
    check (failed && !(H.actual_reads)=1 && !(H.actual_bytes)=8) "partial nonce EOF was accepted";
    random_closed ());
  test ~work "eintr-and-short-reads" H.Interrupted_short (fun () ->
    let result = N.nonce () in
    check (String.length result=32 && !(H.interrupted)=3 && !(H.actual_reads)=5 &&
           !(H.actual_bytes)=32 && !(H.read_calls)=8) "finite EINTR or short-read retry changed";
    random_closed ());
  test ~work "close-eio" H.Close_error (fun () ->
    check (same (caught N.nonce) H.close_marker && !(H.close_faults)=1)
      "close EIO changed primary exception";
    random_closed ());
  test ~work "read-error-before-close-eio" H.Read_and_close_error (fun () ->
    check (same (caught N.nonce) H.read_marker && !(H.read_faults)=1 && !(H.close_faults)=1)
      "close EIO replaced primary read error";
    random_closed ());
  test ~work "close-eio-reused-number" H.Close_error_reuse (fun () ->
    check (same (caught N.nonce) H.close_marker)
      "close EIO changed after descriptor reuse";
    sentinel_preserved ();
    check (!(H.close_faults)=1) "cleanup retried a consumed descriptor");
  test ~work "post-close-string-oom-reused-number" H.String_oom_reuse (fun () ->
    check (same (caught N.nonce) Out_of_memory && !(H.string_faults)=1)
      "post-close result allocation OOM was lost";
    sentinel_preserved ());
  test ~work "primary-read-error-close-eio-reused-number" H.Read_close_error_reuse (fun () ->
    check (same (caught N.nonce) H.read_marker && !(H.read_faults)=1 && !(H.close_faults)=1)
      "reused-number cleanup replaced primary read error";
    sentinel_preserved ());
  Printf.printf "Nonce ownership controls complete: %d\n%!" !count
