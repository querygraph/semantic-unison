let armed=ref false
let attempts=ref 0
let close handle =
 if !armed then begin
  incr attempts;Unix.closedir handle;
  raise(Unix.Unix_error(Unix.EIO,"foreign closedir after settlement",""))
 end else Unix.closedir handle
