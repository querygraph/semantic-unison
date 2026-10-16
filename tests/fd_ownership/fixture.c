#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <dirent.h>
#include <stdlib.h>
#include <unistd.h>
/* Kernel descriptor census; exclude only the descriptor used for enumeration. */
CAMLprim value fd_ownership_count(value unit)
{
  CAMLparam1(unit);
  DIR *directory = opendir("/dev/fd");
  if (!directory) abort();
  int count = 0, own = dirfd(directory);
  struct dirent *entry;
  while ((entry = readdir(directory))) {
    char *end; long fd = strtol(entry->d_name,&end,10);
    if (end != entry->d_name && !*end && fd != own) ++count;
  }
  if (closedir(directory)) abort();
  CAMLreturn(Val_int(count));
}
