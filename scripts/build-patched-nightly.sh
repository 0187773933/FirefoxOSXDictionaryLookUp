#!/bin/bash
set -euo pipefail

if [ "${1:-}" = "--help" ]; then
    echo "Usage: build-patched-nightly.sh [/path/to/firefox-source]"
    echo "Applies Look Up, builds the current checkout, and repairs macOS helper names."
    exit 0
fi

PACKAGE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SRC="${1:-${FIREFOX_SRC:-/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified}}"
LOOKUP_PATCH="$PACKAGE_DIR/patches/native-lookup.patch"
cd "$SRC"

if git apply --reverse --check "$LOOKUP_PATCH" 2>/dev/null; then
    echo "==> Native Look Up is already applied"
elif git apply --check "$LOOKUP_PATCH"; then
    git apply "$LOOKUP_PATCH"
else
    echo "ERROR: The Look Up patch does not apply cleanly to this checkout." >&2
    exit 1
fi

if [ ! -f mozconfig ] && [ -z "${MOZCONFIG:-}" ]; then
    cp "$PACKAGE_DIR/config/mozconfig" mozconfig
fi

./mach build
"$PACKAGE_DIR/scripts/fix-macos-helpers.sh" "$SRC"
echo "==> Build complete. Restart the Nightly app from this checkout."
