#include <cassert>
#include <cstdint>
#include <iostream>

#include "../firmware/display_serial/button_debouncer.h"

int main() {
  ButtonDebouncer button(10, false, 0);
  assert(!button.update(true, 1));
  assert(!button.update(false, 3));
  assert(!button.update(true, 5));
  assert(!button.update(false, 7));
  assert(!button.update(true, 9));
  assert(!button.update(true, 18));
  assert(button.update(true, 19));
  assert(button.pressed());
  assert(!button.update(true, 2000));
  assert(!button.update(false, 2001));
  assert(!button.update(true, 2005));
  assert(!button.update(true, 2020));
  assert(button.pressed());
  assert(!button.update(false, 2021));
  assert(!button.update(false, 2031));
  assert(!button.pressed());
  assert(!button.update(true, 2032));
  assert(button.update(true, 2042));

  ButtonDebouncer rapid(10, false, 0);
  unsigned presses = 0;
  for (uint32_t ms = 0; ms < 3000; ++ms) {
    const bool pressed = ms % 30 < 15;
    if (rapid.update(pressed, ms)) ++presses;
  }
  assert(presses == 100);

  ButtonDebouncer rollover(10, false, UINT32_MAX - 5);
  assert(!rollover.update(true, UINT32_MAX - 5));
  assert(!rollover.update(true, 3));
  assert(rollover.update(true, 4));
  assert(!rollover.update(true, 5));

  ButtonDebouncer held_at_boot(10, true, 0);
  assert(!held_at_boot.update(true, 1000));
  assert(!held_at_boot.update(false, 1001));
  assert(!held_at_boot.update(false, 1011));
  assert(!held_at_boot.update(true, 1012));
  assert(held_at_boot.update(true, 1022));
  std::cout << "PASS: bounce, hold, release, 100 rapid presses, timer rollover, held at boot\n";
}
