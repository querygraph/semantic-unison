/* Separate posix_spawn'ed process: never modify the multithreaded parent's
 * limits and never fork an OCaml runtime. Exec retains PID/process group. */
#include <sys/resource.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#if defined(__linux__)
#include <sys/syscall.h>
#elif defined(__APPLE__)
#include <libproc.h>
#include <sys/proc_info.h>
#endif
extern char **environ;
static int error(const char *what) {
  fprintf(stderr,"UNISON-HELPER-LIMITS 1: %s: %s\n",what,strerror(errno));
  return 125;
}
static int decimal(const char *text,rlim_t *result) {
  uint64_t n=0;
  if(!*text || (text[0]=='0' && text[1])) return 0;
  for(const unsigned char *p=(const unsigned char *)text;*p;p++) {
    if(*p<'0'||*p>'9'||n>(UINT64_MAX-(*p-'0'))/10) return 0;
    n=n*10+(*p-'0');
  }
  *result=(rlim_t)n;
  return (uint64_t)*result==n && *result!=RLIM_INFINITY;
}
static int lower(int resource,rlim_t requested) {
  if(!requested) return 0;
  struct rlimit limit;
  if(getrlimit(resource,&limit))return -1;
  limit.rlim_cur=limit.rlim_max=limit.rlim_max<requested?limit.rlim_max:requested;
  if(setrlimit(resource,&limit))return -1;
  struct rlimit actual;
  if(getrlimit(resource,&actual))return -1;
  if(actual.rlim_cur>requested||actual.rlim_max>requested) {errno=EINVAL;return -1;}
  return 0;
}
static int close_inherited(void) {
#if defined(__APPLE__)
  /* Darwin has no public closefrom. This fresh single-threaded launcher opens
   * no descriptors during enumeration. Bound allocation and reject truncation. */
  int needed=proc_pidinfo(getpid(),PROC_PIDLISTFDS,0,NULL,0);
  if(needed<=0 || needed>4*1024*1024-32*(int)sizeof(struct proc_fdinfo)) {errno=EOVERFLOW;return -1;}
  int capacity=needed+32*(int)sizeof(struct proc_fdinfo);
  struct proc_fdinfo *fds=malloc((size_t)capacity);
  if(!fds)return -1;
  int count=proc_pidinfo(getpid(),PROC_PIDLISTFDS,0,fds,capacity);
  if(count<=0 || count>=capacity || count%(int)sizeof(*fds)) {free(fds);errno=EOVERFLOW;return -1;}
  for(int i=0;i<count/(int)sizeof(*fds);i++)if(fds[i].proc_fd>=3) {
    /* Never retry a numeric descriptor after an uncertain close. This fresh
     * launcher exits on failure, so no target can inherit uncertain ownership. */
    if(close(fds[i].proc_fd)) {int saved=errno;free(fds);errno=saved;return -1;}
  }
  count=proc_pidinfo(getpid(),PROC_PIDLISTFDS,0,fds,capacity);
  if(count<0 || count>=capacity || count%(int)sizeof(*fds)) {free(fds);errno=EOVERFLOW;return -1;}
  for(int i=0;i<count/(int)sizeof(*fds);i++)if(fds[i].proc_fd>=3) {free(fds);errno=EBUSY;return -1;}
  free(fds);return 0;
#elif defined(__FreeBSD__) || defined(__OpenBSD__) || defined(__NetBSD__)
  closefrom(3);return 0;
#elif defined(__linux__) && defined(SYS_close_range)
  if(syscall(SYS_close_range,3U,UINT_MAX,0)==0)return 0;
  if(errno!=ENOSYS&&errno!=EINVAL)return -1;
#endif
#if !defined(__APPLE__) && !defined(__FreeBSD__) && !defined(__OpenBSD__) && !defined(__NetBSD__)
  struct rlimit before;
  if(getrlimit(RLIMIT_NOFILE,&before))return -1;
  /* Without a kernel close-range API, refuse an unbounded/very large scan.
   * A configured optional launcher must fail closed, never skip high FDs. */
  if(before.rlim_max==RLIM_INFINITY || before.rlim_max>65536) {errno=ENOTSUP;return -1;}
  for(int fd=3;fd<(int)before.rlim_max;fd++)
    if(close(fd) && errno!=EBADF)return -1;
  return 0;
#endif
}
int main(int argc,char **argv) {
  rlim_t descriptors,address;
  if(argc<7 || strcmp(argv[1],"--unison-helper-limits-v1") ||
     !decimal(argv[2],&descriptors) || !decimal(argv[3],&address) ||
     (descriptors && descriptors<3) || (!descriptors && !address) ||
     strcmp(argv[4],"--") || argv[5][0]!='/') {
    errno=EINVAL;return error("invalid invocation");
  }
  if(close_inherited())return error("close inherited descriptors");
  if(lower(RLIMIT_NOFILE,descriptors))return error("descriptor limit");
#ifdef RLIMIT_AS
  if(lower(RLIMIT_AS,address))return error("address-space limit");
#else
  if(address){errno=ENOTSUP;return error("address-space limit unavailable");}
#endif
  execve(argv[5],argv+6,environ);
  return error("execve");
}
