#!/bin/bash
set -euo pipefail
lab_root="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$(uname -s)" != "Darwin" ]]; then
  printf '%s\n' 'BLOCKED: macOS with Xcode/Command Line Tools is required. No Mac build was attempted.' >&2
  exit 78
fi
if ! command -v xcrun >/dev/null 2>&1; then
  printf '%s\n' 'BLOCKED: xcrun is unavailable. Install Apple developer tools before building.' >&2
  exit 78
fi
sdk_path="$(xcrun --sdk macosx --show-sdk-path)"
machine_arch="$(uname -m)"
target_triple="$machine_arch-apple-macos14.0"
output_root="$lab_root/build"
mkdir -p "$output_root"
bash "$lab_root/Fixture/build.sh"
app_dir="$output_root/Controller.app"
mkdir -p "$app_dir/Contents/MacOS"
cp "$lab_root/Controller/Info.plist" "$app_dir/Contents/Info.plist"
xcrun --sdk macosx swiftc -swift-version 5 -sdk "$sdk_path" \
  -target "$target_triple" -framework AppKit -framework ApplicationServices \
  "$lab_root/Controller/Sources/Geometry.swift" \
  "$lab_root/Controller/Sources/Diagnostics.swift" \
  "$lab_root/Controller/Sources/main.swift" \
  -o "$app_dir/Contents/MacOS/MenuValidationController"
xcrun --sdk macosx swiftc -swift-version 5 -sdk "$sdk_path" \
  -target "$target_triple" -framework AppKit -framework ApplicationServices \
  "$lab_root/Controller/Sources/Diagnostics.swift" "$lab_root/Observer/main.swift" \
  -o "$output_root/observer"
xcrun --sdk macosx clang -fobjc-arc -isysroot "$sdk_path" \
  -mmacosx-version-min=14.0 -framework Foundation \
  "$lab_root/PrivateProbe/main.m" -o "$output_root/private-probe"
printf '%s\n' 'Build finished. Apps have not been launched; this is not a behavior test.'
printf '%s\n' "$output_root/Fixture.app" "$output_root/Controller.app" "$output_root/observer" "$output_root/private-probe"

