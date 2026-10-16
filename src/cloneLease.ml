type endpoint = Source | Destination
type issue =
  | Owner_closed
  | Owner_invalidated
  | Lease_invalidated
  | Identity_unavailable of endpoint
  | Invalid_observation of endpoint * string
  | Not_regular of endpoint
  | Aliased_objects
  | Source_changed
  | Destination_constraints_changed
exception Invalidated of issue

type owner = { instance_id : string; epoch : int64 option Atomic.t }
type t = {
  owner : owner;
  generation : int64;
  source_fd : Unix.file_descr;
  destination_fd : Unix.file_descr;
  source : FileObservation.t;
  destination : FileObservation.t;
  backend_revision : string;
  expected : CloneRange.bindings;
  observe_fd : Unix.file_descr -> FileObservation.t;
  invalidated : bool Atomic.t;
}

let create_owner ~instance_id =
  if instance_id = "" then invalid_arg "CloneLease: empty owner identity";
  { instance_id; epoch = Atomic.make (Some 0L) }

let close_owner owner = Atomic.set owner.epoch None
let invalidate_owner owner =
  let rec advance () =
    let previous = Atomic.get owner.epoch in
    match previous with
    | None -> ()
    | Some generation ->
        let next = if generation = Int64.max_int then None
          else Some (Int64.succ generation) in
        if not (Atomic.compare_and_set owner.epoch previous next) then advance ()
  in advance ()

let owner_epoch owner = match Atomic.get owner.epoch with
  | None -> raise (Invalidated Owner_closed)
  | Some generation -> generation
let check_epoch owner expected =
  if owner_epoch owner <> expected then raise (Invalidated Owner_invalidated)

let valid_observation endpoint (observation : FileObservation.t) =
  let reject reason = raise (Invalidated (Invalid_observation (endpoint, reason))) in
  if observation.device_id = "" || observation.file_id = "" ||
     observation.filesystem_id = "" then reject "empty native identity";
  if observation.size < 0L || observation.link_count < 0L ||
     observation.file_flags < 0L || observation.mount_flags < 0L then
    reject "negative size, links or flags";
  if observation.mtime_nanoseconds < 0 || observation.mtime_nanoseconds >= 1_000_000_000 ||
     observation.ctime_nanoseconds < 0 || observation.ctime_nanoseconds >= 1_000_000_000 then
    reject "invalid native timestamp fraction";
  if observation.kind <> Unix.S_REG then raise (Invalidated (Not_regular endpoint));
  match observation.volume_uuid with
  | Some identity when identity <> "" -> ()
  | Some _ -> reject "empty volume identity"
  | None -> raise (Invalidated (Identity_unavailable endpoint))

(* Length framing preserves arbitrary full-width future backend identities;
   no truncation or delimiter ambiguity, and no mount-name inference. *)
let volume_id (observation : FileObservation.t) =
  let uuid = match observation.volume_uuid with Some uuid -> uuid | None -> assert false in
  let field text = string_of_int (String.length text) ^ ":" ^ text in
  field uuid ^ field observation.filesystem_id ^ field observation.device_id

let bindings owner generation backend_revision source destination =
  let binding (observation : FileObservation.t) : CloneRange.binding =
    { volume_id = volume_id observation; generation;
      file_id = observation.file_id; size = observation.size } in
  { CloneRange.owner_instance = owner.instance_id; backend_revision;
    source = binding source; destination = binding destination }

let same_native_constraints (before : FileObservation.t) (after : FileObservation.t) =
  before.kind = after.kind && before.link_count = after.link_count &&
  before.file_flags = after.file_flags && before.mount_flags = after.mount_flags
let same_source_stamp (before : FileObservation.t) (after : FileObservation.t) =
  before.mtime_seconds = after.mtime_seconds && before.mtime_nanoseconds = after.mtime_nanoseconds &&
  before.ctime_seconds = after.ctime_seconds && before.ctime_nanoseconds = after.ctime_nanoseconds

let enroll ?(observe = FileObservation.observe) owner ~backend_revision ~source ~destination =
  try
    if backend_revision = "" then invalid_arg "CloneLease: empty backend revision";
    let generation = owner_epoch owner in
    let source_observation = observe source in
    let destination_observation = observe destination in
    check_epoch owner generation;
    valid_observation Source source_observation;
    valid_observation Destination destination_observation;
    let expected = bindings owner generation backend_revision source_observation destination_observation in
    if expected.source.volume_id = expected.destination.volume_id &&
       expected.source.file_id = expected.destination.file_id then
      raise (Invalidated Aliased_objects);
    Ok { owner; generation; source_fd = source; destination_fd = destination;
         source = source_observation; destination = destination_observation;
         backend_revision; expected; observe_fd = observe;
         invalidated = Atomic.make false }
  with error -> Error error

let expected lease = lease.expected
let invalidate lease = Atomic.set lease.invalidated true
let check_lease lease =
  if Atomic.get lease.invalidated then raise (Invalidated Lease_invalidated);
  check_epoch lease.owner lease.generation

let observe lease =
  try
    check_lease lease;
    let source = lease.observe_fd lease.source_fd in
    let destination = lease.observe_fd lease.destination_fd in
    check_lease lease;
    valid_observation Source source;
    valid_observation Destination destination;
    let current = bindings lease.owner lease.generation lease.backend_revision source destination in
    (* Return actually observed binding changes to the executor. Native fields
       not represented in CloneRange bindings have their own failure channel. *)
    if current = lease.expected then begin
      if not (same_native_constraints lease.source source) ||
         not (same_source_stamp lease.source source) then raise (Invalidated Source_changed);
      if not (same_native_constraints lease.destination destination) then
        raise (Invalidated Destination_constraints_changed)
    end;
    Ok current
  with error -> Error error

let execute ?check_cancel lease ~capabilities ~request ~perform ~notify () =
  CloneRange.execute ?check_cancel ~capabilities ~expected:lease.expected ~request
    ~observe:(fun () -> observe lease)
    ~perform:(fun operation -> perform ~source:lease.source_fd
      ~destination:lease.destination_fd operation) ~notify ()
