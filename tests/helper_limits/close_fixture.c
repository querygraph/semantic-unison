/* Original injected control of the portable syscall boundary. */
#include <sys/resource.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static rlim_t bound;
static int calls, fail_at;
static int fixture_getrlimit(int which,struct rlimit *out) {
  (void)which;out->rlim_cur=out->rlim_max=bound;return 0;
}
static int fixture_close(int fd) {
  calls++;errno=fd==fail_at?EINTR:EBADF;return -1;
}
#undef __APPLE__
#undef __linux__
#undef __FreeBSD__
#undef __OpenBSD__
#undef __NetBSD__
#define getrlimit fixture_getrlimit
#define close fixture_close
#define main launcher_main
#include "launcher.c"
#undef main
int main(void) {
  bound=65537;calls=0;
  if(close_inherited()!=-1 || errno!=ENOTSUP || calls)return 1;
  bound=RLIM_INFINITY;calls=0;
  if(close_inherited()!=-1 || errno!=ENOTSUP || calls)return 2;
  bound=8;calls=0;fail_at=5;
  if(close_inherited()!=-1 || errno!=EINTR || calls!=3)return 3;
  calls=0;fail_at=-1;
  if(close_inherited()!=0 || calls!=5)return 4;
  puts("PASS4 portable bounded scan/no uncertain numeric retry");return 0;
}
