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
