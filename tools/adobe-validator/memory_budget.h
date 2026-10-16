// Original Unison quota for requested backing allocations, not process RSS.
#ifndef UNISON_MEMORY_BUDGET_H
#define UNISON_MEMORY_BUDGET_H
#include <cstddef>
#include <cstdlib>
#include <limits>
#include <memory>
#include <mutex>
#include <new>
#include <stdexcept>
namespace unison_memory {
struct Usage { std::size_t limit, used, peak, live, denied; };
class State {
  const std::size_t limit_;
  mutable std::mutex mutex_;
  std::size_t used_=0, peak_=0, live_=0, denied_=0;
public:
  explicit State(std::size_t limit):limit_(limit) {
    if(!limit)throw std::invalid_argument("memory budget must be positive");
  }
  bool reserve(std::size_t bytes) noexcept {
    try {
      std::lock_guard<std::mutex> lock(mutex_);
      if(bytes>limit_-used_) {++denied_;return false;}
      used_+=bytes;++live_;if(used_>peak_)peak_=used_;return true;
    } catch(...) {return false;}
  }
  void release(std::size_t bytes) noexcept {
    try {
      std::lock_guard<std::mutex> lock(mutex_);
      if(bytes>used_ || !live_)std::terminate();
      used_-=bytes;--live_;
    } catch(...) {std::terminate();}
  }
  Usage usage() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return {limit_,used_,peak_,live_,denied_};
  }
};
class Budget {
  struct alignas(std::max_align_t) Header {
    std::shared_ptr<State> state;
    std::size_t charged;
  };
  std::shared_ptr<State> state_;
public:
  explicit Budget(std::size_t bytes):state_(std::make_shared<State>(bytes)) {}
  static constexpr std::size_t overhead() {return sizeof(Header);}
  Usage usage() const {return state_->usage();}
  void *try_malloc(std::size_t bytes) const noexcept {
    if(bytes>std::numeric_limits<std::size_t>::max()-sizeof(Header))return nullptr;
    const std::size_t charged=bytes+sizeof(Header);
    if(!state_->reserve(charged))return nullptr;
    void *raw=std::malloc(charged);
    if(!raw){state_->release(charged);return nullptr;}
    // Copying shared_ptr and constructing these fields cannot throw. Its owned
    // state keeps the charge alive even if the Budget/host is already gone.
    auto *header=::new(raw) Header{state_,charged};
    return header+1;
  }
  static void free(void *pointer) noexcept {
    if(!pointer)return;
    auto *header=static_cast<Header *>(pointer)-1;
    auto state=header->state;const auto charged=header->charged;
    header->~Header();std::free(header);
    // Retire only after freeing backing memory; a concurrent allocator cannot
    // reuse the credits while this backing allocation is still live.
    state->release(charged);
  }
};
}
#endif
