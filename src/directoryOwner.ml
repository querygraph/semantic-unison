type phase = Empty | Opening | Held | Close_uncertain | Closed | Open_failed
type t = {
  mutable phase:phase;
  mutable handle:Obj.t;
  mutable path:string;
  mutable operation_error:exn;
  mutable operation_failed:bool;
  mutable close_error:exn;
  mutable linked:bool;
  mutable previous:t option;
  mutable next:t option;
  link:t option;
  carrier:exn;
}
exception Uncertain of t
let owners=ref None
let prepare () =
  let rec owner={phase=Empty;handle=Obj.repr ();path="";
    operation_error=Exit;operation_failed=false;close_error=Exit;
    linked=false;previous=None;next=None;link=Some owner;carrier=Uncertain owner} in
  owner
let unlink owner =
  if owner.linked then begin
    (match owner.previous with None -> owners:=owner.next | Some p -> p.next<-owner.next);
    (match owner.next with None -> () | Some n -> n.previous<-owner.previous);
    owner.previous<-None;owner.next<-None;owner.linked<-false
  end
let remember_failure owner error =
  if error != owner.carrier && not owner.operation_failed then begin
    owner.operation_error<-error;owner.operation_failed<-true
  end
let close owner =
  if owner.phase=Held then begin
    (* Mark attempted before invoking the opaque close. Never retry a historic
       directory object, including after an error following kernel settlement. *)
    owner.phase<-Close_uncertain;
    try Unix.closedir (Obj.obj owner.handle : Unix.dir_handle);
      owner.phase<-Closed;owner.handle<-Obj.repr ();unlink owner
    with error -> owner.close_error<-error
  end;
  if owner.phase=Close_uncertain then raise owner.carrier
let open_with owner path publish =
  if owner.phase<>Empty then invalid_arg "directory owner already used";
  owner.path<-path;
  owner.next<- !owners;
  (match !owners with None -> () | Some p -> p.previous<-owner.link);
  owners:=owner.link;owner.linked<-true;owner.phase<-Opening;
  (try
     let handle=Unix.opendir path in
     (* Only this typed store writes the monomorphic GC-root slot. The empty
        placeholder is never interpreted as a directory handle. *)
     owner.handle<-Obj.repr handle;owner.phase<-Held
   with error -> owner.phase<-Open_failed;unlink owner;raise error);
  try publish () with error ->
    remember_failure owner error;close owner;raise error
let read owner =
  match owner.phase with
  | Held -> Unix.readdir (Obj.obj owner.handle : Unix.dir_handle)
  | Close_uncertain -> raise owner.carrier
  | _ -> invalid_arg "directory is not open"
let phase owner=owner.phase
let path owner=owner.path
let operation_cause owner=if owner.operation_failed then Some owner.operation_error else None
let close_cause owner=if owner.phase=Close_uncertain then Some owner.close_error else None
let iter_retained f =
  let rec loop=function None -> () | Some owner ->
    if owner.phase=Close_uncertain then f owner;
    loop owner.next in
  loop !owners
let retained_count () =let n=ref 0 in iter_retained(fun _ -> incr n);!n
