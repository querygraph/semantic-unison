exception Original_error
external native_mode : int -> unit = "owned_fixture_mode"
external native_closes : unit -> int = "owned_fixture_closes"
external watch_parent : Unix.file_descr -> unit = "parent_fixture_watch"
external parent_closes : unit -> int = "parent_fixture_closes"
let mode=ref "known"
let basis=ref Unix.stdin and output=ref Unix.stdin and source=ref Unix.stdin
let pair_seen=ref false and source_seen=ref false
let nested_fd=ref Unix.stdin and nested_seen=ref false and nested_calls=ref 0
let read_calls=ref 0 and write_calls=ref 0 and source_calls=ref 0 and parent_calls=ref 0
let recycled=ref [] and unclosed=ref []
let handoff : StagePublication.parent_handoff option ref=ref None
let before_native_count=ref 0
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let pair b o=basis:=b;output:=o;pair_seen:=true
let source_open fd=source:=fd;source_seen:=true
let interrupt_pair ()= !mode="interrupt-pair"
let interrupt_source ()= !mode="interrupt-source"
let prepare ()=if !mode="prepare" then raise Original_error
let before_register ()=if !mode="register" || !mode="register-close" then raise Original_error
let before_source ()=if !mode="open-source" || !mode="open-source-close" then raise Original_error
let before_native context h parent =
 handoff:=Some h;watch_parent parent;
 if !mode="preentry" then begin
  native_mode (-1);
  (try StagePublication.abort_owned context with StagePublication.Ownership_uncertain _->());
  before_native_count:=native_closes ()
 end;
 if List.mem !mode ["before-native";"parent-before";"parent-after"] then raise Original_error
let after_native ()=if !mode="after-native" then raise Original_error
let close _read fd =
 let parent=(Unix.fstat fd).Unix.st_kind=Unix.S_DIR in
 let role=if !nested_seen && fd= !nested_fd then "nested" else if parent then "parent" else if !pair_seen && fd= !basis then "read"
  else if !pair_seen && fd= !output then "write" else if !source_seen && fd= !source then "source" else "other" in
 (match role with "read"->incr read_calls | "write"->incr write_calls | "source"->incr source_calls | "parent"->incr parent_calls | "nested"->incr nested_calls | _->());
 let fail=(role="nested" && !mode="borrowed-unknown") || (role="parent" && List.mem !mode ["parent-before";"parent-after"]) ||
  (role<>"parent" && role<>"other" &&
   (List.mem !mode ["all";"callback-close";"register-close";"open-source-close"] ||
    !mode=role || !mode="before-"^role)) in
 if fail && List.mem !mode ["before-read";"before-source";"parent-before"] then begin
  unclosed:=fd::!unclosed;raise(Unix.Unix_error(Unix.EIO,"local close before settlement",""))
 end;
 Unix.close fd;
 if fail then begin
  Unix.dup2 spare fd;recycled:=fd::!recycled;
  raise(Unix.Unix_error(Unix.EIO,"local close after settlement",""))
 end
let close_read fd=close true fd
let close_write fd=close false fd
