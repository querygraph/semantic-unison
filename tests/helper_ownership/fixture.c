#define unsn_helper_spawn_group private_helper_spawn_group
#include "helperSupervisor_stubs.c"
#undef unsn_helper_spawn_group

/* Observe the actual immediate native PID without adding a post-spawn ML
   allocation or callback before the production owner stores it. */
static int watched_pid = -1;
CAMLprim value unsn_helper_spawn_group(value executable, value arguments,
                                      value environment, value outfd, value errfd)
{
  CAMLparam5(executable, arguments, environment, outfd, errfd);
  value result = private_helper_spawn_group(executable, arguments, environment,
                                           outfd, errfd);
  watched_pid = Int_val(result);
  CAMLreturn(result);
}
CAMLprim value helper_owner_pid(value unit)
{
  CAMLparam1(unit);
  CAMLreturn(Val_int(watched_pid));
}
CAMLprim value helper_owner_reset(value unit)
{
  CAMLparam1(unit);
  watched_pid = -1;
  CAMLreturn(Val_unit);
}
