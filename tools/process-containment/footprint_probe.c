/* Original disposable self-task observation, never a production limiter. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#ifdef __APPLE__
#include <mach/mach.h>
#include <mach/task.h>
#include <mach/task_info.h>
static void observation(const char *stage,size_t touched) {
  task_vm_info_data_t info;
  mach_msg_type_number_t count=TASK_VM_INFO_COUNT;
  kern_return_t result=task_info(mach_task_self(),TASK_VM_INFO,(task_info_t)&info,&count);
  if(result==KERN_SUCCESS)
    printf("{\"stage\":\"%s\",\"touched\":%zu,\"resident_size\":%llu,\"phys_footprint\":%llu}\n",
      stage,touched,(unsigned long long)info.resident_size,(unsigned long long)info.phys_footprint);
  else printf("{\"stage\":\"%s\",\"task_info_error\":%d}\n",stage,result);
  fflush(stdout);
}
#endif
int main(int argc,char **argv) {
  if(argc!=2 || (strcmp(argv[1],"baseline")&&strcmp(argv[1],"self-limit")))return 2;
#ifdef __APPLE__
  printf("{\"pid\":%ld,\"scope\":\"self-task only, 32MiB maximum, observation not RSS enforcement\"}\n",(long)getpid());
  fflush(stdout);observation("before",0);
  if(!strcmp(argv[1],"self-limit")) {
    int old_limit=0;
    kern_return_t result=task_set_phys_footprint_limit(mach_task_self(),16,&old_limit);
    printf("{\"task_set_phys_footprint_limit_result\":%d,\"requested_MiB\":16,\"old_limit\":%d}\n",result,old_limit);
    fflush(stdout);
    if(result!=KERN_SUCCESS)return 0;
  }
  const size_t bytes=32U*1024U*1024U;
  long page=sysconf(_SC_PAGESIZE);if(page<=0||page>1024*1024)return 3;
  volatile unsigned char *memory=malloc(bytes);if(!memory)return 4;
  for(size_t offset=0;offset<bytes;offset+=(size_t)page) {
    memory[offset]=(unsigned char)(offset/(size_t)page);
    if((offset+(size_t)page)%(1024U*1024U)==0)observation("touch",offset+(size_t)page);
  }
  observation("completed",bytes);free((void *)memory);return 0;
#else
  puts("{\"platform\":\"unsupported\",\"scope\":\"no self-task API invoked\"}");return 0;
#endif
}
