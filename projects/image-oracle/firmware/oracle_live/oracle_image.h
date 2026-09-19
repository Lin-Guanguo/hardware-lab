#pragma once

#include <stddef.h>
#include <stdint.h>

inline void resize_rgb565(const uint16_t *source, size_t width, size_t height,
                          uint16_t *destination, size_t out_width, size_t out_height) {
  for (size_t y = 0; y < out_height; ++y) {
    for (size_t x = 0; x < out_width; ++x) {
      destination[y * out_width + x] = source[(y * height / out_height) * width + x * width / out_width];
    }
  }
}

inline uint32_t oracle_hash(const uint16_t *pixels, size_t count) {
  uint32_t hash = 2166136261u;
  for (size_t i = 0; i < count; ++i) {
    // Canonical high-byte-first order makes the result independent of CPU endianness.
    hash = (hash ^ (pixels[i] >> 8)) * 16777619u;
    hash = (hash ^ (pixels[i] & 0xff)) * 16777619u;
  }
  return hash;
}

inline bool oracle_answer(uint32_t hash) {
  return (hash & 0x80000000u) != 0;
}
