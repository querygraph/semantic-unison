let armed = Atomic.make false
let hits = Atomic.make 0
let replacement_fds : Unix.file_descr list Atomic.t = Atomic.make []
let spare = Atomic.make Unix.stdin
let arm () =
  Atomic.set spare (Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0);
  Atomic.set armed true
let close fd =
  Unix.close fd;
  if Atomic.get armed then begin
    (* The old number now names a fresh, independently owned descriptor. A
       second close by the retired slot would corrupt this sentinel. *)
    Unix.dup2 (Atomic.get spare) fd;
    Atomic.set replacement_fds (fd :: Atomic.get replacement_fds);
    ignore (Atomic.fetch_and_add hits 1);
    raise (Unix.Unix_error (Unix.EIO,"injected close-after-kernel-close",""))
  end
let attempts () = Atomic.get hits
let replacements () = Atomic.get replacement_fds
