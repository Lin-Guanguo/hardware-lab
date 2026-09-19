#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ARDUINO_DIRECTORIES_DATA="$project_dir/downloads/arduino/data"
export ARDUINO_DIRECTORIES_DOWNLOADS="$project_dir/downloads/arduino/staging"
export ARDUINO_DIRECTORIES_USER="$project_dir/downloads/arduino/user"

exec "$project_dir/downloads/tools/arduino-cli" "$@"
