/* Private kernel FD census; excludes its own directory descriptor. */
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/fail.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdlib.h>
#include <errno.h>
CAMLprim value resource_fixture_fd_count(value unit) {
  CAMLparam1(unit);
  DIR *d = opendir("/dev/fd");
  if (!d) caml_failwith("open FD census");
  int own = dirfd(d), count = 0;
  struct dirent *e;
  while ((e = readdir(d))) {
    char *end;
    long fd = strtol(e->d_name, &end, 10);
    if (*e->d_name && !*end && fd >= 0 && fd <= 0x7fffffffL && fd != own &&
        fcntl((int)fd, F_GETFD) != -1) count++;
  }
  if (closedir(d)) caml_failwith("close FD census");
  CAMLreturn(Val_int(count));
}
