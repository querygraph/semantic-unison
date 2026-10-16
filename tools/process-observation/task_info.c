/* Metadata observation only. The caller must retain PID ownership separately. */
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef __APPLE__
#include <libproc.h>
#include <sys/proc_info.h>
#endif
int main(int argc, char **argv) {
  if (argc != 2 || !argv[1][0] || argv[1][0] == '0') return 64;
  for (const char *p=argv[1]; *p; ++p) if (*p<'0' || *p>'9') return 64;
  errno=0; char *end=NULL; long pid=strtol(argv[1],&end,10);
  if (errno || !end || *end || pid<=0 || pid>INT_MAX) return 64;
#ifdef __APPLE__
  struct proc_taskinfo info;
  errno=0;
  int n=proc_pidinfo((int)pid,PROC_PIDTASKINFO,0,&info,sizeof info);
  if (n != sizeof info) {
    printf("{\"available\":false,\"pid\":%ld,\"returned_bytes\":%d,\"errno\":%d}\n",pid,n,errno);
    return 0;
  }
  if (info.pti_threadnum<1 || info.pti_numrunning<0) return 65;
  printf("{\"available\":true,\"pid\":%ld,\"backend\":\"Darwin-PROC_PIDTASKINFO\","
         "\"resident_bytes\":%" PRIu64 ",\"virtual_bytes\":%" PRIu64 ","
         "\"threads\":%d,\"running_threads\":%d,"
         "\"total_user_native_units\":%" PRIu64 ",\"total_system_native_units\":%" PRIu64 "}\n",
         pid,info.pti_resident_size,info.pti_virtual_size,info.pti_threadnum,
         info.pti_numrunning,info.pti_total_user,info.pti_total_system);
#else
  printf("{\"available\":false,\"pid\":%ld,\"reason\":\"platform-unqualified\"}\n",pid);
#endif
  return 0;
}
