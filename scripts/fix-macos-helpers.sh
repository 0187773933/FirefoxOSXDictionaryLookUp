#!/bin/bash
# WebGL fix -- run after every build.
#
# The downloaded artifact XUL is built by Mozilla with official *nightly*
# branding (MOZ_APP_DISPLAYNAME="Firefox Nightly"), so it spawns its child
# processes from paths like:
#     gpu-helper.app/Contents/MacOS/Firefox Nightly GPU Helper
# But this tree builds with *unofficial* branding (MOZ_APP_DISPLAYNAME=Nightly),
# which stages them as:
#     gpu-helper.app/Contents/MacOS/Nightly GPU Helper
#
# The mismatch makes posix_spawnp fail with ENOENT (0x2). The GPU process never
# launches, WebRender falls back to software, and WebGL is disabled -- which no
# amount of about:config toggling can override. Hardlinking the officially-named
# executables fixes it. Idempotent; safe to re-run.
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
