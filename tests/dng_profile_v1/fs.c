#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <sys/mount.h>

/* Observe only the private synthetic fixture directory's filesystem. */
CAMLprim value fixture_dng_v1_filesystem(value path)
{
  CAMLparam1(path);
  struct statfs observed;
  if (statfs(String_val(path), &observed))
    caml_unix_error(errno, "fixture_dng_v1_statfs", Nothing);
  CAMLreturn(caml_copy_string(observed.f_fstypename));
}
