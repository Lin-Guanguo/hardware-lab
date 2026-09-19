#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
    printf 'This setup pins the macOS ARM64 toolchain.\n' >&2
    exit 1
fi

tools_dir="$project_dir/downloads/tools"
archive=arduino-cli_1.5.1_macOS_ARM64.tar.gz
mkdir -p "$tools_dir"
if [[ ! -f "$tools_dir/$archive" ]]; then
    curl --fail --location --retry 2 \
        "https://github.com/arduino/arduino-cli/releases/download/v1.5.1/$archive" \
        --output "$tools_dir/$archive"
fi
printf '%s  %s\n' \
    cb952e8c1621c95ef5f1d17831c945e3d0ec5973f89c557a7ec8feb9c4f7d4c9 \
    "$tools_dir/$archive" | shasum -a 256 --check
tar -xzf "$tools_dir/$archive" -C "$tools_dir"

index_url=https://espressif.github.io/arduino-esp32/package_esp32_index.json
bash "$project_dir/scripts/arduino.sh" version
bash "$project_dir/scripts/arduino.sh" core update-index --additional-urls "$index_url"
bash "$project_dir/scripts/arduino.sh" core install esp32:esp32@3.3.11 --additional-urls "$index_url"
