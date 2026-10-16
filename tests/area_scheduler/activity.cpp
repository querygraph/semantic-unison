// Original deterministic callback observation tests; no SDK or codec linkage.
#include "area_scheduler.h"
#include <chrono>
#include <iostream>

using namespace unison_area;
static void check(bool condition) {
  if (!condition) throw std::runtime_error("activity observation mismatch");
}
template<class F> static void fails(F fn) {
  try { fn(); } catch (const std::runtime_error &) { return; }
  throw std::logic_error("expected failure absent");
}
int main() {
  for (unsigned lanes : {1, 6, 18}) {
    Activity activity;
    std::atomic<unsigned> entered{0};
    std::vector<Rect> parts(lanes, {0, 0, 1, 1});
    run(parts, {
      [](uint32_t, Control &) {},
      [&](uint32_t, Rect, Control &) {
        ++entered;
        auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        while (entered != lanes) {
          if (std::chrono::steady_clock::now() >= deadline)
            throw std::runtime_error("bounded simultaneous wave timed out");
          std::this_thread::yield();
        }
      },
      [&](uint32_t) { check(activity.snapshot().active_callbacks == 0); },
      &activity
    });
    auto a = activity.snapshot();
    check(a.tasks == 1 && a.start_successes == 1 && a.finish_calls == 1);
    check(a.process_calls == lanes && a.peak_callbacks == lanes
          && a.active_callbacks == 0 && a.max_partition == lanes);
  }
  Activity start;
  fails([&] { run({{0, 0, 1, 1}}, {
    [](uint32_t, Control &) { throw std::runtime_error("start failed"); },
    [](uint32_t, Rect, Control &) {}, [](uint32_t) {}, &start}); });
  check(start.snapshot().tasks == 1 && start.snapshot().start_successes == 0
        && start.snapshot().finish_calls == 0 && start.snapshot().active_callbacks == 0);
  Activity processing;
  fails([&] { run(std::vector<Rect>(6, {0, 0, 1, 1}), {
    [](uint32_t, Control &) {},
    [](uint32_t, Rect, Control &) { throw std::runtime_error("process failed"); },
    [](uint32_t) {}, &processing}); });
  auto a = processing.snapshot();
  check(a.start_successes == 1 && a.finish_calls == 1 && a.active_callbacks == 0
        && a.process_calls >= 1 && a.process_calls <= 6 && a.max_partition == 6);
  Activity launching;
  unsigned launches = 0;
  fails([&] { run(std::vector<Rect>(6, {0, 0, 1, 1}), {
    [](uint32_t, Control &) {}, [](uint32_t, Rect, Control &) {},
    [](uint32_t) {}, &launching}, [&](std::function<void()> fn) {
      if (++launches == 2) throw std::runtime_error("launch failed");
      return std::thread(std::move(fn));
    }); });
  check(launching.snapshot().active_callbacks == 0 && launching.snapshot().finish_calls == 1);
  Activity finishing;
  fails([&] { run({{0, 0, 1, 1}}, {
    [](uint32_t, Control &) {}, [](uint32_t, Rect, Control &) {},
    [](uint32_t) { throw std::runtime_error("finish failed"); }, &finishing}); });
  check(finishing.snapshot().finish_calls == 1 && finishing.snapshot().active_callbacks == 0);
  std::cout << "PASS 1/6/18 callback waves and start/process/launch/finish failure observations\n";
}
