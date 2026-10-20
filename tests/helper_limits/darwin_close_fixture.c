/* Kernel close succeeds but reports EINTR. Isolated process only. */
#include <sys/resource.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <fcntl.h>
#if defined(__APPLE__)
#include <libproc.h>
#include <sys/proc_info.h>
static int calls;
static int fixture_close(int fd) {
  calls++;if(close(fd))return -1;errno=EINTR;return -1;
}
#define close fixture_close
#define main launcher_main
#include "launcher.c"
#undef main
#undef close
int main(int argc,char **argv) {
  if(argc!=3)return 4;
  int fd=open("/dev/null",O_RDONLY);
  if(fd<3)return 1;
  if(close_inherited()!=-1 || errno!=EINTR || calls!=1)return 2;
  if(fcntl(fd,F_GETFD)!=-1 || errno!=EBADF)return 3;
  fd=open("/dev/null",O_RDONLY);calls=0;
  if(fd<3)return 5;
  char *target[]={"launcher","--unison-helper-limits-v1","12","0",
    "--",argv[1],"probe","marker",argv[2],NULL};
  if(launcher_main(9,target)!=125 || calls!=1)return 6;
  if(access(argv[2],F_OK)==0)return 7;
  puts("PASS Darwin uncertain close refused/no numeric retry");return 0;
}
#else
int main(void) {puts("SKIP Darwin-specific enumeration");return 0;}
#endif
