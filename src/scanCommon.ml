(* Shared by the scan and -semdiff modes of unison-dngscan: the directory walk
   with its listing cache, the forked worker pool, and a small JSON reader and
   writer for report lines and exiftool-rs records. *)

(* A directory's cached listing: its subdirectories and the regular files kept
   by the walk's filter. Adding, removing or renaming an entry changes the
   directory's mtime, so the listing is reused only while device, inode and
   mtime are all unchanged. *)
type listing = { dev : int; ino : int; mtime : float; subdirs : string list; files : string list }

let load_cache format path =
  try
    let ch = open_in_bin path in
    Fun.protect ~finally:(fun () -> close_in ch) (fun () ->
      match (Marshal.from_channel ch : string * (string, listing) Hashtbl.t) with
      | f, table when f = format -> table
      | _ -> Hashtbl.create 0)
  with Sys_error _ | End_of_file | Failure _ -> Hashtbl.create 0

let save_cache format path table =
  let temp = path ^ ".tmp" in
  let ch = open_out_bin temp in
  Marshal.to_channel ch (format, table) [];
  close_out ch;
  Sys.rename temp path

(* Depth-first, no symlinks followed, unreadable directories reported. With a
   cache, unchanged directories are listed from it without reading their entries.
   A directory modified in the last few seconds, or with an unreadable entry, is
   not cached. [format] names the cache layout and the filter, so caches kept
   with different filters never mix. Returns the files, the errors, and
   directories (listed, reused). *)
let walk ?cache ~format ~keep roots =
  let old = match cache with Some path -> load_cache format path | None -> Hashtbl.create 0 in
  let fresh = Hashtbl.create (max 16 (Hashtbl.length old)) in
  let now = Unix.gettimeofday () in
  let files = ref [] and walk_errors = ref [] and listed = ref 0 and reused = ref 0 in
  let error path e = walk_errors := (path, Unix.error_message e) :: !walk_errors in
  let rec visit path =
    match Unix.LargeFile.lstat path with
    | exception Unix.Unix_error (e, _, _) -> error path e
    | {Unix.LargeFile.st_kind = Unix.S_REG; _} -> if keep (Filename.basename path) then files := path :: !files
    | {Unix.LargeFile.st_kind = Unix.S_DIR; st_dev; st_ino; st_mtime; _} ->
        let listing = match Hashtbl.find_opt old path with
          | Some l when l.dev = st_dev && l.ino = st_ino && l.mtime = st_mtime -> incr reused; Some l
          | _ -> list path st_dev st_ino st_mtime in
        Option.iter (fun l ->
          if cache <> None then Hashtbl.replace fresh path l;
          List.iter (fun name -> files := Filename.concat path name :: !files) l.files;
          List.iter (fun name -> visit (Filename.concat path name)) l.subdirs) listing
    | _ -> ()
  and list path dev ino mtime =
    match Unix.opendir path with
    | exception Unix.Unix_error (e, _, _) -> error path e; None
    | dir ->
        incr listed;
        let names = ref [] in
        (try while true do
           let name = Unix.readdir dir in
           if name <> "." && name <> ".." then names := name :: !names
         done with End_of_file -> ());
        Unix.closedir dir;
        let subdirs = ref [] and kept = ref [] and complete = ref true in
        List.iter (fun name ->
          let child = Filename.concat path name in
          match Unix.LargeFile.lstat child with
          | exception Unix.Unix_error (e, _, _) -> error child e; complete := false
          | {Unix.LargeFile.st_kind = Unix.S_DIR; _} -> subdirs := name :: !subdirs
          | {Unix.LargeFile.st_kind = Unix.S_REG; _} when keep name -> kept := name :: !kept
          | _ -> ()) (List.sort compare !names);
        let l = {dev; ino; mtime; subdirs = List.rev !subdirs; files = List.rev !kept} in
        if !complete && mtime < now -. 5. then Some l
        else begin
          (* Still walked now, but left out of the cache. *)
          List.iter (fun name -> files := Filename.concat path name :: !files) l.files;
          List.iter (fun name -> visit (Filename.concat path name)) l.subdirs;
          None
        end in
  List.iter visit roots;
  Option.iter (fun path -> save_cache format path fresh) cache;
  Array.of_list (List.rev !files), List.rev !walk_errors, (!listed, !reused)

(* Worker k takes items k, k+workers, ... and marshals one result per item; the
   parent hands results to [on_result] as they arrive, in any order, and prints
   progress every 30 seconds. Returns the number of workers that failed. *)
let run_pool ~label ~workers items job on_result =
  let workers = max 1 (min workers (Array.length items)) in
  if Array.length items = 0 then 0 else begin
    let children = List.init workers (fun k ->
      let input, output = Unix.pipe ~cloexec:true () in
      match Unix.fork () with
      | 0 ->
          Unix.close input;
          let channel = Unix.out_channel_of_descr output in
          let i = ref k in
          while !i < Array.length items do
            Marshal.to_channel channel (job items.(!i)) [];
            flush channel;
            i := !i + workers
          done;
          close_out channel;
          Unix._exit 0
      | pid -> Unix.close output; pid, Unix.in_channel_of_descr input) in
    let received = ref 0 and last = ref (Unix.gettimeofday ()) in
    let started = !last in
    let pending = ref (List.map snd children) in
    while !pending <> [] do
      let ready, _, _ = Unix.select (List.map Unix.descr_of_in_channel !pending) [] [] (-1.) in
      pending := List.filter (fun ch ->
        if not (List.mem (Unix.descr_of_in_channel ch) ready) then true else
        match Marshal.from_channel ch with
        | r ->
            on_result r; incr received;
            let now = Unix.gettimeofday () in
            if now -. !last >= 30. then begin
              last := now;
              let rate = float !received /. (now -. started) in
              Printf.eprintf "%s: %d/%d files, %.0f/s, about %.0f min left\n%!" label !received
                (Array.length items) rate (float (Array.length items - !received) /. rate /. 60.)
            end;
            true
        | exception End_of_file -> close_in ch; false) !pending
    done;
    List.length (List.filter (fun (pid, _) -> match Unix.waitpid [] pid with
      | _, Unix.WEXITED 0 -> false | _ -> true) children)
  end

(* JSON. Numbers keep their source text, so values copied from an exiftool-rs
   record are written back unchanged. *)
type json = Null | Bool of bool | Num of string | Str of string | Arr of json list | Obj of (string * json) list

exception Bad_json

let utf8 b code =
  let add n = Buffer.add_char b (Char.chr n) in
  if code < 0x80 then add code
  else if code < 0x800 then (add (0xc0 lor (code lsr 6)); add (0x80 lor (code land 0x3f)))
  else if code < 0x10000 then
    (add (0xe0 lor (code lsr 12)); add (0x80 lor ((code lsr 6) land 0x3f)); add (0x80 lor (code land 0x3f)))
  else
    (add (0xf0 lor (code lsr 18)); add (0x80 lor ((code lsr 12) land 0x3f));
     add (0x80 lor ((code lsr 6) land 0x3f)); add (0x80 lor (code land 0x3f)))

let parse text =
  let i = ref 0 and n = String.length text in
  let peek () = if !i < n then text.[!i] else raise Bad_json in
  let skip () = while !i < n && (match text.[!i] with ' ' | '\t' | '\n' | '\r' -> true | _ -> false) do incr i done in
  let expect c = skip (); if peek () <> c then raise Bad_json; incr i in
  let literal word v =
    if !i + String.length word <= n && String.sub text !i (String.length word) = word
    then (i := !i + String.length word; v) else raise Bad_json in
  let hex4 () =
    if !i + 4 > n then raise Bad_json;
    let v = try int_of_string ("0x" ^ String.sub text !i 4) with Failure _ -> raise Bad_json in
    i := !i + 4; v in
  let string () =
    expect '"';
    let b = Buffer.create 32 in
    let rec loop () = match peek () with
      | '"' -> incr i
      | '\\' ->
          incr i;
          let c = peek () in incr i;
          (match c with
           | '"' | '\\' | '/' -> Buffer.add_char b c
           | 'b' -> Buffer.add_char b '\b' | 'f' -> Buffer.add_char b '\012'
           | 'n' -> Buffer.add_char b '\n' | 'r' -> Buffer.add_char b '\r' | 't' -> Buffer.add_char b '\t'
           | 'u' ->
               let hi = hex4 () in
               if hi >= 0xd800 && hi < 0xdc00 && !i + 6 <= n && text.[!i] = '\\' && text.[!i + 1] = 'u' then begin
                 i := !i + 2;
                 let lo = hex4 () in
                 if lo >= 0xdc00 && lo < 0xe000 then utf8 b (0x10000 + ((hi - 0xd800) lsl 10) + (lo - 0xdc00))
                 else (utf8 b 0xfffd; utf8 b lo)
               end else utf8 b (if hi >= 0xd800 && hi < 0xe000 then 0xfffd else hi)
           | _ -> raise Bad_json);
          loop ()
      | c -> Buffer.add_char b c; incr i; loop () in
    loop (); Buffer.contents b in
  let rec value () =
    skip ();
    match peek () with
    | '"' -> Str (string ())
    | '{' ->
        incr i; skip ();
        if peek () = '}' then (incr i; Obj []) else
        let rec fields acc =
          let k = string () in expect ':';
          let v = value () in
          skip ();
          match peek () with
          | ',' -> incr i; fields ((k, v) :: acc)
          | '}' -> incr i; Obj (List.rev ((k, v) :: acc))
          | _ -> raise Bad_json in
        fields []
    | '[' ->
        incr i; skip ();
        if peek () = ']' then (incr i; Arr []) else
        let rec items acc =
          let v = value () in
          skip ();
          match peek () with
          | ',' -> incr i; items (v :: acc)
          | ']' -> incr i; Arr (List.rev (v :: acc))
          | _ -> raise Bad_json in
        items []
    | 't' -> literal "true" (Bool true)
    | 'f' -> literal "false" (Bool false)
    | 'n' -> literal "null" Null
    | '-' | '0'..'9' ->
        let start = !i in
        while !i < n && (match text.[!i] with '-' | '+' | '.' | 'e' | 'E' | '0'..'9' -> true | _ -> false) do incr i done;
        Num (String.sub text start (!i - start))
    | _ -> raise Bad_json in
  let v = value () in
  skip ();
  if !i <> n then raise Bad_json;
  v

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

let rec to_string = function
  | Null -> "null" | Bool b -> string_of_bool b | Num s -> s | Str s -> json_string s
  | Arr l -> "[" ^ String.concat "," (List.map to_string l) ^ "]"
  | Obj l -> "{" ^ String.concat "," (List.map (fun (k, v) -> json_string k ^ ":" ^ to_string v) l) ^ "}"

let member k = function Obj l -> List.assoc_opt k l | _ -> None
