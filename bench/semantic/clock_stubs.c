/* Benchmark-only clocks: wall time is monotonic, CPU time includes all domains. */
#include <time.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/fail.h>

static value seconds(clockid_t clock)
{
  struct timespec t;
  if (clock_gettime(clock, &t)) caml_failwith("benchmark clock_gettime");
  return caml_copy_double((double)t.tv_sec + (double)t.tv_nsec / 1e9);
}
CAMLprim value benchmark_wall(value unit) { return seconds(CLOCK_MONOTONIC); }
CAMLprim value benchmark_cpu(value unit) { return seconds(CLOCK_PROCESS_CPUTIME_ID); }

/* Process-lifetime high water, including startup and shutdown. macOS reports
   bytes; Linux reports KiB. This is measurement, not an RSS limit. */
#include <sys/resource.h>
CAMLprim value benchmark_peak_rss(value unit) {
  struct rusage usage;
  if (getrusage(RUSAGE_SELF, &usage)) caml_failwith("benchmark getrusage");
#ifdef __APPLE__
  return caml_copy_double((double)usage.ru_maxrss);
#else
  return caml_copy_double((double)usage.ru_maxrss * 1024.0);
#endif
}
/* Private kernel FD census; excludes its own directory descriptor. */
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/fail.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdlib.h>
#include <errno.h>
CAMLprim value benchmark_fd_count(value unit) {
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
