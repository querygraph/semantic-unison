/* Original metadata-only fixture: expose exact native mtime/ctime, no IO policy. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <sys/stat.h>
#include <errno.h>
#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#endif
CAMLprim value unison_publication_test_exact_times(value path)
{
  CAMLparam1(path);
  CAMLlocal5(result,mtime_seconds,mtime_nanoseconds,ctime_seconds,ctime_nanoseconds);
  struct stat observed;
  if (lstat(String_val(path), &observed) < 0)
    caml_unix_error(errno, "publication_test_exact_times", path);
#if defined(__APPLE__)
  mtime_seconds = caml_copy_int64(observed.st_mtimespec.tv_sec);
  mtime_nanoseconds = Val_long(observed.st_mtimespec.tv_nsec);
  ctime_seconds = caml_copy_int64(observed.st_ctimespec.tv_sec);
  ctime_nanoseconds = Val_long(observed.st_ctimespec.tv_nsec);
#else
  mtime_seconds = caml_copy_int64(observed.st_mtim.tv_sec);
  mtime_nanoseconds = Val_long(observed.st_mtim.tv_nsec);
  ctime_seconds = caml_copy_int64(observed.st_ctim.tv_sec);
  ctime_nanoseconds = Val_long(observed.st_ctim.tv_nsec);
#endif
  result = caml_alloc_tuple(4);
  Store_field(result,0,mtime_seconds); Store_field(result,1,mtime_nanoseconds);
  Store_field(result,2,ctime_seconds); Store_field(result,3,ctime_nanoseconds);
  CAMLreturn(result);
}
