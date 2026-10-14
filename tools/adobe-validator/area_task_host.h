// Original Unison adapter. Adobe SDK headers/source remain separately obtained.
#ifndef UNISON_AREA_TASK_HOST_H
#define UNISON_AREA_TASK_HOST_H

#include "area_scheduler.h"
#include "dng_abort_sniffer.h"
#include "dng_area_task.h"
#include "dng_exceptions.h"
#include "dng_host.h"
#include <atomic>
#include <memory>
#include <mutex>

class UnisonAreaTaskHost : public dng_host {
  const uint32 requested_threads_;
  std::atomic_flag busy_ = ATOMIC_FLAG_INIT;
  unison_area::Activity activity_;
  std::atomic<uint64_t> reference_tasks_{0};

  class CooperativeSniffer final : public dng_abort_sniffer {
    unison_area::Control &control_;
    dng_abort_sniffer *delegate_;
    std::mutex delegate_mutex_;
  public:
    CooperativeSniffer(unison_area::Control &control, dng_abort_sniffer *delegate)
      : control_(control), delegate_(delegate) {}
    bool ThreadSafe() const override { return true; }
    bool SupportsPriorityWait() const override { return false; }
  protected:
    void Sniff() override {
      if (control_.stopped()) ThrowUserCanceled();
      if (delegate_) {
        if (delegate_->ThreadSafe()) dng_abort_sniffer::SniffForAbort(delegate_);
        else {
          std::lock_guard<std::mutex> lock(delegate_mutex_);
          dng_abort_sniffer::SniffForAbort(delegate_);
        }
      }
      if (control_.stopped()) ThrowUserCanceled();
    }
  };
  class SerializedProgress final : public dng_area_task_progress {
    dng_area_task_progress *delegate_;
    std::mutex mutex_;
  public:
    explicit SerializedProgress(dng_area_task_progress *delegate) : delegate_(delegate) {}
    void FinishedTile(const dng_rect &tile) override {
      std::lock_guard<std::mutex> lock(mutex_);
      delegate_->FinishedTile(tile);
    }
  };
public:
  unison_area::ActivitySnapshot Activity() const noexcept { return activity_.snapshot(); }
  uint64_t ReferenceTasks() const noexcept { return reference_tasks_.load(); }
  explicit UnisonAreaTaskHost(uint32 requested_threads, dng_memory_allocator *allocator = nullptr)
    : dng_host(allocator), requested_threads_(unison_area::available_threads(requested_threads)) {}

  uint32 PerformAreaTaskThreads() override {
    // Includes caller; prevents area-workers × nested-JXL-workers expansion.
    return unison_area::available_threads(requested_threads_);
  }
  void PerformAreaTask(dng_area_task &task, const dng_rect &area,
                       dng_area_task_progress *progress = nullptr) override {
    // Preserve the exact SDK reference path for an explicit one-thread host.
    if (requested_threads_ == 1) {
      ++reference_tasks_;
      dng_host::PerformAreaTask(task, area, progress);
      return;
    }
    const bool nested = unison_area::execution_depth != 0;
    if (!nested && busy_.test_and_set(std::memory_order_acquire))
      throw std::logic_error("concurrent entry to synchronous SDK area host");
    struct BusyRelease {
      std::atomic_flag &flag;
      bool acquired;
      ~BusyRelease() { if (acquired) flag.clear(std::memory_order_release); }
    } busy_release{busy_, !nested};
    const dng_point tile = task.FindTileSize(area);
    const dng_point unit = task.UnitCell();
    const auto parts = unison_area::partition(
      {area.t, area.l, area.b, area.r}, PerformAreaTaskThreads(),
      task.MaxThreads(), task.MinTaskArea(), unit.v, unit.h);
    SerializedProgress serial_progress(progress);
    // One shared sniffer serializes delegates which are not ThreadSafe. Its
    // stop flag is borrowed only until run has joined all task workers.
    std::unique_ptr<CooperativeSniffer> sniffer;
    unison_area::run(parts, {
      [&](uint32 count, unison_area::Control &control) {
        sniffer.reset(new CooperativeSniffer(control, Sniffer()));
        task.Start(count, area, tile, &Allocator(), Sniffer());
      },
      [&](uint32 index, unison_area::Rect part, unison_area::Control &control) {
        (void) control;
        task.ProcessOnThread(index, dng_rect(part.top, part.left, part.bottom, part.right),
          tile, sniffer.get(), progress ? &serial_progress : nullptr);
      },
      [&](uint32 count) { task.Finish(count); },
      &activity_
    });
  }
};
#endif
