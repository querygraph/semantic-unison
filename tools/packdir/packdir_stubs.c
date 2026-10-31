/* F_FULLFSYNC: flush the drive's own write cache (macOS); fsync elsewhere. */
#include <fcntl.h>
#include <unistd.h>
#include <caml/mlvalues.h>
#include <caml/unixsupport.h>

CAMLprim value packdir_fullfsync(value fd) {
#ifdef F_FULLFSYNC
  if (fcntl(Int_val(fd), F_FULLFSYNC) == 0) return Val_unit;
#endif
  if (fsync(Int_val(fd)) < 0) uerror("fullfsync", Nothing);
  return Val_unit;
}
