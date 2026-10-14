#include "memory_budget.h"
#include "memory_allocator.h"
#include <atomic>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>
#include <memory>
using unison_memory::Budget;
static_assert(noexcept(std::declval<UnisonMemoryAllocator &>().Malloc(0)),"codec callback must not unwind");
static_assert(noexcept(std::declval<UnisonMemoryAllocator &>().Free(nullptr)),"codec free must not unwind");
static unsigned checks=0;
static void check(bool condition,const char *label) {++checks;if(!condition)throw std::runtime_error(label);}
static void scalar() {
 bool rejected=false;try{Budget invalid(0);}catch(const std::invalid_argument &){rejected=true;}check(rejected,"zero limit rejected");
 Budget budget(512);const auto overhead=Budget::overhead();check(overhead>0 && overhead<512,"header charge bounded");
 void *p=budget.try_malloc(512-overhead);check(p!=nullptr,"exact budget allocation");
 check(budget.usage().used==512 && budget.usage().live==1,"exact header accounting");
 check(budget.try_malloc(0)==nullptr,"exhausted zero-byte allocation declined");
 check(budget.usage().used==512,"denial did not change debit");
 Budget::free(p);check(budget.usage().used==0 && budget.usage().live==0,"release settled");
 check(budget.try_malloc(std::numeric_limits<std::size_t>::max())==nullptr,"size addition overflow rejected");
 p=budget.try_malloc(0);check(p!=nullptr,"zero payload allocates owned header");
 check(budget.usage().used==overhead,"zero payload cannot evade quota");Budget::free(p);Budget::free(nullptr);
 check(budget.usage().used==0,"null/zero releases settle");
 void *survivor=nullptr;{Budget transient(512);survivor=transient.try_malloc(128);check(survivor!=nullptr,"transient quota allocation");}Budget::free(survivor);
 check(budget.try_malloc(513)==nullptr,"oversized request rejected");
}
static void adapter() {
 UnisonMemoryAllocator allocator(2048);
 dng_memory_allocator &interface=allocator;
 std::unique_ptr<dng_memory_block> block(interface.Allocate(256));
 check(block->LogicalSize()==256,"SDK logical size");
 check(reinterpret_cast<std::uintptr_t>(block->Buffer())%
#ifdef MOCK_AVX
 32
#else
 16
#endif
 ==0,"SDK SIMD alignment");
 std::memset(block->Buffer(),0x5a,256);
 std::unique_ptr<dng_memory_block> copy(interface.Allocate(256));
 std::memcpy(copy->Buffer(),block->Buffer(),256);check(std::memcmp(copy->Buffer(),block->Buffer(),256)==0,"independent cloned data");
 const auto used=allocator.usage().used;check(used>512,"padding/object/header accounted");
 auto *raw=interface.Malloc(100);check(raw!=nullptr,"C codec callback allocation");interface.Free(raw);interface.Free(nullptr);
 check(allocator.usage().used==used,"C callback paired free");
 check(interface.Malloc(4096)==nullptr,"C codec exhaustion returns null");
 bool rejected=false;try{std::unique_ptr<dng_memory_block> too_big(interface.Allocate(4096));}catch(const MemoryFull &){rejected=true;}check(rejected,"SDK block exhaustion throws MemoryFull");
 check(allocator.usage().used==used,"failed block construction rolls object quota back");
 rejected=false;try{std::unique_ptr<dng_memory_block> too_big(interface.Allocate(UINT32_MAX));}catch(const std::overflow_error &){rejected=true;}check(rejected,"SDK physical overflow preserved");
 check(allocator.usage().used==used,"overflow construction rolls quota back");
 copy.reset();block.reset();check(allocator.usage().used==0 && allocator.usage().live==0,"virtual delete retires object and backing");
 dng_memory_block *survivor=nullptr;{UnisonMemoryAllocator temporary(2048);survivor=temporary.Allocate(64);}
 check(survivor->LogicalSize()==64,"block remains valid after allocator destruction");delete survivor;
}
static void shared_adapters() {
 Budget root(1024);UnisonMemoryAllocator first(root),second(root);
 auto *a=first.Malloc(400),*b=second.Malloc(400);
 check(a && b,"two adapters share an injected pool");
 check(root.usage().used==800+2*Budget::overhead(),"shared adapter debit is combined");
 check(first.Malloc(200)==nullptr,"second adapter cannot mint another allowance");
 first.Free(a);check(root.usage().used==400+Budget::overhead(),"shared adapter partial release");
 second.Free(b);check(root.usage().used==0,"shared adapter pool retires fully");
}
static void concurrent(unsigned lanes) {
 Budget budget(4096);std::atomic<unsigned> errors{0},start{0};
 auto work=[&](unsigned lane) {
  start.fetch_add(1);while(start.load()<lanes)std::this_thread::yield();
  for(unsigned i=0;i<2000;i++) {
   auto *p=budget.try_malloc(128+(i+lane)%128);
   if(p) {std::memset(p,int(lane),128);auto usage=budget.usage();if(usage.used>usage.limit)errors.fetch_add(1);Budget::free(p);}
  }
 };
 std::vector<std::thread> threads;
 for(unsigned i=1;i<lanes;i++)threads.emplace_back(work,i);
 work(0);for(auto &thread:threads)thread.join();
 check(errors.load()==0,"concurrent quota never exceeds capacity");auto usage=budget.usage();
 check(usage.used==0 && usage.live==0 && usage.peak<=usage.limit,"concurrent allocations fully retire");
}
static void pressure_wave() {
 constexpr unsigned lanes=18,capacity=12;
 Budget budget(capacity*(256+Budget::overhead()));
 std::atomic<unsigned> allocated{0},sampled{0},successes{0},errors{0};
 auto work=[&] {
  auto *p=budget.try_malloc(256);if(p)successes.fetch_add(1);
  allocated.fetch_add(1);while(allocated.load()<lanes)std::this_thread::yield();
  const auto usage=budget.usage();
  if(usage.used!=capacity*(256+Budget::overhead()) || usage.live!=capacity)errors.fetch_add(1);
  sampled.fetch_add(1);while(sampled.load()<lanes)std::this_thread::yield();
  Budget::free(p);
 };
 std::vector<std::thread> threads;for(unsigned i=1;i<lanes;i++)threads.emplace_back(work);
 work();for(auto &t:threads)t.join();
 check(successes.load()==capacity && errors.load()==0,"18-lane pressure wave independently matches exact capacity");
 check(budget.usage().used==0 && budget.usage().live==0,"pressure wave settles all reservations");
}
int main() {
 try {scalar();adapter();shared_adapters();for(unsigned lanes:{1u,6u,18u})concurrent(lanes);pressure_wave();
  std::cout<<"PASS "<<checks<<" budget/SDK-interface controls; 50000 concurrent allocation attempts; no Adobe linkage\n";return 0;
 }catch(const std::exception &error){std::cerr<<error.what()<<"\n";return 1;}
}
