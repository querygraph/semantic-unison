(* Original same-size mutation cases; exact mtime restoration is native-observed. *)
module P=FinalPublication
external times : string -> int64 * int * int64 * int = "unison_publication_test_exact_times"
external native_fds : unit -> int = "final_publication_fixture_fd_count"
let check value reason=if not value then failwith reason
let payload=String.make 128 'P'
let sentinel=String.make 128 'T'
let write path bytes flags=
 let fd=Unix.openfile path (Unix.O_WRONLY::Unix.O_CLOEXEC::flags) 0o600 in
 Fun.protect ~finally:(fun()->Unix.close fd) (fun()->
  let rec loop pos=if pos<String.length bytes then
   let n=Unix.write_substring fd bytes pos (String.length bytes-pos) in
   check(n>0) "fixture write stalled";loop(pos+n) in loop 0)
let read path=let channel=open_in_bin path in
 Fun.protect ~finally:(fun()->close_in channel) (fun()->really_input_string channel (in_channel_length channel))
let restored path before=
 let ms,mn,cs,cn=before in let ms2,mn2,cs2,cn2=times path in
 check(ms=1700000000L && mn=0 && ms=ms2 && mn=mn2) "fixture did not restore exact native mtime";
 check(cs<>cs2 || cn<>cn2) "fixture did not change native ctime";
 Printf.printf "native_mtime=%Ld.%09d unchanged native_ctime=%Ld.%09d->%Ld.%09d\n%!" ms mn cs cn cs2 cn2
let ()=
 if not(P.available()) then failwith "native publication unavailable";
 let base=native_fds() in
 List.iter(fun selected ->
  let directory=Filename.concat Sys.argv.(1) selected in Unix.mkdir directory 0o700;
  let candidate=Filename.concat directory "candidate" and target=Filename.concat directory "target" in
  write candidate payload [Unix.O_CREAT;Unix.O_EXCL];write target sentinel [Unix.O_CREAT;Unix.O_EXCL];
  let changed=if selected="candidate" then candidate else target in
  Unix.utimes changed 1700000000. 1700000000.;let before=times changed in
  let owner=P.prepare ~logical_root:directory ~working_dir:directory ~candidate:"candidate" ~target:"target" ~check_apple_double:true in
  P.attach owner;P.observe_target owner;
  Unix.sleepf 0.01;write changed (String.make 128 'X') [];Unix.utimes changed 1700000000. 1700000000.;
  restored changed before;check(read changed=String.make 128 'X') "same-size bytes did not change";
  let preserved=read target in
  check(try P.publish owner;false with Unix.Unix_error(Unix.EBUSY,_,_)->true) "restored-mtime mutation published";
  check(not(P.published owner) && read target=preserved) "refusal changed live target";
  P.abort_and_close owner;check(native_fds()=base) "restored-mtime guard leaked native proof descriptors";
  Printf.printf "PASS %s same-size changed bytes/exact restored mtime refused with live target preserved\n%!" selected
 ) ["candidate";"target"];
 Printf.printf "PASS 2 restored-native-mtime publication mutation cases\n%!"
