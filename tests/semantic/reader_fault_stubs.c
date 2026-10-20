/* Original test-only pread wrapper, compiled separately without the macro. */
#define _POSIX_C_SOURCE 200809L
#include <caml/mlvalues.h>
#include <stdatomic.h>
#include <unistd.h>
#include <errno.h>
static _Atomic int mode, calls;
CAMLprim value unison_reader_control_mode(value setting)
{
  atomic_store(&calls, 0); atomic_store(&mode, Int_val(setting)); return Val_unit;
}
CAMLprim value unison_reader_control_calls(value unit)
{
  (void)unit; return Val_int(atomic_load(&calls));
}
ssize_t unison_reader_control_pread(int fd, void *buffer, size_t count, off_t offset)
{
  int ordinal=atomic_fetch_add(&calls, 1), selected=atomic_load(&mode);
  if (selected==5 || (selected==1 && ordinal==0)) { errno=EINTR; return -1; }
  if (selected==2 && count>7) count=7;
  if (selected==3) return 0;
  if (selected==4) { errno=EIO; return -1; }
  return pread(fd, buffer, count, offset);
}
