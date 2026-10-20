let () =
  let path="original64.bin" in
  let data=String.init 64 Char.chr in
  let ch=open_out_bin path in output_string ch data;close_out ch;
  let fd=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let baseline=Array.length(Sys.readdir "/dev/fd") in
  Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
    let digest,stats=SemanticFile.with_read_stats ~measure_stages:true fd (fun input ->
      let digest=SemanticFile.digest input in
      let marker=SemanticFile.measure input SemanticFile.Parse (fun () -> "unchanged") in
      if marker<>"unchanged" then failwith "clock changed callback value";
      digest) in
    if digest<>SemanticHash.string data || stats.logical_bytes<>64L || stats.chunks<>1L ||
       stats.stages<>None then failwith "invalid clock fabricated timing or changed hash";
    if (Unix.LargeFile.fstat fd).st_size<>64L ||
       Array.length(Sys.readdir "/dev/fd")<>baseline then failwith "clock fault changed FD ownership");
  print_endline "PASS invalid clock yields unavailable stages, exact bytes and settled reader"
