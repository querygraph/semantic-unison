/* Test-only ordinary positional copying; this is not a native clone backend. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <caml/signals.h>
#include <errno.h>
#include <unistd.h>

CAMLprim value clone_lease_fixture_copy(value source, value destination,
                                        value source_offset, value destination_offset,
                                        value length)
{
  CAMLparam5(source, destination, source_offset, destination_offset, length);
  char buffer[256];
  int s = Int_val(source), d = Int_val(destination), saved = 0;
  size_t n = Long_val(length), read_count = 0, written = 0;
  off_t so = Int64_val(source_offset), doff = Int64_val(destination_offset);
  if (Long_val(length) < 1 || n > sizeof(buffer)) caml_invalid_argument("fixture copy length");
  caml_enter_blocking_section_no_pending();
  while (read_count < n) {
    ssize_t count = pread(s, buffer + read_count, n - read_count, so + read_count);
    if (count < 0 && errno == EINTR) continue;
    if (count <= 0) {saved = count == 0 ? EIO : errno; break;}
    read_count += count;
  }
  while (!saved && written < n) {
    ssize_t count = pwrite(d, buffer + written, n - written, doff + written);
    if (count < 0 && errno == EINTR) continue;
    if (count <= 0) {saved = count == 0 ? EIO : errno; break;}
    written += count;
  }
  caml_leave_blocking_section();
  if (saved) unix_error(saved, "fixture positional copy", Nothing);
  CAMLreturn(Val_long(written));
}
