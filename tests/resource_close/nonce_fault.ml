exception Read_failed
let mode=ref "known"
let reads=ref 0 and closes=ref 0
let recycled=ref [] and unclosed=ref []
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let read fd buffer start count =
 incr reads;
 if !mode="read-error" || !mode="read-close" then raise Read_failed;
 if !mode="empty" then 0
 else if !mode="interrupt" && !reads=1 then raise(Unix.Unix_error(Unix.EINTR,"nonce read",""))
 else Unix.read fd buffer start count
let close fd =
 incr closes;
 if !mode="before" then begin unclosed:=fd::!unclosed;raise(Unix.Unix_error(Unix.EIO,"nonce close before settlement","")) end;
 Unix.close fd;
 if !mode="after" || !mode="read-close" then begin
  Unix.dup2 spare fd;recycled:=fd::!recycled;
  raise(Unix.Unix_error(Unix.EIO,"nonce close after kernel close",""))
 end
