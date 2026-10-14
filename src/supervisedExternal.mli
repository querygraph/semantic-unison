(** Owner-loop bridge for per-file copy, merge and diff commands. POSIX
    invocations share the semantic/SDK CPU supervisor, bounded output and
    process-group cancellation/reap. Command helpers must remain foreground
    and complete their output before exit. Windows retains the explicit
    unsupervised legacy backend. No child-memory/FD ceiling is established. *)
val runExternalProgram : string -> (Unix.process_status * string) Lwt.t
val runExternalProgramArgs : string -> string array -> (Unix.process_status * string) Lwt.t
(** The argv array includes its original argv[0], as in External's legacy API.
    Preserve argument boundaries, invocation name and inherited environment.
    Shell commands use /bin/sh -c; no shell is added for argv invocations.
    Completed nonzero exit statuses are returned for caller policy. Signals, cancellation,
    timeout, output-limit and supervision failures reject after settlement. *)
