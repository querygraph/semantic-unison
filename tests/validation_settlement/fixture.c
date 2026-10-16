/* The private wrapper records actual immediate spawn PIDs by nonallocating
   scalar assignment. It does not delay the production post-spawn owner. */
#define unsn_helper_spawn_group validation_private_spawn_group
#include "helperSupervisor_stubs.c"
#undef unsn_helper_spawn_group
static int validation_pids[64];
static int validation_pid_count;
CAMLprim value unsn_helper_spawn_group(value executable, value arguments,
                                      value environment, value outfd, value errfd)
{
  CAMLparam5(executable, arguments, environment, outfd, errfd);
  value result = validation_private_spawn_group(executable, arguments, environment,
                                                outfd, errfd);
  if (validation_pid_count < 64) validation_pids[validation_pid_count++] = Int_val(result);
  CAMLreturn(result);
}
CAMLprim value validation_fixture_pid_count(value unit)
{
  CAMLparam1(unit);
  CAMLreturn(Val_int(validation_pid_count));
}
CAMLprim value validation_fixture_pid_at(value index)
{
  CAMLparam1(index);
  int i = Int_val(index);
  CAMLreturn(Val_int(i >= 0 && i < validation_pid_count ? validation_pids[i] : -1));
}
CAMLprim value validation_fixture_reset(value unit)
{
  CAMLparam1(unit);
  validation_pid_count = 0;
  CAMLreturn(Val_unit);
}
