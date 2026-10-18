exception Original_error
let mode=ref "known"
let read_calls=ref 0 and write_calls=ref 0
let recycled=ref [] and unclosed=ref []
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let failing read =
 !mode<>"known" && (!mode<>"read" || read) && (!mode<>"write" || not read)
let close read fd =
 let regular=(Unix.LargeFile.fstat fd).Unix.LargeFile.st_kind=Unix.S_REG in
 if regular then (if read then incr read_calls else incr write_calls);
 if regular && failing read && !mode="before" then begin
  unclosed:=fd::!unclosed;
  raise(Unix.Unix_error(Unix.EIO,"remote pair close before settlement",""))
 end;
 Unix.close fd;
 if regular && failing read then begin
  Unix.dup2 spare fd;recycled:=fd::!recycled;
  raise(Unix.Unix_error(Unix.EIO,"remote pair close after kernel close",""))
 end
let close_read fd=close true fd
let close_write fd=close false fd
let before_register ()=if !mode="register" then raise Original_error
let before_record ()=if !mode="record" then raise Original_error
