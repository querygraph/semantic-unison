(* unison-dngscan: read-only survey of DNG files against the built-in merge.

   Walks the given paths, and for every *.dng file runs the same inspectors the
   merge uses: dng-xmp /0, /1 and the merge-only /2, then an identity XmpMerge of
   the embedded packet at its fixed length. A file that passes both can take a
   built-in merge. For any other file the /2 grammar is walked once more to list
   every field it does not know, not just the first. Files are opened read-only
   and only their TIFF directories and XMP packet are read; nothing is written
   under the scanned paths. Work is sharded over forked worker processes. *)

type verdict = Mergeable | Xmp_unsupported of string | Declined of string | Error of string

type record = {
  path : string; size : int64;
  v0 : bool; v1 : bool; v2 : bool; verdict : verdict;
  unknown : (string * int * int * int64) list;
}

let usage = "usage: unison-dngscan [-j WORKERS] [-o REPORT.jsonl] PATH..."

let is_dng name =
  String.lowercase_ascii (Filename.extension name) = ".dng"

(* Depth-first, no symlinks followed, unreadable directories reported. *)
let walk roots =
  let files = ref [] and walk_errors = ref [] in
  let rec visit path =
    match Unix.LargeFile.lstat path with
    | exception Unix.Unix_error (e, _, _) -> walk_errors := (path, Unix.error_message e) :: !walk_errors
    | {Unix.LargeFile.st_kind = Unix.S_REG; _} -> if is_dng path then files := path :: !files
    | {Unix.LargeFile.st_kind = Unix.S_DIR; _} ->
        (match Unix.opendir path with
         | exception Unix.Unix_error (e, _, _) -> walk_errors := (path, Unix.error_message e) :: !walk_errors
         | dir ->
             let names = ref [] in
             (try while true do
                let name = Unix.readdir dir in
                if name <> "." && name <> ".." then names := name :: !names
              done with End_of_file -> ());
             Unix.closedir dir;
             List.iter (fun name -> visit (Filename.concat path name)) (List.sort compare !names))
    | _ -> () in
  List.iter visit roots;
  Array.of_list (List.rev !files), List.rev !walk_errors

let read_packet file (region : FormatExtension.region) =
  let buffer = Buffer.create region.length in
  let rec loop at left =
    if left > 0 then begin
      let n = min left 1048576 in
      Buffer.add_string buffer (SemanticFile.read file at n);
      loop (Int64.add at (Int64.of_int n)) (left - n)
    end in
  loop region.offset region.length;
  Buffer.contents buffer

let ok = function Ok _ -> true | Result.Error _ -> false

let inspect path =
  let blank = {path; size = 0L; v0 = false; v1 = false; v2 = false;
               verdict = Error ""; unknown = []} in
  match Unix.openfile path [Unix.O_RDONLY; Unix.O_CLOEXEC] 0 with
  | exception Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)}
  | fd ->
      Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
        try
          SemanticFile.with_borrowed_fd fd (fun file ->
            let size = SemanticFile.size file in
            let v0 = ok (DngSemantic.inspect file) and v1 = ok (DngSemantic.inspect_extended file) in
            match DngSemantic.inspect_opaque_maker file with
            | Ok {FormatExtension.regions = [region]} ->
                let packet = read_packet file region in
                let verdict = match XmpMerge.merge ~base:packet ~left:packet ~right:packet with
                  | Ok merged when String.length merged = String.length packet -> Mergeable
                  | Ok _ -> Xmp_unsupported "identity merge changes packet length"
                  | Result.Error reason -> Xmp_unsupported reason in
                {blank with size; v0; v1; v2 = true; verdict}
            | Ok _ -> {blank with size; v0; v1; v2 = true; verdict = Xmp_unsupported "not one XMP region"}
            | Result.Error reason ->
                let unknown, _ = DngSemantic.unknown_fields file in
                {blank with size; v0; v1; verdict = Declined reason; unknown})
        with
        | SemanticFile.Invalid reason -> {blank with verdict = Error reason}
        | Unix.Unix_error (e, _, _) -> {blank with verdict = Error (Unix.error_message e)})

(* Worker k takes files k, k+workers, ... and marshals one record per file. *)
let run_worker files workers k out =
  let channel = Unix.out_channel_of_descr out in
  let total = (Array.length files - k + workers - 1) / workers in
  let done_ = ref 0 in
  let i = ref k in
  while !i < Array.length files do
    Marshal.to_channel channel (inspect files.(!i) : record) [];
    flush channel;
    incr done_;
    if !done_ mod 2000 = 0 then
      Printf.eprintf "dngscan: worker %d: %d/%d\n%!" k !done_ total;
    i := !i + workers
  done;
  close_out channel

let json_string s =
  let b = Buffer.create (String.length s + 2) in
  Buffer.add_char b '"';
  String.iter (fun c -> match c with
    | '"' -> Buffer.add_string b "\\\"" | '\\' -> Buffer.add_string b "\\\\"
    | '\n' -> Buffer.add_string b "\\n" | '\t' -> Buffer.add_string b "\\t"
    | c when Char.code c < 0x20 -> Buffer.add_string b (Printf.sprintf "\\u%04x" (Char.code c))
    | c -> Buffer.add_char b c) s;
  Buffer.add_char b '"';
  Buffer.contents b

let verdict_fields = function
  | Mergeable -> "mergeable", ""
  | Xmp_unsupported r -> "xmp-unsupported", r
  | Declined r -> "declined", r
  | Error r -> "error", r

let json r =
  let kind, reason = verdict_fields r.verdict in
  Printf.sprintf "{\"path\":%s,\"size\":%Ld,\"dng-xmp/0\":%b,\"dng-xmp/1\":%b,\"dng-xmp/2\":%b,\"verdict\":%s,\"reason\":%s,\"unknown\":[%s]}"
    (json_string r.path) r.size r.v0 r.v1 r.v2 (json_string kind) (json_string reason)
    (String.concat "," (List.map (fun (d, tag, typ, n) ->
       Printf.sprintf "{\"ifd\":%s,\"tag\":%d,\"type\":%d,\"count\":%Ld}" (json_string d) tag typ n) r.unknown))

let bump table key example =
  match Hashtbl.find_opt table key with
  | Some (n, e) -> Hashtbl.replace table key (n + 1, e)
  | None -> Hashtbl.replace table key (1, example)

let sorted table =
  List.sort (fun (k, (a, _)) (k', (b, _)) -> compare (b, k) (a, k')) (Hashtbl.fold (fun k v l -> (k, v) :: l) table [])

let () =
  let workers = ref 8 and report = ref "" and roots = ref [] in
  Arg.parse [
    "-j", Arg.Set_int workers, "N  worker processes (default 8)";
    "-o", Arg.Set_string report, "FILE  write one JSON line per DNG";
  ] (fun p -> roots := p :: !roots) usage;
  if !roots = [] || !workers < 1 || !workers > 64 then (prerr_endline usage; exit 2);
  let started = Unix.gettimeofday () in
  let files, walk_errors = walk (List.rev !roots) in
  Printf.eprintf "dngscan: %d DNG files found in %.0fs; scanning with %d workers\n%!"
    (Array.length files) (Unix.gettimeofday () -. started) !workers;
  let workers = max 1 (min !workers (Array.length files)) in
  let children = List.init workers (fun k ->
    let input, output = Unix.pipe ~cloexec:true () in
    match Unix.fork () with
    | 0 -> Unix.close input; run_worker files workers k output; Unix._exit 0
    | pid -> Unix.close output; pid, Unix.in_channel_of_descr input) in
  (* Records arrive in any order and carry their path; a pipe at EOF is retired. *)
  let collected = ref [] in
  let pending = ref (List.map snd children) in
  while !pending <> [] do
    let ready, _, _ = Unix.select (List.map Unix.descr_of_in_channel !pending) [] [] (-1.) in
    pending := List.filter (fun ch ->
      if not (List.mem (Unix.descr_of_in_channel ch) ready) then true else
      match (Marshal.from_channel ch : record) with
      | r -> collected := r :: !collected; true
      | exception End_of_file -> close_in ch; false) !pending
  done;
  let results = List.sort (fun a b -> compare a.path b.path) !collected in
  let missing = Array.length files - List.length results in
  let failed_workers = List.filter (fun (pid, _) -> match Unix.waitpid [] pid with
    | _, Unix.WEXITED 0 -> false | _ -> true) children in
  let out = if !report = "" then None else Some (open_out_bin !report) in
  let verdicts = Hashtbl.create 8 and reasons = Hashtbl.create 32 and unknown = Hashtbl.create 64 in
  let profiles = Array.make 3 0 and bytes = ref 0L in
  List.iter (fun r ->
        Option.iter (fun ch -> output_string ch (json r); output_char ch '\n') out;
        bytes := Int64.add !bytes r.size;
        if r.v0 then profiles.(0) <- profiles.(0) + 1;
        if r.v1 then profiles.(1) <- profiles.(1) + 1;
        if r.v2 then profiles.(2) <- profiles.(2) + 1;
        let kind, reason = verdict_fields r.verdict in
        bump verdicts kind r.path;
        if reason <> "" then bump reasons (kind ^ ": " ^ reason) r.path;
        List.iter (fun (d, tag, typ, n) ->
          bump unknown (Printf.sprintf "%s tag %d type %d count %s" d tag typ
            (if n = 1L then "1" else "n")) r.path)
          (List.sort_uniq compare (List.map (fun (d, t, ty, n) -> d, t, ty, if n = 1L then 1L else 2L) r.unknown)))
    results;
  Option.iter close_out out;
  Printf.printf "DNG files: %d (%.1f GiB) in %.0fs\n" (Array.length files)
    (Int64.to_float !bytes /. 1073741824.) (Unix.gettimeofday () -. started);
  Printf.printf "accepted by inspector: dng-xmp/0 %d, /1 %d, /2 %d\n" profiles.(0) profiles.(1) profiles.(2);
  Printf.printf "\nverdicts:\n";
  List.iter (fun (k, (n, _)) -> Printf.printf "  %8d  %s\n" n k) (sorted verdicts);
  if Hashtbl.length reasons > 0 then begin
    Printf.printf "\nreasons (first stop of the real inspector or XMP merge):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted reasons)
  end;
  if Hashtbl.length unknown > 0 then begin
    Printf.printf "\nfields outside dng-xmp/2 (files containing each):\n";
    List.iter (fun (k, (n, e)) -> Printf.printf "  %8d  %s\n            e.g. %s\n" n k e) (sorted unknown)
  end;
  if walk_errors <> [] then begin
    Printf.printf "\nunreadable paths: %d\n" (List.length walk_errors);
    List.iter (fun (p, e) -> Printf.printf "  %s: %s\n" p e) walk_errors
  end;
  if missing > 0 || failed_workers <> [] then
    Printf.printf "\nINCOMPLETE: %d files without a result, %d workers failed\n" missing (List.length failed_workers);
  let all_mergeable = Hashtbl.length verdicts = 1 && Hashtbl.mem verdicts "mergeable" in
  exit (if missing > 0 || failed_workers <> [] || walk_errors <> [] then 2
        else if all_mergeable then 0 else 1)
