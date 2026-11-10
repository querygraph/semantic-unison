(* unison-dngscan -semindex: phindex indexes of the trees being compared
   (https://github.com/firstpair/phindex).  An index lists each file of a tree
   with its size, modification time, SHA-256 and the identities that survive a
   metadata edit (DNG raw blocks, image data).  Semdiff uses a row only while
   the file still has the row's size and modification time, and then takes the
   row's word for the file's content without reading it.

   Opened read-only with immutable=1: nothing is written beside the index.
   Every lookup is a point query; a column the database has no index for is
   not looked up. *)

type row = { size : int64; mtime_ns : int64; sha256 : string; dng_blocks : string; image_data : string }
type t = { db : Sqlite3.db; columns : string; by_sha256 : bool; identities : string list }

let available = true

let rows db sql params =
  let st = Sqlite3.prepare db sql in
  Fun.protect ~finally:(fun () -> ignore (Sqlite3.finalize st)) (fun () ->
    List.iteri (fun i p -> ignore (Sqlite3.bind st (i + 1) p)) params;
    let rec go acc = match Sqlite3.step st with
      | Sqlite3.Rc.ROW -> go (Sqlite3.row_data st :: acc)
      | Sqlite3.Rc.DONE -> List.rev acc
      | rc -> failwith (Printf.sprintf "%s (%s)" (Sqlite3.Rc.to_string rc) (Sqlite3.errmsg db)) in
    go [])

let open_ file =
  if not (Sys.file_exists file) || Sys.is_directory file then failwith ("-semindex: no phindex index at " ^ file);
  let real = try Unix.realpath file with Unix.Unix_error _ -> file in
  (* In a URI filename % ? and # are syntax. *)
  let b = Buffer.create (String.length real) in
  String.iter (function '%' -> Buffer.add_string b "%25" | '?' -> Buffer.add_string b "%3f"
                        | '#' -> Buffer.add_string b "%23" | c -> Buffer.add_char b c) real;
  let db = Sqlite3.db_open ~mode:`READONLY ~uri:true ("file:" ^ Buffer.contents b ^ "?immutable=1") in
  let names q = List.filter_map (fun r -> match r.(0) with Sqlite3.Data.TEXT s -> Some s | _ -> None)
      (try rows db q [] with Failure _ | Sqlite3.Error _ -> []) in
  let have = names "SELECT name FROM pragma_table_info('files')" in
  if not (List.for_all (fun c -> List.mem c have) ["path"; "size"; "mtime_ns"; "sha256"; "gone"]) then begin
    ignore (Sqlite3.db_close db);
    failwith ("-semindex: " ^ file ^ " is not a phindex index")
  end;
  let leading = names "SELECT i.name FROM pragma_index_list('files') l, pragma_index_info(l.name) i WHERE i.seqno=0" in
  let column c = if List.mem c have then c else "NULL" in
  { db; columns = Printf.sprintf "path, size, mtime_ns, sha256, %s, %s" (column "dng_blocks") (column "image_data");
    by_sha256 = List.mem "sha256" leading;
    identities = List.filter (fun c -> List.mem c have && List.mem c leading) ["dng_blocks"; "image_data"] }

let listed t where key limit =
  let text = function Sqlite3.Data.TEXT s -> s | _ -> "" in
  List.filter_map (fun r ->
    match r.(0), r.(1), r.(2) with
    | Sqlite3.Data.TEXT path, Sqlite3.Data.INT size, Sqlite3.Data.INT mtime_ns ->
        Some (path, { size; mtime_ns; sha256 = text r.(3); dng_blocks = text r.(4); image_data = text r.(5) })
    | _ -> None)
    (try rows t.db (Printf.sprintf "SELECT %s FROM files WHERE %s=?1 AND gone=0 LIMIT ?2" t.columns where)
           [Sqlite3.Data.TEXT key; Sqlite3.Data.INT (Int64.of_int limit)]
     with Failure _ | Sqlite3.Error _ -> [])

(* The live row of a path. *)
let at t path = match listed t "path" path 1 with [ (_, r) ] -> Some r | _ -> None

(* Live rows listed with this SHA-256, at most [limit]. *)
let holding t sha256 limit = if t.by_sha256 && sha256 <> "" then listed t "sha256" sha256 limit else []

(* Live rows listed with this identity ([column] is dng_blocks or image_data). *)
let sharing t column value limit =
  if value <> "" && List.mem column t.identities then listed t column value limit else []
