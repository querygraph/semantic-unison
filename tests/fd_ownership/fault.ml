(* Private fault state, used only by the owner thread except the atomic domain
   census. No production mutable hook is compiled into shipped code. *)
[@@@alert "-unsafe_multidomain"]
exception Primary
let mode = ref ""
let hits = ref 0
let close_calls = ref 0
let sentinel = ref None
let domains = Atomic.make 0
let rec adjust amount =
  let current = Atomic.get domains in
  if not (Atomic.compare_and_set domains current (current + amount)) then adjust amount
let hit name = if !mode = name ||
  (!mode = "pool-close-recycle" && name = "pool-shared") ||
  (!mode = "submit-close-recycle" && name = "submit-listener")
  then (incr hits; raise Primary)
let reset name = mode := name; hits := 0; close_calls := 0; sentinel := None
let set_nonblock label fd = hit label; Unix.set_nonblock fd
let close_channel channel =
  incr close_calls;
  let fd = Unix.descr_of_in_channel channel in
  Stdlib.close_in channel;
  if !mode = "semantic-close-recycle" then begin
    let replacement = Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    if replacement <> fd then failwith "fixture did not recycle the exact descriptor";
    sentinel := Some replacement;
    raise (Unix.Unix_error (Unix.EIO,"fixture-close",""))
  end
let close_channel_noerr channel = try close_channel channel with Unix.Unix_error _ -> ()
let close_fd fd =
  incr close_calls; Unix.close fd;
  if (!mode = "pool-close-recycle" || !mode = "submit-close-recycle") && !sentinel = None then begin
    let replacement = Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
    if replacement <> fd then failwith "fixture did not recycle exact raw FD";
    sentinel := Some replacement;
    raise (Unix.Unix_error (Unix.EIO,"fixture-close",""))
  end
let sentinel_alive () = match !sentinel with
  | None -> false
  | Some fd -> (try ignore (Unix.fstat fd); true with Unix.Unix_error _ -> false)
let dispose_sentinel () = match !sentinel with
  | None -> ()
  | Some fd -> sentinel := None; Unix.close fd
