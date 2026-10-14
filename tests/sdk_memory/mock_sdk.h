// Independently authored SDK-interface surrogate; not Adobe implementation.
#ifndef UNISON_MOCK_MEMORY_SDK_H
#define UNISON_MOCK_MEMORY_SDK_H
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <limits>
using uint32=std::uint32_t;
class MemoryFull:public std::runtime_error {public:MemoryFull():std::runtime_error("memory full") {}};
[[noreturn]] inline void ThrowMemoryFull(){throw MemoryFull();}
class dng_memory_allocator;
class dng_memory_block {
  uint32 size_;
  void *data_=nullptr;
protected:
  explicit dng_memory_block(uint32 size):size_(size) {}
  uint32 PhysicalSize() {
#ifdef MOCK_AVX
    constexpr uint32 padding=160;
#else
    constexpr uint32 padding=64;
#endif
    if(size_>std::numeric_limits<uint32>::max()-padding)throw std::overflow_error("physical size");
    return size_+padding;
  }
  void SetBuffer(void *raw) {
#ifdef MOCK_AVX
    constexpr std::uintptr_t alignment=32;
#else
    constexpr std::uintptr_t alignment=16;
#endif
    data_=reinterpret_cast<void *>((reinterpret_cast<std::uintptr_t>(raw)+alignment-1)&~(alignment-1));
  }
public:
  virtual ~dng_memory_block()=default;
  uint32 LogicalSize() const {return size_;}
  void *Buffer() {return data_;}
};
class dng_memory_allocator {
public:
  virtual ~dng_memory_allocator()=default;
  virtual dng_memory_block *Allocate(uint32)=0;
  virtual void *Malloc(std::size_t)=0;
  virtual void Free(void *)=0;
};
#endif
