exception Original_error
let mode=ref "known"
let bindings=ref []
let file_calls=ref [] and directory_calls=ref []
let unlink_calls=ref 0
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let acquired path fd=
 bindings:=(fd,path)::!bindings;
 if List.mem !mode ["temporary-interrupt";"temporary-interrupt-close"] && String.starts_with ~prefix:".base-"(Filename.basename path) then raise Original_error
let kind path=if Filename.basename path=".quota-v1" then "quota" else if String.starts_with ~prefix:".base-"(Filename.basename path) then "temporary" else "read"
let armed ()= !mode<>"known"
let close fd=
 let path=try List.assoc fd !bindings with Not_found->"" in
 let role=if path="" then "other" else kind path in
 if armed() && role<>"other" then file_calls:=role::!file_calls;
 let bad= !mode=role^"-before" || !mode=role^"-after" || (!mode="error-quota-dir" && role="quota") || (!mode="temporary-interrupt-close" && role="temporary") in
 if bad && String.ends_with ~suffix:"-before" !mode then raise(Unix.Unix_error(Unix.EIO,"cache close before kernel",path));
 Unix.close fd;
 if bad then begin Unix.dup2 spare fd;raise(Unix.Unix_error(Unix.EIO,"cache close after kernel/recycle",path)) end
let closedir path handle=
 let role=if Filename.basename path="semantic-merge-bases-v1" then "root" else "shard" in
 if armed() then directory_calls:=role::!directory_calls;
 let ordinal=List.length !directory_calls in
 let bad=(!mode="directory-before" && ordinal=1) || (!mode="directory-after" && ordinal=1) ||
  (!mode="root-after" && role="root") || (!mode="inner-shard-after" && role="shard" && ordinal=2) ||
  (!mode="error-quota-dir" && role="root") in
 if bad && !mode="directory-before" then raise(Unix.Unix_error(Unix.EIO,"cache closedir before kernel",path));
 Unix.closedir handle;
 if bad then raise(Unix.Unix_error(Unix.EIO,"cache closedir after kernel",path))
let unlink path=
 if armed() then incr unlink_calls;
 if !mode="unlink-before" then raise(Unix.Unix_error(Unix.EIO,"cache unlink before kernel",path));
 Unix.unlink path;
 if !mode="unlink-after" then raise(Unix.Unix_error(Unix.EIO,"cache unlink after kernel",path))
let quota_body ()=if !mode="error-quota-dir" then raise Original_error
let before_remove path=
 if !mode="unlink-rebound" && Sys.file_exists path then begin
  Unix.rename path (path^".original");
  let fd=Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL] 0o600 in
  ignore(Unix.write_substring fd "peer sentinel" 0 13);Unix.close fd
 end
