#!/bin/bash
# Install native macOS Look Up into a built Nightly .app (no rebuild needed).
#   ./install.sh                 every obj-*/dist/*.app in the Firefox source
#   ./install.sh /path/To.app    one specific app
#   ./install.sh --uninstall [/path/To.app]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${FIREFOX_SRC:-/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified}"

uninstall=false
if [ "${1:-}" = "--uninstall" ]; then
    uninstall=true
    shift
fi

apps=()
if [ $# -gt 0 ]; then
    apps=("$@")
else
    for app in "$SRC"/obj-*/dist/*.app; do
        [ -d "$app" ] && apps+=("$app")
    done
fi
if [ ${#apps[@]} -eq 0 ]; then
    echo "ERROR: No Nightly .app found under $SRC/obj-*/dist" >&2
    exit 1
fi

for app in "${apps[@]}"; do
    res="$app/Contents/Resources"
    if [ ! -f "$res/application.ini" ]; then
        echo "ERROR: Not a Firefox app bundle: $app" >&2
        exit 1
    fi
    rm -rf "$res/dictionary-lookup"
    rm -f "$res/dictionary-lookup.cfg" "$res/defaults/pref/dictionary-lookup-prefs.js"
    if [ "$uninstall" = true ]; then
        echo "==> Removed native Look Up from $(basename "$app")"
        continue
    fi
    mkdir -p "$res/defaults/pref" "$res/dictionary-lookup"
    cp "$HERE/src/defaults/pref/dictionary-lookup-prefs.js" "$res/defaults/pref/"
    cp "$HERE/src/dictionary-lookup.cfg" "$res/"
    cp "$HERE"/src/modules/*.sys.mjs "$res/dictionary-lookup/"
    echo "==> Installed native Look Up into $(basename "$app")"
done
echo "    Restart Nightly to load it (add -purgecaches if you changed the modules)."
