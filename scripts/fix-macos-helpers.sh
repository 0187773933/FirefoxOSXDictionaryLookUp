#!/bin/bash
set -euo pipefail
SRC="${1:?Usage: fix-macos-helpers.sh /path/to/firefox-source}"

echo "==> Patching branded helper executable names (WebGL/GPU process fix)"
for app in "$SRC"/obj-*/dist/*.app; do
    macos="$app/Contents/MacOS"
    [ -d "$macos" ] || continue
    for pair in "gpu-helper.app:GPU Helper" \
                "media-plugin-helper.app:Media Plugin Helper" \
                "security-module-helper.app:Security Module Helper"; do
        bundle="${pair%%:*}"
        suffix="${pair#*:}"
        src="$macos/$bundle/Contents/MacOS/Nightly $suffix"
        dst="$macos/$bundle/Contents/MacOS/Firefox Nightly $suffix"
        [ -e "$src" ] || continue
        [ -e "$dst" ] && continue
        if ln "$src" "$dst" 2>/dev/null || cp -p "$src" "$dst"; then
            echo "    + $(basename "$app")/$bundle -> Firefox Nightly $suffix"
        else
            echo "    ! FAILED to create: $dst" >&2
            exit 1
        fi
    done
done
