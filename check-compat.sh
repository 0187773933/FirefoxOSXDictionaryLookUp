#!/bin/bash
# Early warning: checks that a Firefox revision still has every internal the
# module relies on. It reads the git objects only and never touches the checkout.
#   ./check-compat.sh [revision]   (default: origin/bookmarks/central)
set -uo pipefail

SRC="${FIREFOX_SRC:-/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified}"
rev="${1:-origin/bookmarks/central}"
cd "$SRC" || exit 1

# file | text that must appear in it
checks=(
  "dom/base/nsGlobalWindowCommands.cpp|\"cmd_lookUpDictionary\""
  "dom/interfaces/base/nsIDOMWindowUtils.idl|toTopLevelWidgetRect"
  "dom/interfaces/base/nsIDOMWindowUtils.idl|convertFromParentProcessWidgetToLocal"
  "browser/base/content/browser-context.js|gContextMenu = new nsContextMenu"
  "browser/base/content/main-popupset.inc.xhtml|id=\"contentAreaContextMenu\""
  "browser/base/content/nsContextMenu.sys.mjs|this.isTextSelected ="
  "browser/base/content/nsContextMenu.sys.mjs|this.onPassword ="
  "browser/base/content/nsContextMenu.sys.mjs|this.selectedText ="
  "browser/base/content/nsContextMenu.sys.mjs|this.contentData ="
  "browser/base/content/nsContextMenu.sys.mjs|this.actor ="
  "browser/base/content/nsContextMenu.sys.mjs|showHideSeparators"
  "browser/actors/ContextMenuChild.sys.mjs|context.clientX"
  "browser/base/content/browser-init.js|browser-delayed-startup-finished"
  "extensions/pref/autoconfig/src/nsReadConfig.cpp|general.config.sandbox_enabled"
  "dom/chrome-webidl/JSActor.webidl|safeForUntrustedWebProcess"
)

failed=0
for check in "${checks[@]}"; do
    file="${check%%|*}"
    text="${check#*|}"
    content="$(git show "$rev:$file" 2>/dev/null)"
    if ! grep -qF -- "$text" <<<"$content"; then
        echo "WARNING: $file no longer contains: $text" >&2
        failed=1
    fi
done
if [ $failed -eq 0 ]; then
    echo "==> Native Look Up: every Firefox internal it uses is still present"
else
    echo "WARNING: Native Look Up may stop working on this revision (Nightly itself is unaffected)." >&2
fi
exit $failed
