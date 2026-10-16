// Original Unison code. This scheduler has no Adobe or codec dependency.
#ifndef UNISON_AREA_SCHEDULER_H
#define UNISON_AREA_SCHEDULER_H

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <exception>
#include <functional>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>

namespace unison_area {

struct Rect {
  int32_t top, left, bottom, right;
};

// This is a total CPU-thread allowance, including the calling thread. Nested
// codec/area operations must use one thread while one of these scopes is live.
inline thread_local unsigned execution_depth = 0;
class ExecutionScope {
public:
  ExecutionScope() { ++execution_depth; }
  ~ExecutionScope() { --execution_depth; }
  ExecutionScope(const ExecutionScope &) = delete;
  ExecutionScope &operator=(const ExecutionScope &) = delete;
};
inline uint32_t available_threads(uint32_t requested) {
  if (!requested || requested > 128) throw std::invalid_argument("thread allowance must be 1..128");
  return execution_depth ? 1 : requested;
}

// Use disjoint strips, with interior edges on the task's unit-cell lattice
// relative to the destination origin. ProcessOnThread remains responsible for
// the SDK's repeating-tile patterns, tile order and maximum tile dimensions.
inline std::vector<Rect> partition(Rect area, uint32_t requested,
                                   uint32_t task_max, uint32_t min_area,
                                   int32_t unit_v, int32_t unit_h) {
  requested = available_threads(requested);
  if (!task_max || unit_v <= 0 || unit_h <= 0)
    throw std::invalid_argument("invalid task thread or unit-cell constraint");
  const int64_t height = int64_t(area.bottom) - area.top;
  const int64_t width = int64_t(area.right) - area.left;
  if (height < 0 || width < 0) throw std::invalid_argument("inverted task rectangle");
  if (!height || !width) return {area};
  // Each dimension can span at most UINT32_MAX, whose square fits uint64_t.
  const uint64_t pixels = uint64_t(height) * uint64_t(width);
  const uint64_t profitable = std::max<uint64_t>(1, pixels / std::max<uint32_t>(1, min_area));
  const uint64_t rows = uint64_t(height) / uint32_t(unit_v);
  const uint64_t cols = uint64_t(width) / uint32_t(unit_h);
  const bool vertical = rows >= cols;
  const uint64_t cells = vertical ? rows : cols;
  const uint32_t count = uint32_t(std::max<uint64_t>(1,
    std::min<uint64_t>({requested, task_max, profitable, cells})));
  std::vector<Rect> result;
  result.reserve(count);
  int32_t edge = vertical ? area.top : area.left;
  const int64_t origin = edge;
  const int64_t unit = vertical ? unit_v : unit_h;
  for (uint32_t index = 0; index < count; ++index) {
    const int32_t next = index + 1 == count ? (vertical ? area.bottom : area.right)
      : int32_t(origin + int64_t((cells * (index + 1)) / count) * unit);
    Rect strip = area;
    if (vertical) { strip.top = edge; strip.bottom = next; }
    else { strip.left = edge; strip.right = next; }
    result.push_back(strip);
    edge = next;
  }
  return result;
}

class Control {
  std::atomic<bool> stopped_{false};
public:
  bool stopped() const noexcept { return stopped_.load(std::memory_order_acquire); }
  void stop() noexcept { stopped_.store(true, std::memory_order_release); }
};

// These are callback-frame observations, not OS thread or whole-process CPU
// accounting. Nested callbacks can share one thread. A snapshot is coherent
// only after the synchronous owner has joined all of its work.
struct ActivitySnapshot {
  uint64_t tasks, start_successes, finish_calls, process_calls;
  uint64_t active_callbacks, peak_callbacks, max_partition;
};
class Activity {
  std::atomic<uint64_t> tasks_{0}, starts_{0}, finishes_{0}, calls_{0};
  std::atomic<uint64_t> active_{0}, peak_{0}, partition_{0};
  static void maximum(std::atomic<uint64_t> &target, uint64_t value) noexcept {
    auto prior = target.load(std::memory_order_relaxed);
    while (prior < value && !target.compare_exchange_weak(prior, value,
            std::memory_order_relaxed, std::memory_order_relaxed)) {}
  }
public:
  void task(uint64_t parts) noexcept { ++tasks_; maximum(partition_, parts); }
  void started() noexcept { ++starts_; }
  void finishing() noexcept { ++finishes_; }
  void enter() noexcept { ++calls_; maximum(peak_, active_.fetch_add(1) + 1); }
  void leave() noexcept { --active_; }
  ActivitySnapshot snapshot() const noexcept {
    return {tasks_.load(), starts_.load(), finishes_.load(), calls_.load(),
            active_.load(), peak_.load(), partition_.load()};
  }
};

struct Callbacks {
  std::function<void(uint32_t, Control &)> start;
  std::function<void(uint32_t, Rect, Control &)> process;
  std::function<void(uint32_t)> finish;
  Activity *activity = nullptr; // borrowed through the synchronous join only
};
using Launcher = std::function<std::thread(std::function<void()>)>;

// Synchronous ownership: Start once; every launched worker joins; Finish once
// after successful Start even on launch, processing or cancellation failure.
// Start's own partial-failure cleanup belongs to the task, as in SDK Perform.
// A processing/launch exception takes precedence over a secondary Finish error.
inline void run(const std::vector<Rect> &parts, const Callbacks &task,
                const Launcher &launch = [](std::function<void()> fn) {
                  return std::thread(std::move(fn));
                }) {
  if (parts.empty() || parts.size() > 128 || !task.start || !task.process || !task.finish)
    throw std::invalid_argument("invalid area task callbacks or partition count");
  // Allocation failure here occurs before task-owned resources are acquired.
  std::vector<std::thread> workers;
  workers.reserve(parts.size() - 1);
  Control control;
  std::mutex error_mutex;
  std::exception_ptr first_error;
  auto fail = [&] {
    const auto error = std::current_exception();
    std::lock_guard<std::mutex> lock(error_mutex);
    if (!first_error) first_error = error;
    control.stop();
  };
  const uint32_t count = uint32_t(parts.size());
  ExecutionScope caller_scope;
  if (task.activity) task.activity->task(count);
  task.start(count, control);
  if (task.activity) task.activity->started();
  auto process = [&](uint32_t index) {
    ExecutionScope scope;
    if (control.stopped()) return;
    struct ObservedCallback {
      Activity *activity;
      explicit ObservedCallback(Activity *value) : activity(value) {
        if (activity) activity->enter();
      }
      ~ObservedCallback() { if (activity) activity->leave(); }
    } observed(task.activity);
    try { task.process(index, parts[index], control); }
    catch (...) { fail(); }
  };
  try {
    for (uint32_t index = 1; index < count; ++index)
      workers.push_back(launch([&, index] { process(index); }));
    process(0);
  } catch (...) { fail(); }
  // std::thread objects are exclusively owned here and always joined by their
  // creating caller, never from their own worker. No task borrow survives run.
  for (auto &worker : workers) worker.join();
  if (task.activity) task.activity->finishing();
  try { task.finish(count); } catch (...) { fail(); }
  if (first_error) std::rethrow_exception(first_error);
}

} // namespace unison_area
#endif
