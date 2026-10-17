open Lwt
type retained = {
  mutable fd:Unix.file_descr; mutable owned:bool; mutable uncertain:bool;
  mutable before:Unix.LargeFile.stats option; mutable error:exn;
  mutable original:exn option;
  mutable observation_failed:bool; mutable observation_error:exn; mutable linked:bool;
  mutable self:retained option; mutable previous:retained option; mutable next:retained option;
}
let owners=ref None
let descriptor t=t.fd
let before_close t=t.before
let close_error t=t.error
let original_failure t=t.original
let retained () =
  let rec collect result=function None -> List.rev result
    | Some t -> collect (if t.uncertain then t::result else result) t.next in
  collect [] !owners
let unlink t =
  if t.linked then begin
    t.linked<-false;
    (match t.previous with None -> owners:=t.next | Some p -> p.next<-t.next);
    (match t.next with None -> () | Some n -> n.previous<-t.previous);
    t.previous<-None;t.next<-None
  end
let with_file ?(close=Unix.close) path operation =
  let pending=Lwt.wait () in
  let owner={fd=Unix.stdin;owned=false;uncertain=false;before=None;error=Exit;
    original=None;self=None;previous=None;next=None;
    observation_failed=false;observation_error=Exit;linked=false} in
  owner.self<-Some owner;
  let finish failure =
    if owner.original=None then owner.original<-failure;
    if owner.owned then begin
      owner.owned<-false;
      (try owner.before<-Some (Unix.LargeFile.fstat owner.fd)
       with error -> owner.observation_failed<-true;owner.observation_error<-error);
      (try close owner.fd
       with error -> owner.uncertain<-true;owner.error<-error)
    end;
    if owner.uncertain then pending else begin
      unlink owner;
      match failure with
      | Some error -> fail error
      | None when owner.observation_failed -> fail owner.observation_error
      | None -> return ()
    end in
  (* All ownership nodes and the pending return exist before acquiring the FD.
     Removal mutates links without allocating after a known close. *)
  owner.next<- !owners;
  (match !owners with None -> () | Some n -> n.previous<-owner.self);
  owners:=owner.self;
  owner.linked<-true;
  try
    let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_NONBLOCK;Unix.O_CLOEXEC] 0 in
    owner.fd<-fd;owner.owned<-true;
    BorrowedWork.try_bind (fun () -> operation fd)
      (fun value ->
        BorrowedWork.bind (fun () -> finish None) (fun () -> return value))
      (fun error -> BorrowedWork.bind (fun () -> finish (Some error)) (fun () -> assert false))
  with error ->
    BorrowedWork.bind (fun () -> finish (Some error)) (fun () -> assert false)
