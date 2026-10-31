(* Built without the packdir library (no SQLite binding): packed roots are refused. *)
let available = false
let install (_ : Fspath.t) (_ : int) = ()
let copy (_ : Common.root) (_ : Path.t) (_ : Common.updateItem) (_ : Common.root) (_ : Path.t) : unit Lwt.t =
  raise (Util.Transient "packed roots are not supported by this build")
let delete (_ : Common.root) (_ : Path.t) (_ : Common.root) (_ : Path.t) : unit Lwt.t =
  raise (Util.Transient "packed roots are not supported by this build")
