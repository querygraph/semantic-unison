let armed=ref false
let attempts=ref 0
let candidate=ref Unix.stdin
let replacements=ref []
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let open_candidate path =
 let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0 in
 candidate:=fd;fd
let close fd =
 let regular=(Unix.LargeFile.fstat fd).Unix.LargeFile.st_kind=Unix.S_REG in
 Unix.close fd;
 if regular then begin
  incr attempts;
  if !armed then begin
   Unix.dup2 spare fd;replacements:=fd::!replacements;
   raise(Unix.Unix_error(Unix.EIO,"I/O scope close after kernel close",""))
  end
 end
