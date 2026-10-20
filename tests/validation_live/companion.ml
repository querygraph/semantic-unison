open Lwt
let check b s=if not b then failwith s
let read path=let f=open_in_bin path in Fun.protect ~finally:(fun()->close_in f)
 (fun()->really_input_string f (in_channel_length f))
let mode=Sys.argv.(1)
let helper=Sys.argv.(2)
let candidate=Filename.concat(Sys.getcwd()) "candidate.dng"
let inspect path=
 let st=Unix.LargeFile.stat path in
 return {CandidateValidator.sha256=SemanticHash.hex(SemanticHash.string(read path));
 size=st.st_size;identity=Printf.sprintf "%d:%d:%Ld:%.17g" st.st_dev st.st_ino st.st_size st.st_mtime}
let () =
 Unix.mkdir Util.unisonDir 0o700;
 Prefs.loadStrings (["log = false";"adobevalidate = "^(if mode="off" then "off" else "require");
   "adobevalidator = "^helper;"adobevalidatorhash = "^SemanticHash.hex(SemanticHash.string(read helper));
   "adobevalidatorbuild = synthetic-live-1";"adobevalidatorthreads = 1";"adobevalidatetimeout = 3";
   "debug = validation-group"]@(if mode="silent" then [] else ["debug = validation-live"]));
 Features.setEnabled(Features.all());
 let supervisor=HelperSupervisor.create ~cpu_permits:2 ~max_children:2 ~max_pending:4 in
 let cancellation=HelperSupervisor.cancellation () in
 let expected=Lwt_unix.run(inspect candidate) in
 let context={CandidateValidator.supervisor;cancellation;cpu_budget=2;candidate;destination=candidate;expected;
   resources=BackendResources.none;inspect;execute=(fun run->run())} in
 let verdict=try (match DngCandidateValidation.select() with
   | None -> () | Some validate ->
       if mode="parallel" then begin
         let candidate2=Filename.concat(Sys.getcwd()) "candidate2.dng" in
         let expected2=Lwt_unix.run(inspect candidate2) in
         let context2={context with candidate=candidate2;expected=expected2} in
         let a=validate context and b=validate context2 in
         Lwt_unix.run(a >>= fun () -> b)
       end else Lwt_unix.run(validate context));true with Util.Transient _ -> false in
 check(verdict<>(mode="error")) "companion receipt decision differs";
 check(HelperSupervisor.usage supervisor=(0,0)) "companion helper credits not closed";
 let calls=if Sys.file_exists "helper.calls" then String.split_on_char '\n'(String.trim(read "helper.calls")) else [] in
 check(List.length calls=(if mode="off" then 0 else if mode="parallel" then 2 else 1)) "helper call count differs";
 List.iter(fun line -> let pid=int_of_string line in
   check(try ignore(Unix.waitpid[Unix.WNOHANG]pid);false with Unix.Unix_error(Unix.ECHILD,_,_)->true)
    "helper direct wait not complete") calls;
 Printf.printf "COMPONENT-CLOSED owner=%d mode=%s helpers=%d cpu=0 children=0\n%!" (Unix.getpid()) mode (List.length calls)
