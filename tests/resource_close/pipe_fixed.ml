exception Original_error
let require yes why=if not yes then failwith why
let () =
 let mode=Sys.argv.(1) in
 let pipe=NotificationPipe.prepare () in
 let read,write=Unix.pipe ~cloexec:true () in
 NotificationPipe.adopt pipe read write;
 PipeFault.read_fd:=read;PipeFault.write_fd:=write;
 PipeFault.fail_read:=(mode="read" || mode="both" || mode="wrapped");
 PipeFault.fail_write:=(mode="write" || mode="both");
 if mode="wrapped" || mode="known-wrapped" then
   NotificationPipe.install_reader pipe (Lwt_unix.of_unix_file_descr read);
 NotificationPipe.remember_failure pipe Original_error;
 let uncertain=mode<>"known" && mode<>"known-wrapped" in
 let close ()=try NotificationPipe.close_all pipe;false
   with NotificationPipe.Uncertain actual -> require(actual==pipe) "wrong carrier";true in
 require(close ()=uncertain) "wrong settlement";
 require(Option.is_some(NotificationPipe.read_identity pipe) && Option.is_some(NotificationPipe.write_identity pipe)) "preclose identities missing";
 require(NotificationPipe.read_identity_error pipe=None && NotificationPipe.write_identity_error pipe=None) "identity observation failed";
 require(!(PipeFault.read_calls)=1 && !(PipeFault.write_calls)=1) "missing endpoint attempt";
 require(close ()=uncertain) "repeat result changed";
 require(!(PipeFault.read_calls)=1 && !(PipeFault.write_calls)=1) "numeric retry";
 require(NotificationPipe.settled pipe=not uncertain) "settled flag";
 require(NotificationPipe.operation_cause pipe=Some Original_error) "primary cause lost";
 require(Option.is_some(NotificationPipe.read_cause pipe)= !(PipeFault.fail_read)) "read cause";
 require(Option.is_some(NotificationPipe.write_cause pipe)= !(PipeFault.fail_write)) "write cause";
 require(NotificationPipe.retained_count ()=(if uncertain then 1 else 0)) "root count";
 Gc.full_major ();
 List.iter(fun fd -> ignore(Unix.fstat fd)) !(PipeFault.replacements);
 Printf.printf "PASS notification pipe %s; unknown settled at process exit only\n%!" mode
