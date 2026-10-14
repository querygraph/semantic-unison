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

val bind : (unit -> 'a Lwt.t) -> ('a -> 'b Lwt.t) -> 'b Lwt.t
val catch : (unit -> 'a Lwt.t) -> (exn -> 'a Lwt.t) -> 'a Lwt.t

val all : ?on_error:(exn -> unit) -> (unit -> 'a Lwt.t) list -> 'a list Lwt.t
(** Start the supplied thunks concurrently and retain every returned promise
    before allocating another observer. Launch/observer failure drains all
    recorded participants before reporting the first observed error. The optional
    owner-loop callback can stop a caller's consumers from starting more work;
    it must be nonblocking and non-raising. Unreturned independently dispatched
    work and persistent/delayed-connection failure have the limits above. *)
