#include <sys/resource.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
int main(int argc,char **argv) {
 if(argc<2)return 2;
 struct rlimit limit;if(getrlimit(RLIMIT_NOFILE,&limit))return 3;
 printf("LIMIT %llu %llu\n",(unsigned long long)limit.rlim_cur,(unsigned long long)limit.rlim_max);
 printf("GROUP %d\n",getpid()==getpgrp());fflush(stdout);
 if(!strcmp(argv[1],"opens")) {
  int count=0;while(count<40&&open("/dev/null",O_RDONLY)>=0)count++;
  printf("OPEN %d ERR %d\n",count,errno);return 0;
 }
 if(!strcmp(argv[1],"raise")) {
  struct rlimit bigger={13,13};int rc=setrlimit(RLIMIT_NOFILE,&bigger);
  printf("RAISE %d ERR %d\n",rc,errno);return 0;
 }
 if(!strcmp(argv[1],"args")) {
  for(int i=0;i<argc;i++){printf("ARG %d %zu ",i,strlen(argv[i]));for(unsigned char *p=(unsigned char *)argv[i];*p;p++)printf("%02x",*p);puts("");}
  const char *env=getenv("LIMIT_ENV");printf("ENV %s\n",env?env:"MISSING");return 0;
 }
 if(!strcmp(argv[1],"inherit")) {
  if(argc!=3)return 2;errno=0;int rc=fcntl(atoi(argv[2]),F_GETFD);printf("INHERIT %d ERR %d\n",rc,errno);return 0;
 }
 if(!strcmp(argv[1],"marker")) {
  if(argc!=3)return 2;int fd=open(argv[2],O_CREAT|O_EXCL|O_WRONLY,0600);if(fd<0)return 4;close(fd);return 0;
 }
 if(!strcmp(argv[1],"busy")) {for(;;)usleep(1000);}
 if(!strcmp(argv[1],"flood")) {for(;;)puts("0123456789012345678901234567890123456789");}
 if(!strcmp(argv[1],"descendant")) {
  pid_t pid=fork();if(pid<0)return 4;
  if(!pid){struct rlimit child;if(getrlimit(RLIMIT_NOFILE,&child))_exit(5);printf("CHILD %llu %llu\n",(unsigned long long)child.rlim_cur,(unsigned long long)child.rlim_max);fflush(stdout);_exit(0);}
  int status;if(waitpid(pid,&status,0)!=pid)return 4;return WIFEXITED(status)?WEXITSTATUS(status):6;
 }
 return 2;
}
