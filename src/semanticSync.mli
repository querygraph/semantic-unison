val try_local : source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool
(** Sequential reference implementation for tests. Production uses
    [try_local_async]. Creates only transaction-owned staging; false means
    normal copy should be used. No live file is modified. *)
val is_enabled : unit -> bool
val try_local_async : source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool Lwt.t
(** Production local semantic transaction. Inspects source and private basis
    concurrently, materializes and verifies on typed workers under the shared
    CPU budget. The caller retains the stock source/property/fork/fingerprint
    lifecycle. False means ordinary copying should be used. *)
val try_local_async_with_producer : producer:(Unix.file_descr -> unit) ->
  source:Fspath.t -> basis:Fspath.t -> directory:Fspath.t ->
  staging:Path.local -> bool Lwt.t
(** Bound local semantic transaction. Promote the verified candidate through
    a captured creation-parent owner, then pass its still-open output descriptor
    to [producer] before relinquishing staging ownership and closing the
    transaction. Callback failures are terminal and retain their original
    exception. Unsupported initial preparation/layout may return false. *)
