type t = {
  max_files:int; max_path_bytes:int; names:(string,unit) Hashtbl.t;
  mutable reversed:Path.local list; mutable bytes:int;
  mutable failure:string option;
}
exception Limit_exceeded of string
let create ~max_files ~max_path_bytes =
  if max_files<1 || max_path_bytes<1 then invalid_arg "ValidationPaths limits";
  {max_files;max_path_bytes;names=Hashtbl.create (min max_files 256);
   reversed=[];bytes=0;failure=None}
let check t=match t.failure with None -> () | Some reason -> raise (Limit_exceeded reason)
let refuse t reason=t.failure<-Some reason;raise (Limit_exceeded reason)
let add t path =
  check t;
  let name=Path.toString path in
  if not (Hashtbl.mem t.names name) then begin
    if Hashtbl.length t.names>=t.max_files then refuse t "validation selected-file limit exceeded";
    if String.length name>t.max_path_bytes-t.bytes then refuse t "validation pathname-byte limit exceeded";
    Hashtbl.add t.names name ();t.bytes<-t.bytes+String.length name;
    t.reversed<-path::t.reversed
  end
let paths t=check t;List.rev t.reversed
