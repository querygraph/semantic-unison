exception Original_error
let mode=ref "known"
let fds=Array.make 4 Unix.stdin
let seen=Array.make 4 false
let calls=Array.make 4 0
let spare=Unix.openfile "/dev/null" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let acquired index fd=fds.(index)<-fd;seen.(index)<-true
let close fd =
 let index=ref (-1) in
 for i=0 to 3 do if seen.(i) && fd=fds.(i) then index:=i done;
 if !index<0 then Unix.close fd else begin
  let i= !index in calls.(i)<-calls.(i)+1;
  let fail= !mode="all" || !mode="error-all" || !mode="before-all" || !mode="slot"^string_of_int i in
  if fail && !mode="before-all" then raise(Unix.Unix_error(Unix.EIO,"input close before kernel",""));
  Unix.close fd;
  if fail then begin Unix.dup2 spare fd;raise(Unix.Unix_error(Unix.EIO,"input close after kernel/recycle","")) end
 end
