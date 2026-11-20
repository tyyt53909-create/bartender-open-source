#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Fixture requires macOS 14+ and the Apple command-line tools. This host is not macOS; no build was attempted." >&2
    exit 78
fi

FIXTURE_DIR="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="$(cd "$FIXTURE_DIR/.." && pwd)"
FIXTURE_BUILD_DIR="${FIXTURE_BUILD_DIR:-$LAB_DIR/build}"
APP_BUNDLE="$FIXTURE_BUILD_DIR/Fixture.app"
FIXTURE_ARCH="$(uname -m)"
case "$FIXTURE_ARCH" in
    arm64|x86_64) ;;
    *) echo "Unsupported build architecture: $FIXTURE_ARCH" >&2; exit 78 ;;
esac

xcrun --sdk macosx --find swiftc >/dev/null
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources"
xcrun --sdk macosx swiftc -swift-version 5 \
    -target "$FIXTURE_ARCH-apple-macosx14.0" \
    -framework AppKit \
    "$FIXTURE_DIR/Sources/main.swift" \
    -o "$APP_BUNDLE/Contents/MacOS/MenuBarFixture"
cp "$FIXTURE_DIR/Info.plist" "$APP_BUNDLE/Contents/Info.plist"
echo "$APP_BUNDLE"
