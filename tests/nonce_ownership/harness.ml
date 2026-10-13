module RealUnix = Unix
module RealBytes = Bytes
module Util = struct exception Transient of string end

type mode = Success | Constructor_oom | Open_error | Read_oom | Read_error
  | Eof | Prefix_eof | Interrupted_short | Close_error | Read_and_close_error
  | Close_error_reuse | String_oom_reuse | Read_close_error_reuse
let mode = ref Success
let directory = ref ""
let random_fd = ref RealUnix.stdin and sentinel_fd = ref RealUnix.stdin
let owns_random = ref false and owns_sentinel = ref false
let random_dev = ref 0 and random_ino = ref 0
let sentinel_dev = ref 0 and sentinel_ino = ref 0
let open_attempts = ref 0 and actual_opens = ref 0
let read_calls = ref 0 and actual_reads = ref 0 and actual_bytes = ref 0
let close_calls = ref 0 and actual_closes = ref 0
let constructor_faults = ref 0 and string_faults = ref 0 and read_faults = ref 0
let close_faults = ref 0 and interrupted = ref 0
let reused = ref false
let read_marker = Failure "private nonce read failure"
let open_marker = RealUnix.Unix_error (RealUnix.EACCES, "private nonce open", "")
let close_marker = RealUnix.Unix_error (RealUnix.EIO, "private nonce close", "")
let sentinel_payload = RealBytes.of_string "nonce descriptor reuse sentinel"
let fd_closed fd =
  try ignore (RealUnix.fstat fd); false
  with RealUnix.Unix_error (RealUnix.EBADF, _, _) -> true
let random_alive () =
  try let stat = RealUnix.fstat !random_fd in
    stat.RealUnix.st_kind=RealUnix.S_CHR && stat.RealUnix.st_dev= !random_dev &&
    stat.RealUnix.st_ino= !random_ino
  with RealUnix.Unix_error (RealUnix.EBADF, _, _) -> false
let sentinel_alive () =
  try let stat = RealUnix.fstat !sentinel_fd in
    stat.RealUnix.st_kind=RealUnix.S_REG && stat.RealUnix.st_dev= !sentinel_dev &&
    stat.RealUnix.st_ino= !sentinel_ino
  with RealUnix.Unix_error (RealUnix.EBADF, _, _) -> false
let cleanup () =
  if !owns_random then begin
    owns_random := false;
    if random_alive () then RealUnix.close !random_fd
    else if not (fd_closed !random_fd) then failwith "fixture random descriptor changed identity"
  end;
  if !owns_sentinel then begin
    owns_sentinel := false;
    if sentinel_alive () then RealUnix.close !sentinel_fd
    else if not (fd_closed !sentinel_fd) then failwith "fixture sentinel descriptor changed identity"
  end
let verify_fixture_settled name =
  if !owns_random || !owns_sentinel ||
     (!actual_opens>0 && not (fd_closed !random_fd)) ||
     (!reused && not (fd_closed !sentinel_fd)) then
    failwith "fixture cleanup left an owned descriptor open";
  Printf.printf "CLEAN %s owned_flags_clear=true random_number_closed=%b sentinel_number_closed=%b\n%!"
    name (!actual_opens=0 || fd_closed !random_fd) (not !reused || fd_closed !sentinel_fd)
let reset ~work selected =
  cleanup (); directory := work; mode := selected;
  open_attempts := 0; actual_opens := 0; read_calls := 0; actual_reads := 0;
  actual_bytes := 0; close_calls := 0; actual_closes := 0; constructor_faults := 0;
  string_faults := 0; read_faults := 0; close_faults := 0; interrupted := 0; reused := false
let make_sentinel fd =
  let path = Filename.concat !directory "reuse-sentinel" in
  let replacement = RealUnix.openfile path
    [RealUnix.O_RDWR; RealUnix.O_CREAT; RealUnix.O_TRUNC; RealUnix.O_CLOEXEC] 0o600 in
  sentinel_fd := replacement; owns_sentinel := true;
  let stat = RealUnix.fstat replacement in
  sentinel_dev := stat.RealUnix.st_dev; sentinel_ino := stat.RealUnix.st_ino;
  reused := replacement=fd;
  ignore (RealUnix.write replacement sentinel_payload 0 (RealBytes.length sentinel_payload));
  ignore (RealUnix.lseek replacement 0 RealUnix.SEEK_SET)
let verify_sentinel () =
  if not !reused then failwith "closed descriptor number was not reused";
  if not (sentinel_alive ()) then failwith "nonce cleanup closed reused sentinel";
  let bytes = RealBytes.create (RealBytes.length sentinel_payload) in
  ignore (RealUnix.lseek !sentinel_fd 0 RealUnix.SEEK_SET);
  let count = RealUnix.read !sentinel_fd bytes 0 (RealBytes.length bytes) in
  if count<>RealBytes.length bytes || bytes<>sentinel_payload then
    failwith "nonce cleanup changed reused sentinel data"

module Bytes = struct
  include RealBytes
  let create count =
    if !mode=Constructor_oom then (incr constructor_faults; raise Out_of_memory);
    RealBytes.create count
  let to_string bytes =
    if !mode=String_oom_reuse then (incr string_faults; raise Out_of_memory);
    RealBytes.to_string bytes
end
module Unix = struct
  include RealUnix
  let openfile path flags permissions =
    incr open_attempts;
    if !mode=Open_error then raise open_marker;
    if path<>"/dev/urandom" || not (List.mem RealUnix.O_CLOEXEC flags) then
      failwith "nonce selected unexpected random source or descriptor flags";
    let fd = RealUnix.openfile path flags permissions in
    random_fd := fd; owns_random := true; incr actual_opens;
    let stat = RealUnix.fstat fd in
    random_dev := stat.RealUnix.st_dev; random_ino := stat.RealUnix.st_ino;
    fd
  let read fd bytes offset count =
    incr read_calls;
    (match !mode with
     | Read_oom -> incr read_faults; raise Out_of_memory
     | Read_error | Read_and_close_error | Read_close_error_reuse ->
         incr read_faults; raise read_marker
     | Eof -> ()
     | Interrupted_short when !interrupted<3 ->
         incr interrupted; raise (RealUnix.Unix_error (RealUnix.EINTR, "private nonce read", ""))
     | _ -> ());
    if !mode=Eof || (!mode=Prefix_eof && !actual_reads>0) then 0 else begin
      let count = match !mode with Interrupted_short -> min count 7 | Prefix_eof -> min count 8 | _ -> count in
      let got = RealUnix.read fd bytes offset count in
      incr actual_reads; actual_bytes := !actual_bytes + got; got
    end
  let close fd =
    incr close_calls;
    RealUnix.close fd;
    if fd= !random_fd then owns_random := false;
    incr actual_closes;
    if !mode=Close_error_reuse || !mode=String_oom_reuse || !mode=Read_close_error_reuse then
      if not !reused then make_sentinel fd;
    if !mode=Close_error || !mode=Read_and_close_error || !mode=Close_error_reuse ||
       !mode=Read_close_error_reuse then (incr close_faults; raise close_marker)
end

let print_observation name =
  Printf.printf "OBS %s open_attempts=%d opens=%d reads=%d actual_reads=%d bytes=%d close_calls=%d actual_closes=%d constructor_faults=%d string_faults=%d read_faults=%d close_faults=%d eintr=%d random_alive=%b reused=%b sentinel_alive=%b\n%!"
    name !open_attempts !actual_opens !read_calls !actual_reads !actual_bytes
    !close_calls !actual_closes !constructor_faults !string_faults !read_faults
    !close_faults !interrupted (if !actual_opens=0 then false else random_alive ())
    !reused (if !reused then sentinel_alive () else false)
