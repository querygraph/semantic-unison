open Lwt
let category = `Advanced `General
let descriptors = Prefs.makeEndpointLocal (Prefs.createInt "helperdescriptors" 0
  ~local:true ~category "hard descriptor limit per supervised helper (zero disables)"
  "Limit each copy/merge/diff/validation process and inherited descendants. \
   Includes stdin/stdout/stderr; positive values must be at least three. \
   Requires the pinned native helper limiter. This is not a group/global FD cap.")
let address = Prefs.makeEndpointLocal (Prefs.createInt "helperaddressspace" 0
  ~local:true ~category "hard helper address-space MiB limit (zero disables)"
  "Requires OS support; unsupported limit installation fails before target \
   execution. Address-space enforcement is unqualified on macOS and is not an \
   RSS limit. Configure only against independently qualified platform evidence.")
let launcher = Prefs.makeEndpointLocal (Prefs.createString "helperlimiter" ""
  ~local:true ~category "absolute native helper resource launcher path"
  "Build tools/helper-limits/launcher.c and configure its absolute local path. \
   The separate launcher lowers limits before exec without changing Unison.")
let hash = Prefs.makeEndpointLocal (Prefs.createString "helperlimiterhash" ""
  ~local:true ~category "SHA-256 pin for the helper limiter"
  "Lowercase exact SHA-256 of the qualified native helper limiter executable.")
type config = { process : HelperSupervisor.process_limits; hash : string }
let valid_hash text = String.length text = 64 &&
  String.for_all (function '0'..'9'|'a'..'f' -> true | _ -> false) text
let selected () =
  let fds = Prefs.read descriptors and mib = Prefs.read address in
  if fds = 0 && mib = 0 then None else begin
    if Sys.win32 then raise (Util.Fatal "Supervised helper resource limits require the POSIX backend");
    if fds < 0 || (fds > 0 && fds < 3) || mib < 0 ||
       Int64.of_int mib > Int64.div Int64.max_int 1048576L then
      raise (Util.Fatal "Invalid helperdescriptors/helperaddressspace limits");
    let path = Prefs.read launcher and hash = Prefs.read hash in
    if path = "" || Filename.is_relative path || String.contains path '\000' || not (valid_hash hash) then
      raise (Util.Fatal "Requested helper limits require absolute helperlimiter and lowercase SHA-256 helperlimiterhash");
    Some {process={HelperSupervisor.launcher=path;descriptors=fds;
      address_space_bytes=Int64.mul (Int64.of_int mib) 1048576L};hash}
  end
let with_verified config ~inspect ~check_cancel f = match config with
  | None -> f None
  | Some config ->
    let path = config.process.launcher in
    let verify_size () =
      let st = Unix.LargeFile.stat path in
      if st.Unix.LargeFile.st_kind <> Unix.S_REG || st.st_size <= 0L || st.st_size > 8388608L then
        raise (Util.Transient "Helper limiter must be a nonempty regular executable of at most8 MiB") in
    check_cancel (); verify_size ();
    BorrowedWork.bind (fun () -> inspect path) (fun ((hash,size,identity) as before) ->
      if hash <> config.hash || size <= 0L || size > 8388608L || identity = "" then
        raise (Util.Transient "Helper limiter executable pin mismatch");
      let after () =
        check_cancel (); verify_size ();
        BorrowedWork.bind (fun () -> inspect path) (fun current ->
          if current <> before then raise (Util.Transient "Helper limiter changed during execution");
          check_cancel (); return ()) in
      check_cancel ();
      BorrowedWork.try_bind (fun () -> f (Some config.process))
        (fun result -> BorrowedWork.bind after (fun () -> return result))
        (fun error -> BorrowedWork.try_bind after
          (fun () -> fail error) (fun _ -> fail error)))
