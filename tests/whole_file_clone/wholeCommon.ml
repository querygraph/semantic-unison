let assertions = ref 0
let groups = ref 0
let serial = ref 0
let check condition reason =
  incr assertions;
  if not condition then failwith reason
let test name body =
  (try body () with error -> Printf.eprintf "FAIL %s\n%!" name; raise error);
  incr groups; Printf.printf "PASS %s\n%!" name
let bytes path =
  let channel = open_in_bin path in
  Fun.protect ~finally:(fun () -> close_in channel)
    (fun () -> really_input_string channel (in_channel_length channel))
let write path data =
  let channel = open_out_gen [Open_wronly;Open_creat;Open_excl;Open_binary] 0o640 path in
  Fun.protect ~finally:(fun () -> close_out channel)
    (fun () -> output_string channel data)
let position fd = Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR
let size fd = (Unix.LargeFile.fstat fd).Unix.LargeFile.st_size
let same_object a b =
  let a = Unix.LargeFile.fstat a and b = Unix.LargeFile.fstat b in
  a.Unix.LargeFile.st_dev = b.st_dev && a.st_ino = b.st_ino
let pattern n = String.init n (fun index -> Char.chr ((index * 73 + 19) land 255))
let remove_owned path = try Unix.unlink path with Unix.Unix_error(Unix.ENOENT,_,_) -> ()
type fixture = {
  source_path:string; destination_path:string; live_path:string;
  data:string; source_writer:Unix.file_descr;
  input:in_channel; output:out_channel;
  source_fd:Unix.file_descr; destination_fd:Unix.file_descr;
}
let fixture directory ?(length=8193) body =
  incr serial;
  let name stem = Filename.concat directory (stem ^ string_of_int !serial) in
  let source_path = name "source-" and destination_path = name "output-"
  and live_path = name "live-" in
  let data = pattern length in
  write source_path data; write live_path "PROTECTED LIVE BYTES";
  let source_writer = Unix.openfile source_path [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
  let input = open_in_bin source_path in
  let destination_fd = Unix.openfile destination_path
    [Unix.O_RDWR;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
  let output = Unix.out_channel_of_descr destination_fd in
  let source_fd = Unix.descr_of_in_channel input in
  let f = {source_path;destination_path;live_path;data;source_writer;
           input;output;source_fd;destination_fd} in
  Fun.protect ~finally:(fun () ->
    close_in_noerr input;close_out_noerr output;Unix.close source_writer;
    List.iter remove_owned [source_path;destination_path;live_path])
    (fun () -> body f;
      check (bytes source_path=data) "immutable fixture source bytes changed";
      check (bytes live_path="PROTECTED LIVE BYTES") "live sentinel changed")
let failed body =
  let result = try body (); None with error -> Some error in
  match result with
  | Some error -> error
  | None -> failwith "operation returned despite an injected failure"
let errno expected = function
  | Unix.Unix_error(actual,_,_) -> actual=expected
  | _ -> false
let guarded_fd fd body = Fun.protect ~finally:(fun () -> Unix.close fd) body
