type endpoint = {
  mutable fd:Unix.file_descr;
  mutable owned:bool;
  mutable attempted:bool;
  mutable settled:bool;
  mutable error:exn;
  mutable identity:Unix.LargeFile.stats option;
  mutable identity_error:exn;
  mutable identity_failed:bool;
}
type t = {
  read:endpoint;
  write:endpoint;
  mutable reader:Lwt_unix.file_descr option;
  mutable owner:unit -> unit;
  mutable operation_error:exn;
  mutable operation_failed:bool;
  mutable retained:bool;
  mutable lifecycle_error:exn;
  mutable lifecycle_failed:bool;
  mutable previous:t option;
  link:t option;
  carrier:exn;
  read_close:unit -> unit;
  write_close:unit -> unit;
}
exception Uncertain of t
let roots=ref None
let count=ref 0
let retained_count () = !count
let prepare () =
  let endpoint ()={fd=Unix.stdin;owned=false;attempted=false;settled=false;error=Exit;identity=None;identity_error=Exit;identity_failed=false} in
  let read=endpoint () and write=endpoint () in
  let rec t={read;write;reader=None;owner=(fun () -> ());
    operation_error=Exit;operation_failed=false;retained=false;lifecycle_error=Exit;lifecycle_failed=false;
    previous=None;link=Some t;carrier=Uncertain t;
    read_close=(fun () -> match t.reader with
      | Some reader -> Lwt_unix.close reader
      | None -> Unix.close t.read.fd);
    write_close=(fun () -> Unix.close t.write.fd)} in
  t
let adopt t read write =
  if t.read.owned || t.write.owned then invalid_arg "notification pipe already adopted";
  t.read.fd <- read;t.write.fd <- write;
  t.read.owned <- true;t.write.owned <- true
let install_reader t reader =
  if not t.read.owned || t.read.attempted || t.reader<>None then
    invalid_arg "notification reader installation state";
  t.reader <- Some reader
let keep_owner t owner = t.owner <- owner
let remember_failure t error =
  if error != t.carrier && not t.operation_failed then begin
    t.operation_error <- error;t.operation_failed <- true
  end
let retain t =
  if not t.retained then begin
    t.previous <- !roots;roots := t.link;t.retained <- true;
    if !count<max_int then incr count
  end
let close_endpoint t endpoint close =
  if endpoint.owned && not endpoint.attempted then begin
    endpoint.attempted <- true;
    (try endpoint.identity <- Some (Unix.LargeFile.fstat endpoint.fd)
     with error -> endpoint.identity_error <- error;endpoint.identity_failed <- true);
    try close ();endpoint.settled <- true
    with error -> endpoint.error <- error;retain t
  end;
  if endpoint.owned && not endpoint.settled then raise t.carrier
let close_read t =
  close_endpoint t t.read t.read_close
let close_write t = close_endpoint t t.write t.write_close
let close_all t =
  (try close_read t with Uncertain _ -> ());
  (try close_write t with Uncertain _ -> ());
  if t.retained then raise t.carrier
let settled t =
  (not t.read.owned || t.read.settled) && (not t.write.owned || t.write.settled)
let cause endpoint = if endpoint.owned && endpoint.attempted && not endpoint.settled then Some endpoint.error else None
let read_cause t = cause t.read
let write_cause t = cause t.write
let operation_cause t = if t.operation_failed then Some t.operation_error else None
let descriptors t = t.read.fd,t.write.fd

let read_identity t = t.read.identity
let write_identity t = t.write.identity
let identity_error endpoint = if endpoint.identity_failed then Some endpoint.identity_error else None
let read_identity_error t = identity_error t.read
let write_identity_error t = identity_error t.write

let retain_unsettled t error =
  if error != t.carrier && not t.lifecycle_failed then begin
    t.lifecycle_error <- error;t.lifecycle_failed <- true
  end;
  retain t;
  raise t.carrier
let lifecycle_cause t = if t.lifecycle_failed then Some t.lifecycle_error else None
