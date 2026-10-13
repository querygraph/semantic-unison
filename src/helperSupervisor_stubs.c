/* POSIX child creation safe in a process with OCaml domains: no forked OCaml
 * execution. All called from the supervisor's owner domain with the runtime
 * held. This backend intentionally makes no native Windows claims. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#ifndef _WIN32
#include <spawn.h>
#include <signal.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#endif

#ifdef __APPLE__
#include <sys/types.h>
#include <sys/sysctl.h>
#endif

static long available_cpu_count(void)
{
#ifndef _WIN32
  long count = sysconf(_SC_NPROCESSORS_ONLN);
  return count > 0 ? count : 1;
#else
  return 1;
#endif
}

CAMLprim value unsn_helper_available_cpus(value unit)
{
  (void)unit;
  return Val_long(available_cpu_count());
}

CAMLprim value unsn_helper_available_physical_cpus(value unit)
{
  (void)unit;
  long count = available_cpu_count();
#ifdef __APPLE__
  int physical = 0;
  size_t size = sizeof(physical);
  if (sysctlbyname("hw.physicalcpu", &physical, &size, NULL, 0) == 0 &&
      size == sizeof(physical) && physical > 0 && physical < count)
    count = physical;
#endif
  return Val_long(count);
}

CAMLprim value unsn_helper_monotonic_now(value unit)
{
  CAMLparam1(unit);
#ifndef _WIN32
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    caml_uerror("clock_gettime", Nothing);
  CAMLreturn(caml_copy_double((double)ts.tv_sec + (double)ts.tv_nsec / 1e9));
#else
  caml_failwith("POSIX helper backend unavailable");
#endif
}

CAMLprim value unsn_helper_exited_unreaped(value vpid)
{
  CAMLparam1(vpid);
#ifndef _WIN32
  siginfo_t info;
  int rc;
  memset(&info, 0, sizeof(info));
  do { rc = waitid(P_PID, (id_t)Long_val(vpid), &info,
                  WEXITED | WNOHANG | WNOWAIT); } while (rc != 0 && errno == EINTR);
  if (rc != 0) caml_uerror("waitid", Nothing);
  CAMLreturn(Val_bool(info.si_pid != 0));
#else
  caml_failwith("POSIX helper backend unavailable");
#endif
}

#ifndef _WIN32
static void free_strings(char **strings)
{
  if (!strings) return;
  for (size_t i = 0; strings[i]; i++) free(strings[i]);
  free(strings);
}

static char **copy_strings(value values)
{
  size_t count = Wosize_val(values);
  char **result = calloc(count + 1, sizeof(char *));
  if (!result) return NULL;
  for (size_t i = 0; i < count; i++) {
    result[i] = strdup(String_val(Field(values, i)));
    if (!result[i]) { free_strings(result); return NULL; }
  }
  return result;
}
#endif

CAMLprim value unsn_helper_spawn_group(value executable, value arguments,
                                       value environment, value outfd, value errfd)
{
  CAMLparam5(executable, arguments, environment, outfd, errfd);
#ifndef _WIN32
  char **argv = copy_strings(arguments);
  char **envp = copy_strings(environment);
  if (!argv || !envp) {
    free_strings(argv); free_strings(envp); caml_raise_out_of_memory();
  }
  posix_spawn_file_actions_t actions;
  posix_spawnattr_t attributes;
  int have_actions = 0, have_attributes = 0;
  int child_out = -1, child_err = -1;
  int error = posix_spawn_file_actions_init(&actions);
  pid_t pid = -1;
  if (error) goto finish;
  have_actions = 1;
  error = posix_spawnattr_init(&attributes);
  if (error) goto finish;
  have_attributes = 1;
  /* Even if the application entered with fd 0, 1 or 2 closed, setting up stdin
   * must not overwrite a source descriptor for stdout or stderr. */
  child_out = fcntl(Int_val(outfd), F_DUPFD_CLOEXEC, 3);
  if (child_out < 0) { error = errno; goto finish; }
  child_err = fcntl(Int_val(errfd), F_DUPFD_CLOEXEC, 3);
  if (child_err < 0) { error = errno; goto finish; }
  error = posix_spawn_file_actions_addopen(&actions, STDIN_FILENO,
                                          "/dev/null", O_RDONLY, 0);
  if (error) goto finish;
  error = posix_spawn_file_actions_adddup2(&actions, child_out, STDOUT_FILENO);
  if (error) goto finish;
  error = posix_spawn_file_actions_adddup2(&actions, child_err, STDERR_FILENO);
  if (error) goto finish;
  sigset_t mask, defaults;
  sigemptyset(&mask);
  sigemptyset(&defaults);
  sigaddset(&defaults, SIGPIPE);
  sigaddset(&defaults, SIGTERM);
  sigaddset(&defaults, SIGINT);
  error = posix_spawnattr_setsigmask(&attributes, &mask);
  if (error) goto finish;
  error = posix_spawnattr_setsigdefault(&attributes, &defaults);
  if (error) goto finish;
  short flags = POSIX_SPAWN_SETPGROUP | POSIX_SPAWN_SETSIGMASK |
                POSIX_SPAWN_SETSIGDEF;
#ifdef POSIX_SPAWN_CLOEXEC_DEFAULT
  flags |= POSIX_SPAWN_CLOEXEC_DEFAULT;
#endif
  error = posix_spawnattr_setflags(&attributes, flags);
  if (error) goto finish;
  error = posix_spawnattr_setpgroup(&attributes, 0);
  if (error) goto finish;
  error = posix_spawn(&pid, String_val(executable), &actions, &attributes, argv, envp);
finish:
  if (child_out >= 0) close(child_out);
  if (child_err >= 0) close(child_err);
  if (have_attributes) posix_spawnattr_destroy(&attributes);
  if (have_actions) posix_spawn_file_actions_destroy(&actions);
  free_strings(argv); free_strings(envp);
  if (error) { errno = error; caml_uerror("posix_spawn", executable); }
  CAMLreturn(Val_long(pid));
#else
  caml_failwith("POSIX helper backend unavailable");
#endif
}
