let fail_read=ref false and fail_write=ref false
let read_fd=ref Unix.stdin and write_fd=ref Unix.stdout
let read_calls=ref 0 and write_calls=ref 0
let replacements=ref []
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let after fd =
  let failing=if fd= !read_fd then (incr read_calls;!fail_read)
    else if fd= !write_fd then (incr write_calls;!fail_write)
    else failwith "foreign pipe close" in
  if failing then begin
    Unix.dup2 spare fd;replacements:=fd::!replacements;
    raise(Unix.Unix_error(Unix.EIO,"pipe close after kernel close",""))
  end
let raw_close fd=Unix.close fd;after fd
let wrapped_close reader=
  (* Qualified Unix wrapper's descriptor representation is abstract. Keep the
     known raw identity separately; never reconstruct a wrapper to retry. *)
  Lwt_unix.close reader;after !read_fd
