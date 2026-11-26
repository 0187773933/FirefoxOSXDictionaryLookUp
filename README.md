# Firefox macOS Dictionary Look Up

Adds **select text → right-click → Look Up “…”** to the local Firefox Nightly
artifact build on macOS. The item sits at the top of the page context menu. It
appears when text is selected, except in password fields, and opens the native
macOS Dictionary popover: the same one as a three-finger tap or Safari's
Look Up.

## How it works (and why it is no longer a patch)

Until November 2026 this was a Firefox source patch, now in
`legacy/patches/native-lookup.patch`, re-applied before every build. Nightly
changes every day, so the lines around the patch kept moving. Updates then
stopped with "The Look Up patch conflicts with this Nightly revision."

Now **no Firefox source is changed**. After each build, `install.sh` copies a
small startup script into `Nightly.app`. Firefox's autoconfig runs it as
privileged JavaScript at launch, and it adds the menu item to every window. It
uses only things Firefox already has:

- `cmd_lookUpDictionary`, the native command behind force-touch lookup
- the context menu's own state: `gContextMenu.isTextSelected`,
  `selectedText`, `onPassword` and `contentData.context.clientX/Y`
- a small window actor that runs the command in the page's process, at the
  click point converted to widget coordinates

The update and build can no longer fail because of Look Up. If Firefox renames
one of those internals, the menu item hides itself and `check-compat.sh` names
what changed.

## Daily use

```bash
firefoxNightlyUpdate
```

`/usr/local/bin/firefoxNightlyUpdate` is a symlink to
`scripts/firefoxNightlyUpdate`. It:

1. fetches mozilla-central and runs `check-compat.sh`, which only warns
2. hard-resets the source checkout to `origin/bookmarks/central`
3. runs `./mach build`
4. runs `scripts/fix-macos-helpers.sh` (the WebGL/GPU helper-name fix)
5. runs `install.sh` to put Look Up into `obj-*/dist/*.app`

Then restart Nightly.

```bash
firefoxNightlyUpdate --check-only
```

This only fetches and runs the compatibility check.

To use another checkout, set `FIREFOX_SRC=/path/to/firefox-source` for
`firefoxNightlyUpdate`, `install.sh` or `check-compat.sh`.

## Contents

| Path | Purpose |
| --- | --- |
| `src/defaults/pref/dictionary-lookup-prefs.js` | Turns on autoconfig and points it at the `.cfg` |
| `src/dictionary-lookup.cfg` | Startup script: maps `resource://dictionary-lookup/` and loads the module |
| `src/modules/DictionaryLookup.sys.mjs` | Adds the menu item and separator, shows or hides them, sends the lookup |
| `src/modules/DictionaryLookupChild.sys.mjs` | Runs `cmd_lookUpDictionary` at the click point in the page |
| `src/modules/DictionaryLookupParent.sys.mjs` | The parent half of the actor pair |
| `install.sh` | Copies `src/` into the app's `Contents/Resources`; `--uninstall` removes it |
| `check-compat.sh` | Checks that a Firefox revision still has every internal the module uses |
| `tests/smoke_test.py` | Launches the built Nightly with a throwaway profile and checks the menu item |
| `scripts/firefoxNightlyUpdate` | The updater (see above) |
| `scripts/fix-macos-helpers.sh` | The macOS helper-name fix for artifact builds |
| `config/mozconfig` | The artifact-build configuration used on this Mac |
| `docs/` | Build setup and the original implementation notes |
| `legacy/` | Everything from the patch-based version: patch, patched source copies, tests, logs and snapshots of earlier updaters |

## Changing the module

Edit `src/`, then reinstall and restart Nightly without cached copies:

```bash
./install.sh && open -a "$HOME/APPLICATIONS_2/Firefox/mozilla-unified/obj-x86_64-apple-darwin24.6.0/dist/Nightly.app" --args -purgecaches
```

No rebuild is needed.

## Testing

With Nightly closed:

```bash
python3 tests/smoke_test.py
```

The test starts the built Nightly with a throwaway profile, so your own
profile is never touched, and the test browser quits when it's done. It checks
that a selected word shows **Look Up “serendipity”** as the first item with
its separator, that the page's process actually receives and runs the lookup,
and that clicking it raises no errors. It also checks that the
item stays hidden on blank space and in a password field. The Dictionary
popover is drawn by macOS, so the test can't see it; confirm that by eye.

On macOS, right-clicking a word selects it, so Look Up appears for any word you
right-click, even with nothing selected beforehand. Safari does the same.

## If it stops working

1. Run `./check-compat.sh` to see which Firefox internal changed, and
   `python3 tests/smoke_test.py` to see which behaviour broke.
2. Look in the Browser Console (Cmd+Shift+J) for `DictionaryLookup:` errors.
3. Fix the matching line in `src/modules/DictionaryLookup.sys.mjs`, then run
   `./install.sh`.

## Licensing

The child actor's coordinate conversion and command call come from the
earlier Firefox patch and keep the Mozilla Public License 2.0. Files under
`legacy/source` keep their Mozilla notices, and the legacy browser test keeps
its public-domain notice. This is a local customization, not an upstream
Firefox release.
