#pragma once

#include <stdint.h>

class ButtonDebouncer {
 public:
  ButtonDebouncer(uint32_t debounce_ms, bool pressed, uint32_t now)
      : debounce_ms_(debounce_ms), changed_at_(now), sample_(pressed), pressed_(pressed) {}

  bool update(bool sample, uint32_t now) {
    if (sample != sample_) {
      sample_ = sample;
      changed_at_ = now;
    }
    if (sample_ != pressed_ && static_cast<uint32_t>(now - changed_at_) >= debounce_ms_) {
      pressed_ = sample_;
      return pressed_;
    }
    return false;
  }

  bool pressed() const { return pressed_; }

 private:
  const uint32_t debounce_ms_;
  uint32_t changed_at_;
  bool sample_;
  bool pressed_;
};
