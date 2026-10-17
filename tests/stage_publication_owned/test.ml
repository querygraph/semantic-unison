module P=StagePublication
external mode : int -> unit = "owned_fixture_mode"
external closes : unit -> int = "owned_fixture_closes"
external busy : unit -> int = "owned_fixture_busy"
external known_open : int -> bool = "owned_fixture_known_open"
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let read path=let input=open_in_bin path in let s=really_input_string input(in_channel_length input) in close_in input;s
let payload="original private publication fixture"
let setup root name =
 let dir=Filename.concat root name in Unix.mkdir dir 0o700;
 List.iter(fun leaf->Unix.mkdir(Filename.concat dir leaf)0o700)["in";"out"];
 let path=Filename.concat dir "in/stage" in
 let output=open_out_bin path in output_string output payload;close_out output;
 dir,path
let prepare dir=P.prepare_owned ~working_dir:dir ~stage:"in/stage" ~temporary:"out/temp"
let uncertain work=try work();failwith "expected ownership uncertainty" with
 | P.Ownership_uncertain(Some owner) as error->owner,error
let unchanged owner error expected =
 let before=P.owned_evidence owner and count=closes() in
 let _,again=uncertain(fun()->P.abort_owned owner) in
 check(again==error) "uncertainty delivery allocated/replaced its carrier";
 Gc.full_major();
 check(P.owned_evidence owner=before && closes()=count) "unknown close retried/mutated evidence";
 let _,_,entries,known=before in
 check(Array.length entries=expected) "uncertain descriptor multiplicity lost";
 Array.iter(fun (_,number,phase,device,inode)->
  check(number<>0 && phase<>"" && device<>None && inode<>None) "preclose identity/error lost") entries;
 Array.iter(fun fd->check(known_open fd) "known held descriptor disappeared")known
let adopt dir path owner =
 let parent=Unix.openfile(Filename.concat dir "in")[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
 let input=Unix.openfile path[Unix.O_RDWR;Unix.O_CLOEXEC]0 in
 P.adopt_owned owner ~parent ~stage:input;input
let ()=
 if not(P.available()) then exit 77;
 let root=Sys.argv.(1) in
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let dir,_=setup root "normal-abort" in mode 0;
 let owner=prepare dir in P.abort_owned owner;
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "normal prepare/abort retained native handles";
 let dir,path=setup root "normal-publish" in mode 0;
 let owner=prepare dir in let input=adopt dir path owner in
 P.publish_owned owner;P.disarm_owned owner;Unix.close input;
 check(read(Filename.concat dir "out/temp")=payload && not(Sys.file_exists path)) "normal publication bytes/name";
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "normal disarm retained native handles";
 let dir,_=setup root "prepare-failure" in mode(-1);
 let owner,error=uncertain(fun()->ignore(P.prepare_owned ~working_dir:dir ~stage:"in/stage" ~temporary:"missing/temp")) in
 let phase,(_,cause),_,known=P.owned_evidence owner in
 check(phase="closed" && cause="stage_publication.prepare.temporary_parent" && Array.length known=0)
  "original prepare error or known handle state lost";
 unchanged owner error 2;
 let dir,path=setup root "adopt-failure" in mode 0;
 let owner=prepare dir in
 let parent=Unix.openfile(Filename.concat dir "in")[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
 let input=Unix.openfile path[Unix.O_RDWR;Unix.O_CLOEXEC]0 in mode 4;
 let owner,error=uncertain(fun()->P.adopt_owned owner ~parent ~stage:input) in
 Unix.close input;
 let phase,_,_,known=P.owned_evidence owner in
 check(phase="stage-owned" && Array.length known=4 && read path=payload) "adopt uncertainty lost live owner/name";
 unchanged owner error 1;
 let dir,path=setup root "disarm-failure" in mode 0;
 let owner=prepare dir in let input=adopt dir path owner in P.publish_owned owner;mode(-1);
 let owner,error=uncertain(fun()->P.disarm_owned owner) in Unix.close input;
 let phase,_,_,known=P.owned_evidence owner in
 check(phase="disarmed" && Array.length known=0 && read(Filename.concat dir "out/temp")=payload)
  "postpublication close error removed/misclassified published file";
 unchanged owner error 4;
 let dir,path=setup root "abort-failure" in mode 0;
 let owner=prepare dir in let input=adopt dir path owner in mode(-1);
 let owner,error=uncertain(fun()->P.abort_owned owner) in Unix.close input;
 let phase,_,_,known=P.owned_evidence owner in
 check(phase="closed" && Array.length known=0 && not(Sys.file_exists path)) "abort effects misclassified";
 unchanged owner error 4;
 let dir,path=setup root "combined-failure" in mode 0;
 let owner=prepare dir in
 let parent=Unix.openfile(Filename.concat dir "in")[Unix.O_RDONLY;Unix.O_CLOEXEC]0 in
 let input=Unix.openfile path[Unix.O_RDWR;Unix.O_CLOEXEC]0 in
 let moved=dir^"-moved" in Unix.rename dir moved;Unix.mkdir dir 0o700;mode 1;
 let owner,error=uncertain(fun()->P.adopt_owned owner ~parent ~stage:input) in Unix.close input;
 let phase,(number,cause),_,known=P.owned_evidence owner in
 check(phase="prepared" && number=busy() && cause="stage_publication.binding.working_directory" &&
  Array.length known=4 && read(Filename.concat moved "in/stage")=payload)
  "binding error plus uncertain probe close lost original cause/known owner";
 unchanged owner error 1;
 Printf.printf "PASS %d owned publication checks; native unknown carriers intentionally retained until disposable process exit\n%!" !checks
