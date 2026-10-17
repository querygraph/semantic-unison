/* Original test-only shim. Production builds never link this object or define
 * fsync=unison_record_control_fsync. No environment-selected production behavior. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <stdatomic.h>
static atomic_int mode, regular_calls, directory_calls;
CAMLprim value unison_record_fault_configure(value selected)
{
  atomic_store(&regular_calls, 0); atomic_store(&directory_calls, 0);
  atomic_store(&mode, Int_val(selected)); return Val_unit;
}
CAMLprim value unison_record_fault_counts(value unit)
{
  CAMLparam1(unit); CAMLlocal1(result);
  result = caml_alloc_tuple(2);
  Store_field(result, 0, Val_int(atomic_load(&regular_calls)));
  Store_field(result, 1, Val_int(atomic_load(&directory_calls)));
  CAMLreturn(result);
}
int unison_record_control_fsync(int fd)
{
  struct stat observed;
  if (fstat(fd, &observed) == -1) return -1;
  int selected = atomic_load(&mode);
  if (S_ISDIR(observed.st_mode)) {
    atomic_fetch_add(&directory_calls, 1);
    if (selected == 1) { errno = EIO; return -1; }
  } else if (S_ISREG(observed.st_mode)) {
    atomic_fetch_add(&regular_calls, 1);
    if (selected == 2 || selected == 3) {
      errno = selected == 3 ? EINTR : EIO; return -1;
    }
  }
  return fsync(fd);
}
