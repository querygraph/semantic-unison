module D=DngComponents
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let ()=
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let path=Filename.temp_file "component-source-posix-" "" in
 let out=open_out_bin path in output_string out "original source fixture";close_out out;
 let open_source ()=D.open_component_source(fun () -> Unix.openfile path
  [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0) in
 let source=open_source () in let fd=D.component_source_descriptor source in
 check((Unix.fstat fd).Unix.st_kind=Unix.S_REG) "source not regular";
 D.settle_component_source source None;
 check((try ignore(Unix.fstat fd);false with Unix.Unix_error(Unix.EBADF,_,_)->true))
  "source not closed through non-Apple POSIX path";
 check((try D.settle_component_source source None;false with ComponentHash.Invalid _->true))
  "settled source retried";
 let source=open_source () in let original=Failure "original operation" in
 check((try D.settle_component_source source (Some original);false with error -> error==original))
  "normal error cleanup changed cause";
 let directory=Filename.temp_file "component-source-directory-" "" in
 Sys.remove directory;Unix.mkdir directory 0o700;
 check((try ignore(D.open_component_source(fun () -> Unix.openfile directory
  [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0));false with ComponentHash.Invalid _->true))
  "source directory validation did not close/reject";
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "portable source owner leaked descriptor";
 Printf.printf "PASS %d non-Apple-guard source owner checks (Darwin-host conditional build)\n%!" !checks
