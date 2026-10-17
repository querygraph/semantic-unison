/* Disposable close interposition only. Production contains no fault switch. */
#include <caml/mlvalues.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
static int failed, calls;
CAMLprim value owned_fixture_mode(value mode)
{ failed = Int_val(mode); calls = 0; return Val_unit; }
CAMLprim value owned_fixture_closes(value unit)
{ (void)unit; return Val_int(calls); }
CAMLprim value owned_fixture_busy(value unit)
{ (void)unit; return Val_int(EBUSY); }
CAMLprim value owned_fixture_known_open(value descriptor)
{ return Val_bool(fcntl(Int_val(descriptor), F_GETFD) != -1); }
static int owned_fixture_close(int fd)
{
  int ordinal = ++calls, result = close(fd), saved = errno;
  if (failed == -1 || failed == ordinal) { errno = EIO; return -1; }
  errno = saved; return result;
}
#define close owned_fixture_close
#include "stagePublication_stubs.c"
#undef close
