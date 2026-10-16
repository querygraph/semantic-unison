/* Private syscall observations around byte-identical production code. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/fail.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/stat.h>
static int fault, observed_fd = -1, reused_fd = -1;
static char first[PATH_MAX], second[PATH_MAX], third[PATH_MAX];
static void copy_path(char *output, value path) {
  size_t length = caml_string_length(path);
  if (length >= PATH_MAX || memchr(String_val(path), 0, length))
    caml_invalid_argument("private cleanup fixture path");
  memcpy(output, String_val(path), length); output[length] = 0;
}
CAMLprim value obsolete_fixture_arm(value mode, value a, value b, value c) {
  CAMLparam4(mode, a, b, c);
  copy_path(first, a); copy_path(second, b); copy_path(third, c);
  fault = Int_val(mode); observed_fd = -1; CAMLreturn(Val_unit);
}
CAMLprim value obsolete_fixture_reused(value unit) {
  CAMLparam1(unit); CAMLreturn(Val_int(reused_fd));
}
CAMLprim value obsolete_fixture_disarm(value unit) {
  CAMLparam1(unit); fault = 0; observed_fd = -1; reused_fd = -1; CAMLreturn(Val_unit);
}
static int watched_open(const char *name, int flags) {
  int fd = open(name, flags);
  if (fd >= 0 && fault) observed_fd = fd;
  return fd;
}
static int watched_fstatat(int parent, const char *name, struct stat *st, int flags) {
  int status = fstatat(parent, name, st, flags);
  if (status == 0 && strcmp(name, "candidate") == 0) {
    if (fault == 1 || fault == 2) {
      /* Rename the admitted old object/parent aside and install an independent
         precreated replacement. Native checks must preserve both inventories. */
      int mode = fault; fault = 0;
      if (rename(first, second) || rename(third, first)) abort();
      (void)mode;
    }
  }
  return status;
}
static int watched_unlinkat(int parent, const char *name, int flags) {
  if (fault == 3 && observed_fd >= 0) { fault = 0; errno = EIO; return -1; }
  return unlinkat(parent, name, flags);
}
static int watched_close(int fd) {
  if (fault == 4 && fd == observed_fd) {
    int marker; fault = 0;
    if (close(fd)) abort();
    marker = open("/dev/null", O_RDONLY | O_CLOEXEC);
    if (marker < 0) abort();
    if (marker != fd) {
      if (dup2(marker, fd) < 0) abort();
      close(marker);
      if (fcntl(fd, F_SETFD, FD_CLOEXEC) < 0) abort();
    }
    reused_fd = fd; errno = EIO; return -1;
  }
  return close(fd);
}
#define open watched_open
#define fstatat watched_fstatat
#define unlinkat watched_unlinkat
#define close watched_close
#include "finalPublication_stubs.c"
