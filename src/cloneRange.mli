(** Portable range planning/execution, without native filesystem probing or
    capability caching. Bindings and adapters are trusted endpoint-local inputs,
    never capabilities accepted from a peer. Exact content verification and
    final publication remain the caller's responsibility. *)

type binding = {
  volume_id : string;
  generation : int64;
  file_id : string;
  size : int64;
}
type bindings = {
  owner_instance : string;
  backend_revision : string;
  source : binding;
  destination : binding;
}
(** [owner_instance] must not be reused when a process/controller restarts.
    Generation is assigned by the endpoint owner, not discovered by this module.
    Owner/backend/volume/file identities must be nonempty; generations and sizes
    are nonnegative. Two bindings identifying one file must agree on its size.
    Identity/size equality does not establish immutable source bytes: the caller
    must separately retain a stable basis and its content/stability proof. *)

type range_capability = {
  alignment : int64;
  max_bytes : int64;
  same_volume_only : bool;
  same_file_allowed : bool;
}
type capabilities = {
  native_whole : bool;
  composed_whole : bool;
  range : range_capability option;
  max_copy_bytes : int64;
}
(** Whole-file capabilities are represented separately and are not implemented
    by this range executor. Range offsets and request lengths use equal alignment.
    Destination EOF must already contain the authorized interval, for all kinds
    of operation. Source/destination overlap within one file is always rejected;
    [same_file_allowed] permits only disjoint native range calls. *)

type request = { source_offset : int64; destination_offset : int64; length : int64 }
type kind = Copy | Share
type operation = { kind : kind; source_offset : int64; destination_offset : int64; length : int64 }
type prefix = { shared : int64; copied : int64 }
(** A prefix is contiguous from the start of the requested operation. [copied]
    reports bytes without a sharing guarantee, not measured physical writes.
    Counts do not describe the order of shared/copied extents within that prefix;
    an adapter remains responsible for every native extent's restrictions. *)

type mutation_state = Known_prefix | Indeterminate
type adapter_result =
  | Shared of int64
  | Copied of int64
  | Unsupported of { prefix : prefix; reason : string; mutation : mutation_state }
  | Error of { prefix : prefix; error : exn; mutation : mutation_state }

type receipt = { bindings : bindings; request : request; progress : prefix }
type fault =
  | Invalid_request of string
  | Invalid_capability of string
  | Binding_changed of bindings
  | Observation_failed of exn
  | Invalid_result of string
  | Adapter_unsupported of string
  | Adapter_error of exn
type stopped = { receipt : receipt; fault : fault; mutation : mutation_state }
type outcome = Complete of receipt | Stopped of stopped

val execute :
  ?check_cancel:(unit -> unit) ->
  capabilities:capabilities -> expected:bindings -> request:request ->
  observe:(unit -> (bindings, exn) result) ->
  perform:(operation -> adapter_result) ->
  notify:(operation -> prefix -> unit) -> unit -> outcome
(** Validate arithmetic/bounds/capabilities, then re-observe identities, owner,
    backend, generations and sizes before every operation and before completion.
    Missing/mismatched bindings stop without a new mutation; no boolean validity
    assertion is accepted in place of fresh observed binding data.

    Iterate in bounded space: copied head, aligned positive sharing chunks,
    copied tail. Unequal residues or incompatible range constraints select copy.
    A positive [max_bytes] below [alignment] selects copy. Short successful
    prefixes advance exact offsets and cause replanning. [Shared]/[Copied] must
    make positive bounded progress. Shared bytes may only be reported for a
    Share operation, and their count must be a multiple of the range alignment;
    a short Copied prefix may be unaligned. All prefix counts must be nonnegative
    and their sum must fit the operation. Invalid results stop with Indeterminate
    effect, retaining only earlier verified accounting and never notifying the
    invalid claimed prefix. A known-prefix
    [Unsupported] from a sharing call disables sharing for the remainder and
    copies only the suffix. Unsupported copying is terminal. Operational errors,
    indeterminate effects and stale bindings never cause fallback.

    [notify] receives each valid positive completed prefix once, including a
    reported prefix on Unsupported/Error. Its exceptions, [check_cancel]
    exceptions and unexpected raised adapter/observer exceptions propagate
    unchanged; adapters return expected operational failures as typed results.
    A stopped/exceptional candidate must not be published. No receipt bypasses
    final byte verification or the caller's fresh publication identity checks. *)
