// Original SDK-interface adapter. No Adobe implementation is redistributed.
#ifndef UNISON_MEMORY_ALLOCATOR_H
#define UNISON_MEMORY_ALLOCATOR_H
#include "memory_budget.h"
#include "dng_memory.h"
#include "dng_exceptions.h"
#include <utility>
class UnisonMemoryAllocator final : public dng_memory_allocator {
  unison_memory::Budget budget_;
  class Block final : public dng_memory_block {
    void *backing_=nullptr;
  public:
    Block(uint32 size,const unison_memory::Budget &budget):dng_memory_block(size) {
      // Preserve the actual SDK's checked padding/alignment API, including AVX.
      backing_=budget.try_malloc(PhysicalSize());
      if(!backing_)ThrowMemoryFull();
      SetBuffer(backing_);
    }
    ~Block() override {unison_memory::Budget::free(backing_);}
    static void operator delete(void *pointer) noexcept {
      unison_memory::Budget::free(pointer);
    }
  };
public:
  explicit UnisonMemoryAllocator(std::size_t bytes):budget_(bytes) {}
  explicit UnisonMemoryAllocator(unison_memory::Budget budget):budget_(std::move(budget)) {}
  dng_memory_block *Allocate(uint32 size) override {
    void *storage=budget_.try_malloc(sizeof(Block));
    if(!storage)ThrowMemoryFull();
    try {return ::new(storage) Block(size,budget_);}
    catch(...) {unison_memory::Budget::free(storage);throw;}
  }
  // This callback is also used by the SDK's C JPEG XL allocator bridge. Never
  // throw through C codec frames: return null on exhausted/failed allocation.
  void *Malloc(size_t bytes) noexcept override {return budget_.try_malloc(bytes);}
  void Free(void *pointer) noexcept override {unison_memory::Budget::free(pointer);}
  unison_memory::Usage usage() const {return budget_.usage();}
};
#endif
