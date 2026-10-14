(** Owner-loop settlement for returned asynchronous work.

    Like [Lwt.try_bind], but a failure while installing an observer on a
    returned promise cannot invoke the failure callback while that promise is
    still sleeping. Preserve the first installation error, retry its observer
    once, then poll without attaching an observer to the borrowed promise.
    Both callbacks run only after the returned work settles.

    Construct this guard before invoking work that acquires resources. The
    callback must return its actual work promise; starting independent work and
    throwing before returning it is outside this contract. The owner event loop
    must continue running. Persistent allocation failure, asynchronous callback
    connection failures and uninterruptible work have no settlement deadline. *)
val try_bind :
  (unit -> 'a Lwt.t) -> ('a -> 'b Lwt.t) -> (exn -> 'b Lwt.t) -> 'b Lwt.t
