#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$project_dir/scripts/arduino.sh" lib install --no-deps \
    'Adafruit BusIO@1.17.4' \
    'Adafruit GFX Library@1.12.6' \
    'Adafruit ST7735 and ST7789 Library@1.11.0'
bash "$project_dir/scripts/arduino.sh" compile \
    --fqbn 'esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=cdc,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi' \
    --build-path "$project_dir/build/oracle_live" \
    --warnings default \
    "$project_dir/firmware/oracle_live"
