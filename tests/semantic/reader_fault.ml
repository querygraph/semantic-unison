external mode : int -> unit = "unison_reader_control_mode"
external calls : unit -> int = "unison_reader_control_calls"
let checks=ref 0
let check value why=incr checks;if not value then failwith why
let () =
 let path=Filename.temp_file "borrowed-reader-control-" ".bin" in
 let data=String.init 128 (fun i -> Char.chr i) in
 let out=open_out_bin path in output_string out data;close_out out;
 let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 Fun.protect ~finally:(fun () -> Unix.close fd;Sys.remove path) (fun () ->
  ignore(Unix.lseek fd 11 Unix.SEEK_SET);
  List.iter(fun setting ->
   mode setting;
   let result=SemanticFile.with_borrowed_fd fd (fun file -> SemanticFile.read file 3L 100) in
   check(result=String.sub data 3 100) "borrowed fault read bytes differ";
   check(calls ()=(if setting=1 then 2 else 15)) "short/EINTR attempt accounting differs";
   check(Unix.lseek fd 0 Unix.SEEK_CUR=11) "borrowed retry changed shared position"
  ) [1;2];
  mode 3;
  check(try SemanticFile.with_borrowed_fd fd (fun file -> ignore(SemanticFile.read file 0L 1));false
    with SemanticFile.Invalid _ -> true) "EOF silently accepted";
  check(calls ()=1) "EOF retried";
  mode 4;
  check(try SemanticFile.with_borrowed_fd fd (fun file -> ignore(SemanticFile.read file 0L 1));false
    with Unix.Unix_error(Unix.EIO,_,_) -> true) "I/O error converted to fallback";
  check(calls ()=1) "I/O error retried";
  mode 5;
  let queries=ref 0 in
  check(try SemanticFile.with_borrowed_fd ~check_cancel:(fun () -> incr queries;if !queries>=8 then raise Exit)
    fd (fun file -> ignore(SemanticFile.read file 0L 1));false with Exit -> true)
    "EINTR loop ignored cancellation";
  check(calls ()>0 && calls ()<8) "EINTR loop did not check bounded cancellation";
  check(Unix.lseek fd 0 Unix.SEEK_CUR=11 && (Unix.fstat fd).Unix.st_size=128)
    "failed borrowed read closed or moved caller descriptor");
 Printf.printf "PASS %d borrowed positional reader fault checks\n%!" !checks
