exception Original_error
external native_mode : int -> unit = "owned_fixture_mode"
external native_closes : unit -> int = "owned_fixture_closes"
external watch : Unix.file_descr -> unit = "parent_fixture_watch"
external native_parent_closes : unit -> int = "parent_fixture_closes"
let mode=ref "known"
let entered=ref false
let handoff : StagePublication.parent_handoff option ref=ref None
let parent_fd=ref Unix.stdin
let parent_calls=ref 0 and pair_read_calls=ref 0 and pair_write_calls=ref 0
let recycled=ref [] and unclosed=ref []
let before_count=ref 0
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let interrupt () = !mode="interrupted"
let before_native context h parent =
 entered:=true;handoff:=Some h;parent_fd:=parent;watch parent;
 if !mode="preentry" then begin
  native_mode (-1);
  (try StagePublication.abort_owned context with StagePublication.Ownership_uncertain _ -> ());
  before_count:=native_closes ()
 end;
 if List.mem !mode ["before-call";"parent-before";"parent-after";"combined"] then raise Original_error
let after_native ()=if !mode="after-call" then raise Original_error
let close read fd =
 let kind=(Unix.LargeFile.fstat fd).Unix.LargeFile.st_kind in
 let parent=kind=Unix.S_DIR and regular=kind=Unix.S_REG in
 if parent then incr parent_calls else if regular then (if read then incr pair_read_calls else incr pair_write_calls);
 if parent && !mode="parent-before" then begin unclosed:=fd::!unclosed;raise(Unix.Unix_error(Unix.EIO,"parent close before settlement","")) end;
 Unix.close fd;
 if (parent && (!mode="parent-after" || !mode="combined")) || (regular && !mode="combined") then begin
  Unix.dup2 spare fd;recycled:=fd::!recycled;
  raise(Unix.Unix_error(Unix.EIO,"parent/pair close after kernel close",""))
 end
let close_read fd=close true fd
let close_write fd=close false fd
