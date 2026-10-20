exception Original_error
let mode=ref "known"
let armed=ref false
let target_path=ref ""
let target : Unix.dir_handle option ref=ref None
let replacements=ref []
let opens=ref 0 and closes=ref 0 and reads=ref 0
let cancel=ref(fun () -> ())
let is_target handle=match !target with Some other->handle==other | None->false
let before_wrapper ()=if !armed && !mode="wrapper" then raise Original_error
let open_directory path =
 if !armed && path= !target_path then begin
  incr opens;
  if !mode="open-error" then raise(Unix.Unix_error(Unix.ENOENT,"injected opendir",path));
  let handle=Unix.opendir path in target:=Some handle;handle
 end else Unix.opendir path
let before_publish ()=
 if !armed && List.mem !mode ["publish";"publish-after"] then raise Original_error
let read handle =
 if !armed && is_target handle then begin
  incr reads;
  if List.mem !mode ["read-error";"read-before";"read-after"] then raise Original_error;
  let value=Unix.readdir handle in
  if !mode="cancel" || !mode="cancel-before" then !cancel ();
  value
 end else Unix.readdir handle
let close handle =
 if !armed && is_target handle then begin
  incr closes;
  if List.mem !mode ["close-before";"read-before";"cancel-before";"legacy-close"] then
   raise(Unix.Unix_error(Unix.EIO,"closedir before settlement",!target_path));
  Unix.closedir handle;
  if List.mem !mode ["close-after";"read-after";"publish-after"] then begin
   replacements:=Unix.opendir !target_path :: !replacements;
   raise(Unix.Unix_error(Unix.EIO,"closedir after settlement",!target_path))
  end
 end else Unix.closedir handle
let readable handle =
 try ignore(Unix.readdir handle);true with End_of_file->true | Unix.Unix_error _->false
