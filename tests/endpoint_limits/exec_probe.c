/* A disposable pre-exec oracle. The same PID subsequently becomes Unison. */
#include <sys/resource.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern char **environ;
int main(int argc,char **argv) {
  if(argc<4)return 2;
  int cap=atoi(argv[1]);if(cap<4||cap>4096||argv[2][0]!='/')return 3;
  struct rlimit actual;if(getrlimit(RLIMIT_NOFILE,&actual))return 4;
  if(actual.rlim_cur!=(rlim_t)cap||actual.rlim_max!=(rlim_t)cap)return 5;
  int descriptors[4096],count=0,fd;
  errno=0;
  while(count<cap && (fd=open("/dev/null",O_RDONLY))>=0)descriptors[count++]=fd;
  int open_error=errno;
  if(count!=cap-3||open_error!=EMFILE)return 6;
  for(int i=0;i<count;i++)if(close(descriptors[i]))return 7;
  struct rlimit raised={(rlim_t)cap+1,(rlim_t)cap+1};
  errno=0;int rc=setrlimit(RLIMIT_NOFILE,&raised);int raise_error=errno;
  if(rc==0||raise_error!=EPERM)return 8;
  printf("ENDPOINT-FD-ORACLE pid=%ld soft=%d hard=%d opens=%d EMFILE=true raiseDenied=true\n",(long)getpid(),cap,cap,count);
  fflush(stdout);
  execve(argv[2],argv+3,environ);
  return 9;
}
