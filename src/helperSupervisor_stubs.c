/* POSIX child creation safe in a process with OCaml domains: no forked OCaml
 * execution. All called from the supervisor's owner domain with the runtime
 * held. This backend intentionally makes no native Windows claims. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/custom.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>

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
#include <sys/proc.h>
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

/* The finite pilot is linked separately with this compile-time containment
 * backend. Production always owns one group per helper. No environment switch. */
CAMLprim value unsn_helper_signal_target(value vpid)
{
#ifdef UNISON_BENCH_CONTAINED_HELPERS
  return vpid;
#else
  return Val_long(-Long_val(vpid));
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


/* A preallocated spawn-time binding, not a resource-owning finalizer or a
 * serializable peer capability. The ML owner must retire it before reaping. */
struct helper_group_owner { intnat parent, child; int retired; };
static struct custom_operations helper_group_owner_ops = {
  .identifier = "unison.helper_group_owner.v0",
  .finalize = custom_finalize_default,
  .compare = custom_compare_default,
  .hash = custom_hash_default,
  .serialize = custom_serialize_default,
  .deserialize = custom_deserialize_default,
  .compare_ext = custom_compare_ext_default,
  .fixed_length = custom_fixed_length_default
};
static intnat helper_owner_parent(void)
{
#ifndef _WIN32
  return (intnat)getpid();
#else
  return 0;
#endif
}
static struct helper_group_owner *helper_owner(value owner)
{
  if (!Is_block(owner) || Tag_val(owner) != Custom_tag ||
      Custom_ops_val(owner) != &helper_group_owner_ops)
    caml_invalid_argument("helper group owner type");
  struct helper_group_owner *result = (void *)Data_custom_val(owner);
  if (result->parent != helper_owner_parent())
    caml_invalid_argument("helper group owner process");
  return result;
}
CAMLprim value unsn_helper_group_owner_create(value unit)
{
  CAMLparam1(unit);
  CAMLlocal1(owner);
  owner = caml_alloc_custom(&helper_group_owner_ops,
                           sizeof(struct helper_group_owner), 0, 1);
  struct helper_group_owner *binding = (void *)Data_custom_val(owner);
  binding->parent = helper_owner_parent(); binding->child = 0; binding->retired = 0;
  CAMLreturn(owner);
}
CAMLprim value unsn_helper_group_owner_retire(value owner)
{
  CAMLparam1(owner);
  helper_owner(owner)->retired = 1;
  CAMLreturn(Val_unit);
}

/* Diagnostic observation only. The caller must retain this exact direct child
 * unreaped, on its sole owner loop. The binding was created with group pid.
 * No signaling or reaping occurs here. Unsupported platforms return -1, never
 * an invented zero. Kernel/shape/ownership failures raise, not empty success. */
CAMLprim value unsn_helper_retained_group_others(value owner)
{
  CAMLparam1(owner);
  struct helper_group_owner *binding = helper_owner(owner);
  if (binding->child <= 0 || binding->child > INT_MAX || binding->retired)
    caml_invalid_argument("retained helper group binding");
#if defined(__APPLE__) && !defined(UNISON_BENCH_CONTAINED_HELPERS)
  pid_t pid = (pid_t)binding->child;
  siginfo_t info;
  memset(&info, 0, sizeof(info));
  int rc;
  do { rc = waitid(P_PID, (id_t)pid, &info,
                  WEXITED | WNOHANG | WNOWAIT); } while (rc != 0 && errno == EINTR);
  if (rc != 0) caml_uerror("retained group waitid", Nothing);
  if (info.si_pid != pid) {
    errno = EBUSY; caml_uerror("retained group leader not terminal", Nothing);
  }
  /* getpgid cannot identify Darwin zombie leaders. Use only the immutable
   * group binding authenticated at our successful posix_spawn instead. */
  /* Fixed bounded stack storage. A larger group makes sysctl fail ENOMEM;
   * neither partial enumeration nor malformed records may certify absence. */
  struct kinfo_proc members[64];
  size_t bytes = sizeof(members);
  int mib[4] = { CTL_KERN, KERN_PROC, KERN_PROC_PGRP, (int)pid };
  if (sysctl(mib, 4, members, &bytes, NULL, 0) != 0)
    caml_uerror("retained group sysctl", Nothing);
  if (bytes > sizeof(members) || bytes % sizeof(members[0])) {
    errno = EIO; caml_uerror("retained group record size", Nothing);
  }
  int leader = 0, others = 0;
  for (size_t i = 0; i < bytes / sizeof(members[0]); i++) {
    if (members[i].kp_proc.p_pid <= 0 ||
        (members[i].kp_eproc.e_pgid != pid &&
         !(members[i].kp_proc.p_stat == SZOMB && members[i].kp_eproc.e_pgid == 0))) {
      errno = EIO; caml_uerror("retained group identity", Nothing);
    }
    if (members[i].kp_proc.p_pid == pid) leader++;
    else others++;
  }
  if (leader > 1) {
    errno = EIO; caml_uerror("retained group duplicate leader", Nothing);
  }
  /* Recheck our retained direct-child relationship before reporting the query.
   * Another reaper violates the owner contract and cannot yield a zero receipt. */
  memset(&info, 0, sizeof(info));
  do { rc = waitid(P_PID, (id_t)pid, &info,
                  WEXITED | WNOHANG | WNOWAIT); } while (rc != 0 && errno == EINTR);
  if (rc != 0) caml_uerror("retained group final waitid", Nothing);
  if (info.si_pid != pid) {
    errno = EIO; caml_uerror("retained group final child", Nothing);
  }
  CAMLreturn(Val_int(others));
#else
  CAMLreturn(Val_int(-1));
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

#ifndef _WIN32
static pid_t helper_spawn_native(value executable, value arguments,
                                 value environment, value outfd, value errfd)
{
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
  #ifdef UNISON_BENCH_CONTAINED_HELPERS
  error = posix_spawnattr_setpgroup(&attributes, getpgrp());
#else
  error = posix_spawnattr_setpgroup(&attributes, 0);
#endif
  if (error) goto finish;
  error = posix_spawn(&pid, String_val(executable), &actions, &attributes, argv, envp);
finish:
  if (child_out >= 0) close(child_out);
  if (child_err >= 0) close(child_err);
  if (have_attributes) posix_spawnattr_destroy(&attributes);
  if (have_actions) posix_spawn_file_actions_destroy(&actions);
  free_strings(argv); free_strings(envp);
  if (error) { errno = error; caml_uerror("posix_spawn", executable); }
  return pid;
}
#endif
CAMLprim value unsn_helper_spawn_group(value executable, value arguments,
                                       value environment, value outfd, value errfd)
{
  CAMLparam5(executable, arguments, environment, outfd, errfd);
#ifndef _WIN32
  CAMLreturn(Val_long(helper_spawn_native(executable, arguments, environment, outfd, errfd)));
#else
  caml_failwith("POSIX helper backend unavailable");
#endif
}
CAMLprim value unsn_helper_spawn_group_owned(value executable, value arguments,
        value environment, value outfd, value errfd, value owner)
{
  CAMLparam5(executable, arguments, environment, outfd, errfd);
  CAMLxparam1(owner);
  struct helper_group_owner *binding = helper_owner(owner);
  if (binding->child != 0 || binding->retired)
    caml_invalid_argument("helper group owner reused");
#ifndef _WIN32
  /* No allocation/callback follows successful native spawn before the binding
   * and immediate PID return. The owner was allocated before acquiring a child. */
  pid_t pid = helper_spawn_native(executable, arguments, environment, outfd, errfd);
  binding->child = pid;
  CAMLreturn(Val_long(pid));
#else
  caml_failwith("POSIX helper backend unavailable");
#endif
}
CAMLprim value unsn_helper_spawn_group_owned_bytecode(value *arguments, int count)
{
  if (count != 6) caml_invalid_argument("helper group spawn arity");
  return unsn_helper_spawn_group_owned(arguments[0], arguments[1], arguments[2],
                                    arguments[3], arguments[4], arguments[5]);
}
