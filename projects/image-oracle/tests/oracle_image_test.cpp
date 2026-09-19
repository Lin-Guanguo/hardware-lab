#include <array>
#include <cassert>
#include <iostream>
#include "../firmware/oracle_live/oracle_image.h"

int main() {
  const uint16_t black[] = {0};
  const uint16_t white[] = {0xffff};
  const uint16_t colors[] = {0xf800, 0x07e0, 0x001f};
  assert(oracle_hash(black, 1) == 0x117697cdu);
  assert(oracle_hash(white, 1) == 0xd11ebca3u);
  assert(oracle_hash(colors, 3) == 0xc477088bu);
  assert(!oracle_answer(oracle_hash(black, 1)));
  assert(oracle_answer(oracle_hash(white, 1)));
  std::array<uint16_t, 112 * 84> image;
  image.fill(0x07e0);
  for (int i = 0; i < 100; ++i) {
    assert(oracle_hash(image.data(), image.size()) == 0x35d106c5u);
    assert(!oracle_answer(oracle_hash(image.data(), image.size())));
  }
  image.fill(0xf800);
  assert(oracle_hash(image.data(), image.size()) == 0xdd591dc5u);
  assert(oracle_answer(oracle_hash(image.data(), image.size())));

  const uint16_t source[] = {1, 2, 3, 4};
  uint16_t enlarged[16] = {};
  resize_rgb565(source, 2, 2, enlarged, 4, 4);
  const uint16_t expected[] = {1,1,2,2, 1,1,2,2, 3,3,4,4, 3,3,4,4};
  for (size_t i = 0; i < 16; ++i) assert(enlarged[i] == expected[i]);
  uint16_t reduced[4] = {};
  resize_rgb565(enlarged, 4, 4, reduced, 2, 2);
  for (size_t i = 0; i < 4; ++i) assert(reduced[i] == source[i]);
  std::cout << "PASS: fixed hash vectors, repeatability, both answers, nearest-neighbor resizing\n";
}
