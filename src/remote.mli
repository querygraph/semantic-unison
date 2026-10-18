(* Unison file synchronizer: src/remote.mli *)
(* Copyright 1999-2020, Benjamin C. Pierce (see COPYING for details) *)

module Thread : sig
  val unwindProtect : (unit -> 'a Lwt.t) -> (exn -> unit Lwt.t) -> 'a Lwt.t
end

(* Register a server function.  The result is a function that takes a host
   name as argument and either executes locally or else communicates with a
   remote server, as appropriate.  (Calling registerServerCmd also has the
   side effect of registering the command under the given name, so that when
   we are running as a server it can be looked up and executed when
   requested by a remote client.) *)
(* It is not recommended to use this function in new code unless the cmd is
   truly independent of any roots/replicas. Use [registerRootCmd] or one of
   the other functions instead. *)
val registerHostCmd :
    string              (* command name *)
 -> 'a Umarshal.t -> 'b Umarshal.t
 -> ('a -> 'b Lwt.t)    (* local command *)
 -> (   Common.root     (* -> host (the root path is ignored) *)
     -> 'a              (*    arguments *)
     -> 'b Lwt.t)       (*    -> (suspended) result *)

(* A variant of registerHostCmd, for constructing a remote command to be
   applied to a particular root (host + fspath).
 -

   A naming convention: when a `root command' is built from a
   corresponding `local command', we name the two functions
   <funcName>OnRoot and <funcName>Local *)
val registerRootCmd :
    string                         (* command name *)
 -> 'a Umarshal.t -> 'b Umarshal.t
 -> ((Fspath.t * 'a) -> 'b Lwt.t)  (* local command *)
 -> (   Common.root                (* -> root *)
     -> 'a                         (*    additional arguments *)
     -> 'b Lwt.t)                  (*    -> (suspended) result *)

(* Test whether a command exits on some root *)
val commandAvailable :
  Common.root ->                   (* root *)
  string ->                        (* command name *)
  bool Lwt.t

(* Enter "server mode", reading and processing commands from a remote
   client process until killed *)
val beAServer : unit -> unit
val waitOnPort : string list -> string -> unit

(* Whether the server should be killed when the client terminates *)
val killServer : bool Prefs.t

(* Establish a connection to the remote server (if any) corresponding
   to the root and return the canonical name of the root *)
val canonizeRoot :
  string -> Clroot.clroot -> (string -> Terminal.termInteract) option ->
  Common.root Lwt.t

(* Test if connection to the remote server (if any) corresponding
   to the root is established. Always returns true for local roots *)
val isRootConnected : Common.root -> bool

(* Close the connection to server and run all cleanup and [at_conn_close]
   handlers. Can also be called for a local root; in this case only the
   cleanup and [at_conn_close] handlers are run (as there is no connection
   to close). *)
val clientCloseRootConnection : Common.root -> unit

(* Statistics *)
val emittedBytes : float ref
val receivedBytes : float ref

(* Establish a connection to the server.
   First call openConnectionStart, then loop:
     call openConnectionPrompt, if you get a prompt,
     respond with openConnectionReply if desired.
   After you get None from openConnectionPrompt,
   call openConnectionEnd.
   Call openConnectionCancel to abort the connection.
*)
type preconnection
val openConnectionStart : Clroot.clroot -> preconnection option
val openConnectionPrompt : preconnection -> string option
val openConnectionReply : preconnection -> string -> unit
val openConnectionEnd : preconnection -> unit
val openConnectionCancel : preconnection -> unit

(* return the canonical name of the root.  The connection
   to the root must have already been established by
   the openConnection sequence. *)
val canonize : Clroot.clroot -> Common.root

(****)

type msgId = int
module MsgIdMap : Map.S with type key = msgId
val newMsgId : unit -> msgId

type connection
val connectionVersion : connection -> int
val connectionOfRoot : Common.root -> connection

val register_body_ownership_classifier : (exn -> bool) -> unit
(** Owner-loop initialization hook for ownership carriers defined after Remote.
    Predicates must be pure/owner-only. Registration is additive; no unregister
    or release authority. True or a classifier exception retains body allowance
    through RetainedOwnership rather than translating uncertainty into cleanup.
    This does not discover OS closure or recognize arbitrary unknown exceptions. *)

(* Every incoming packet also obeys the endpoint-local rpcpacketmaxbytes
   outer frame policy. Regular server arguments also use the independent
   rpcdecodedrequestbudget/elements/slots selected-cost owner through actual
   handler/reply settlement. Ordinary legacy registrations use finite owner
   policy limits directly, without a frame-expansion heuristic; bounded
   registrations additionally apply their declared per-decode limits.
   Wire encodings are unchanged. User conversions/global escapes, client
   results, custom streaming decoders, metadata and full heap/RSS are excluded.
   Recognized ownership uncertainty retains selected charges and value roots.
   Handler code must not let arguments escape its actual operation without a
   separate owned lifetime. rpcpendingreplyslots independently bounds pending
   waiter entries (default256/max65536), refusing without waiting before request
   marshaling and rechecking before insertion. Entries end on actual response
   handoff/failure/removal, not decoded client-value lifetime. Duplicate reply
   IDs cannot replace a pending waiter. Frame limits alone are not aggregate
   accounting; outgoing buffers and results still need their own ownership. *)
val registerServerCmd :
  string
 -> 'a Umarshal.t -> 'b Umarshal.t
 -> (connection -> 'a -> 'b Lwt.t)
 -> connection -> 'a -> 'b Lwt.t
val registerBoundedServerCmd :
  ?withScope:(connection -> 'a -> (unit -> unit Lwt.t) -> unit Lwt.t) ->
  ?maxResultForArgs:('a -> int) ->
  string -> maxArgs:int -> maxResult:int -> 'a Umarshal.t -> 'b Umarshal.t ->
  (connection -> 'a -> 'b Lwt.t) -> connection -> 'a -> 'b Lwt.t
(** Additive RPC registration with request and normal-result body frame limits,
    including marshaling tags/headers, checked before outer buffer allocation.
    [maxResultForArgs] can narrow the normal-result limit for each request;
    its result must be nonnegative and is capped at [maxResult].
    [withScope] must invoke and await its callback exactly once. It wraps the
    server computation, response marshaling and consumption by the output
    queue, allowing retained-resource leases to cover the entire reply lifetime.
    A scope failure before the callback can produce an exception reply; failures
    after dispatch starts never produce an additional reply.
    Selected builtin decode allocations are limited per decode to
    [65536 + 8 * frame_limit] charged bytes and collection counts to
    [1024 + 4 * frame_limit]; overflow refuses registration. These charges are
    not decoded heap/RSS or aggregate request bounds. Scope and handler share
    one decoded argument value. The endpoint-local rpcdecodedrequestbudget,
    rpcdecodedrequestelements and rpcdecodedrequestslots independently admit
    regular-command arguments before selected builtin allocations. Owners span
    scope/handler and queued reply consumption, retaining recognized ownership
    uncertainty and the decoded argument itself. Ordinary decode refusal releases
    its partial debit after known failure. Conversion/global escapes, custom streaming
    decoders, returned client values, metadata, recursion and full heap/RSS
    are excluded; handlers/scopes must not retain arguments beyond their actual
    operation without a separately owned lifetime. Valid wire bytes unchanged.
    Shared RPC headers use independent endpoint-local frame/byte/slot limits.
    All body registrations also use separate aggregate request/reply raw-input
    lanes. These follow actual processing/queued output or result decoding and
    preserve recognized ownership uncertainty; not decoded-object/RSS limits. *)
val registerBoundedServerCmdWithResultScope :
  ?withScope:(connection -> 'a -> (unit -> unit Lwt.t) -> unit Lwt.t) ->
  ?maxResultForArgs:('a -> int) ->
  string -> maxArgs:int -> maxResult:int -> 'a Umarshal.t -> 'b Umarshal.t ->
  (connection -> 'a -> 'b Lwt.t) ->
  connection -> 'a -> ('b -> 'c Lwt.t) -> 'c Lwt.t
(** Like bounded registration, but the client supplies its actual asynchronous
    result consumer. Independent endpoint-local rpcdecodedresultbudget/elements/
    slots admit selected builtin decode costs before allocations and retain the
    value through consumer settlement. Known failure releases partial charges;
    recognized ownership uncertainty retains charges and explicit value roots.
    The consumer must not let the decoded value escape into its return value,
    a global, or independent work without separately owned lifetime accounting.
    Copied/converted objects need their own budget; this is not heap/RSS or
    automatic lifetime tracking. No wire change; legacy result APIs unchanged. *)
val intSize : int
val encodeInt : int -> Bytearray.t * int * int
val decodeInt : Bytearray.t -> int -> int
(** Requires a complete five-byte field at a nonnegative offset. Truncation or
    invalid offset raises Util.Fatal before any array access; checksum unchanged. *)
val registerRootCmdWithConnection :
    string                          (* command name *)
 -> 'a Umarshal.t -> 'b Umarshal.t
 -> (connection -> 'a -> 'b Lwt.t)  (* local command *)
 ->    Common.root                  (* root on which the command is executed *)
    -> Common.root                  (* other root *)
    -> 'a                           (* additional arguments *)
    -> 'b Lwt.t                     (* result *)

val streamingActivated : bool Prefs.t

val registerStreamCmd :
  ?maxPayload:int -> string ->
  (connection -> 'a ->
   (Bytearray.t * int * int) list -> (Bytearray.t * int * int) list * int) *
  (connection -> Bytearray.t -> int -> 'a) ->
  (connection -> 'a -> unit) ->
  connection -> (('a -> unit Lwt.t) -> 'b Lwt.t) -> 'b Lwt.t
(** Optional nonnegative maximum custom encoded payload, excluding the RPC tag.
    Includes all custom codec fields. Endpoint derives separate -str/-args body
    caps, rejecting overflow at registration. Both stream and ordinary fallback
    caps apply before raw body allocation, independently of the outer endpoint
    limit and existing raw input lanes. Absent limit preserves the existing
    custom registration behavior. This does not account custom heap/workspace. *)

(* Register a function to be run when the connection between client and server
   is closed (willingly or unexpectedly). The function should not raise
   exceptions. If it does then running some of the other registered functions
   may be skipped (which may not be an issue as the exception is likely going
   to quit the process).

   Registered functions are only expected to be useful when the connection is
   closed but the process keeps running (a socket server, for example). Do not
   use it as a substitute for [at_exit].

   These functions are additionally run when "closing" a local sync when there
   is no actual connection.

   Keep in mind that a function registered like this can be called immediately
   when a lost connection is detected, before any exception indicating lost
   connection is raised. *)
val at_conn_close : ?only_server:bool -> (unit -> unit) -> unit

(* Register resources to be cleaned up when the connection between client and
   server closes (normally or exceptionally). This cleanup is additionally run
   when "closing" a local sync when there is no actual connection.

   Closing the resources is still the responsibility of the code opening the
   resources but it is not always possible to run the resource cleanup code
   (due to an Lwt thread being stopped, for example). In those cases the
   registered resources are cleaned up when the connection is closed, as a
   last resort.

   The returned functions must be used to track the resources registered for
   cleanup. *)
type ('a, 'b, 'c) resourceC =
  { register : 'a -> 'a;       (* Register an opened resource for cleanup *)
    release : 'a -> 'b;        (* Unregister and close the resource normally *)
    release_noerr : 'a -> 'c } (* Same as above; don't raise exceptions *)

val resourceWithConnCleanup :
     ('a -> 'b) (* Function to close the resource normally *)
  -> ('a -> 'c) (* Function to close the resource, don't raise exceptions *)
  -> ('a, 'b, 'c) resourceC (* Functions to track resources for cleanup *)

(* Make an [Lwt_util.region] which is automatically purged and reset when
   the connection between client and server closes. This cleanup is also
   run when "closing" a local sync when there is no actual connection. *)
val lwtRegionWithConnCleanup : int -> Lwt_util.region ref
