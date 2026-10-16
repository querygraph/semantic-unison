// Adobe-free synthetic scheduler controls. No SDK/codec symbols or payloads.
#include "area_scheduler.h"
#include <climits>
#include <iostream>
#include <set>
#include <string>

using namespace unison_area;
static unsigned assertions = 0;
static void check(bool condition, const char *description) {
  ++assertions;
  if (!condition) throw std::runtime_error(description);
}
template<class Fn> static void raises(Fn fn, const std::string &message) {
  bool caught = false;
  try { fn(); }
  catch (const std::exception &error) { caught = error.what() == message; }
  check(caught, message.c_str());
}
static void update_max(std::atomic<unsigned> &maximum, unsigned value) {
  unsigned old = maximum.load();
  while (old < value && !maximum.compare_exchange_weak(old, value)) {}
}

static void partition_controls() {
  const Rect area{-13, 7, 90, 418};
  for (uint32_t budget : {1, 6, 18, 36, 128}) {
    const auto parts = partition(area, budget, 128, 1, 4, 8);
    check(parts.size() <= budget, "partition allowance");
    int32_t edge = area.left;
    uint64_t pixels = 0;
    for (const auto &part : parts) {
      check(part.top == area.top && part.bottom == area.bottom, "strip height");
      check(part.left == edge && part.right > part.left, "strip contiguous and nonempty");
      check(part.right == area.right || (part.right - area.left) % 8 == 0, "unit-cell interior edge");
      edge = part.right;
      pixels += uint64_t(int64_t(part.bottom) - part.top) * uint64_t(int64_t(part.right) - part.left);
    }
    check(edge == area.right && pixels == 103 * 411, "exact rectangle coverage");
  }
  check(partition({0, 0, 1024, 1024}, 18, 4, 1, 1, 1).size() == 4, "task MaxThreads honored");
  check(partition({0, 0, 256, 256}, 18, 128, 65536, 1, 1).size() == 1, "MinTaskArea honored");
  check(partition({0, 0, 16, 288}, 18, 128, 256, 16, 16).size() == 18, "SDK-shaped synthetic range geometry");
  check(partition({0, 0, 1, 1}, 18, 128, 0, 1, 1).size() == 1, "tiny area and zero profitability hint");
  check(partition({9, 10, 9, 10}, 18, 128, 1, 1, 1).size() == 1, "empty area reference count");
  check(partition({INT_MIN, INT_MIN, INT_MAX, INT_MAX}, 128, 128, 1, 1, 1).size() == 128,
        "full signed-coordinate arithmetic without overflow");
  raises([] { partition({2, 0, 1, 1}, 18, 1, 1, 1, 1); }, "inverted task rectangle");
  raises([] { partition({0, 0, 1, 1}, 0, 1, 1, 1, 1); }, "thread allowance must be 1..128");
  raises([] { partition({0, 0, 1, 1}, 129, 1, 1, 1, 1); }, "thread allowance must be 1..128");
  raises([] { partition({0, 0, 1, 1}, 18, 0, 1, 1, 1); }, "invalid task thread or unit-cell constraint");
  raises([] { partition({0, 0, 1, 1}, 18, 1, 1, 0, 1); }, "invalid task thread or unit-cell constraint");
}

static void normal_controls(uint32_t budget) {
  const auto parts = partition({0, 0, 16, int32_t(16 * budget)}, budget, 128, 256, 16, 16);
  std::atomic<unsigned> active{0}, peak{0}, finished{0}, starts{0}, finishes{0};
  std::atomic<unsigned> entered{0};
  std::mutex mutex;
  std::set<uint32_t> indices;
  std::set<std::thread::id> threads;
  const auto caller = std::this_thread::get_id();
  bool caller_worked = false;
  run(parts, {
    [&](uint32_t count, Control &) {
      check(count == budget, "Start count equals partition count");
      check(available_threads(18) == 1, "Start nested codec allowance");
      ++starts;
    },
    [&](uint32_t index, Rect, Control &) {
      update_max(peak, ++active);
      ++entered;
      while (entered.load() != budget) std::this_thread::yield();
      {
        std::lock_guard<std::mutex> lock(mutex);
        check(index < budget && indices.insert(index).second, "unique task thread index");
        threads.insert(std::this_thread::get_id());
        if (std::this_thread::get_id() == caller) caller_worked = index == 0;
        check(available_threads(18) == 1, "area worker nested codec allowance");
      }
      // Nested synchronous tasks get one existing worker and create no peers.
      const auto inner = partition({0, 0, 18, 18}, 18, 128, 1, 1, 1);
      if (inner.size() != 1) throw std::runtime_error("nested area allowance violated");
      run(inner, {
        [](uint32_t, Control &) {},
        [&](uint32_t inner_index, Rect, Control &) {
          if (inner_index != 0 || available_threads(18) != 1)
            throw std::runtime_error("nested codec allowance violated");
        },
        [](uint32_t) {}
      });
      ++finished;
      --active;
    },
    [&](uint32_t count) {
      check(count == budget && active == 0 && finished == budget, "Finish after all workers settled");
      check(available_threads(18) == 1, "Finish nested codec allowance");
      ++finishes;
    }
  });
  check(starts == 1 && finishes == 1, "one Start and one Finish");
  check(caller_worked && threads.size() == budget, "caller included in total threads");
  check(peak <= budget && peak > 0, "bounded processing concurrency");
  check(available_threads(18) == 18 && execution_depth == 0, "top-level allowance restored");
}

static void failure_controls() {
  const auto parts = partition({0, 0, 16, 288}, 18, 128, 256, 16, 16);
  std::atomic<unsigned> active{0}, finishes{0};
  raises([&] {
    run(parts, {
      [](uint32_t, Control &) { throw std::runtime_error("Start failure"); },
      [](uint32_t, Rect, Control &) { throw std::runtime_error("must not Process"); },
      [&](uint32_t) { ++finishes; }
    });
  }, "Start failure");
  check(finishes == 0 && execution_depth == 0, "failed Start owns its partial cleanup");

  unsigned launches = 0;
  raises([&] {
    run(parts, {
      [](uint32_t, Control &) {},
      [&](uint32_t, Rect, Control &control) {
        ++active;
        while (!control.stopped()) std::this_thread::yield();
        --active;
      },
      [&](uint32_t count) { check(active == 0 && count == 18, "launch failure joins before Finish"); ++finishes; }
    }, [&](std::function<void()> fn) {
      if (++launches == 5) throw std::runtime_error("thread creation failure");
      return std::thread(std::move(fn));
    });
  }, "thread creation failure");
  check(finishes == 1 && active == 0 && execution_depth == 0, "launch failure task cleanup once");

  std::atomic<unsigned> entered{0};
  raises([&] {
    run(parts, {
      [](uint32_t, Control &) {},
      [&](uint32_t index, Rect, Control &control) {
        ++active;
        ++entered;
        if (index == 0) { --active; throw std::runtime_error("processing failure"); }
        while (!control.stopped()) std::this_thread::yield();
        --active;
      },
      [&](uint32_t) {
        check(active == 0, "processing failure joins before Finish");
        ++finishes;
        throw std::runtime_error("secondary Finish failure");
      }
    });
  }, "processing failure");
  check(finishes == 2 && active == 0 && entered > 0 && execution_depth == 0, "primary processing error survives Finish error");

  raises([&] {
    run(parts, {
      [](uint32_t, Control &) {},
      [&](uint32_t index, Rect, Control &control) {
        ++active;
        if (index == 0) { control.stop(); --active; throw std::runtime_error("synthetic user canceled"); }
        while (!control.stopped()) std::this_thread::yield();
        --active;
      },
      [&](uint32_t) { check(active == 0, "cancellation joins before Finish"); ++finishes; }
    });
  }, "synthetic user canceled");
  check(finishes == 3 && execution_depth == 0, "canceled task cleanup once");

  raises([&] {
    run({{0, 0, 1, 1}}, {
      [](uint32_t, Control &) {},
      [](uint32_t, Rect, Control &) {},
      [](uint32_t) { throw std::runtime_error("Finish failure"); }
    });
  }, "Finish failure");
  check(execution_depth == 0, "Finish failure restores nesting scope");
  raises([] { run({}, {}); }, "invalid area task callbacks or partition count");
}

int main() {
  try {
    partition_controls();
    for (uint32_t budget : {1, 6, 18, 36, 128}) normal_controls(budget);
    failure_controls();
    std::cout << "PASS " << assertions << " synthetic assertions; no Adobe SDK or codec linkage\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << "\n";
    return 1;
  }
}
