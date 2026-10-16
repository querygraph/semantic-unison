/* Benchmark-only wall, parent-domain CPU and reaped SDK-child CPU clocks. */
#include <time.h>
#include <sys/resource.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/fail.h>

static value clock_seconds(clockid_t clock)
{
  struct timespec value;
  if (clock_gettime(clock, &value)) caml_failwith("benchmark clock_gettime");
  return caml_copy_double((double)value.tv_sec + (double)value.tv_nsec / 1e9);
}
CAMLprim value adobe_benchmark_wall(value unit) { return clock_seconds(CLOCK_MONOTONIC); }
CAMLprim value adobe_benchmark_parent_cpu(value unit) { return clock_seconds(CLOCK_PROCESS_CPUTIME_ID); }
CAMLprim value adobe_benchmark_children_cpu(value unit)
{
  struct rusage usage;
  if (getrusage(RUSAGE_CHILDREN, &usage)) caml_failwith("benchmark getrusage");
  return caml_copy_double((double)usage.ru_utime.tv_sec + (double)usage.ru_utime.tv_usec / 1e6 +
                         (double)usage.ru_stime.tv_sec + (double)usage.ru_stime.tv_usec / 1e6);
}
