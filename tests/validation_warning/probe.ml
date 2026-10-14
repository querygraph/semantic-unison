(* Private owner-side observations, linked before instrumented SemanticWorkers.
   No promise state, worker response, admission or scheduler behavior is changed. *)
let dispatch_depth = ref 0
let pump_rearms = ref 0
let warning_anchor = ref (-1)
let enter_dispatch () = incr dispatch_depth
let leave_dispatch () = decr dispatch_depth
let rearmed () = incr pump_rearms
let anchor () = warning_anchor := !pump_rearms
