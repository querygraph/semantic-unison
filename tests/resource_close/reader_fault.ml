exception Install_failed
let armed=Atomic.make false
let fail_install=Atomic.make false
let calls=Atomic.make 0
let replacement_fds : Unix.file_descr list Atomic.t = Atomic.make []
let spare=Atomic.make Unix.stdin
let arm ~install =
  Atomic.set spare (Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0);
  Atomic.set fail_install install;Atomic.set armed true
let after_close fd =
  ignore(Atomic.fetch_and_add calls 1);
  if Atomic.get armed then begin
    Unix.dup2 (Atomic.get spare) fd;
    Atomic.set replacement_fds (fd::Atomic.get replacement_fds);
    raise(Unix.Unix_error(Unix.EIO,"reader close after kernel close",""))
  end
let close_channel channel =
  let fd=Unix.descr_of_in_channel channel in
  close_in channel;after_close fd
let close_raw fd = Unix.close fd;after_close fd
let channel_of_fd fd =
  if Atomic.get fail_install then raise Install_failed;
  Unix.in_channel_of_descr fd
let attempts () = Atomic.get calls
let replacements () = Atomic.get replacement_fds
