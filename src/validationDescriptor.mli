type retained
val with_file : ?close:(Unix.file_descr -> unit) -> string ->
  (Unix.file_descr -> 'a Lwt.t) -> 'a Lwt.t
(** Read-only/nonblocking/CLOEXEC temporary owner. The callback must return all
    borrowed work. Close once after settlement; uncertainty roots its identity
    and original failure and returns a preallocated pending promise, retaining
    caller admission. No numeric retry/probe. The close override is for original
    fault controls; production uses Unix.close. No hostile namespace sandbox. *)
val retained : unit -> retained list
val descriptor : retained -> Unix.file_descr
val before_close : retained -> Unix.LargeFile.stats option
val close_error : retained -> exn
val original_failure : retained -> exn option
