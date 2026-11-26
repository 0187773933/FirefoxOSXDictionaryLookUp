# Artifact build setup and reconstruction

## What was needed

This feature uses native lookup code that was already present in Firefox's compiled macOS engine. The module in `src/` connects the context menu to `cmd_lookUpDictionary`, supplying the click coordinates in the correct frame. Since November 2026 it does not change any Firefox source. `install.sh` copies it into the built app, and Firefox's autoconfig loads it at startup. The build itself is a plain, unmodified mozilla-central artifact build.

The earlier patch-based version was built at revision `1cf7c37cb9982` (September 12, 2026). Its records are in `legacy/`.

## Configuration

The existing `mozconfig`, copied verbatim into this package, contains:

```text
ac_add_options --enable-artifact-builds
mk_add_options AUTOCLOBBER=1
```

Artifact mode downloads precompiled native components and combines them with the local frontend. `AUTOCLOBBER=1` permits a required build-output cleanup without an interactive stop. Neither option was invented specifically for Look Up; both were already part of the working build setup.

## Using a fresh compatible checkout

Obtain a Mozilla Firefox Git checkout. Any recent revision works; `check-compat.sh` reports whether it still has the internals Look Up uses. The automatic updater specifically expects `origin/bookmarks/central`, so a checkout from a different mirror needs its updater target adjusted.

From the source directory, run Mozilla's bootstrap for artifact builds:

```bash
./mach bootstrap --application-choice browser_artifact_mode
```

Follow bootstrap's prerequisites for macOS, including the appropriate developer tools. On the already-configured Mac, the narrower command used during this work was:

```bash
./mach --no-interactive bootstrap --application-choice browser_artifact_mode --no-system-changes
```

That refreshed build/test tools. It is recorded for completeness; it was not an additional runtime requirement for dictionary lookup.

For a fresh dedicated checkout, copy `config/mozconfig` to `mozconfig`. Preserve and review any existing build configuration instead of overwriting it. If `MOZCONFIG` selects a different file, ensure that file enables artifact builds.

Then build and install from the source directory:

```bash
./mach build
~/WORKSPACE/PROJECTS/FirefoxOSXDictionaryLookUp/scripts/fix-macos-helpers.sh "$PWD"
FIREFOX_SRC="$PWD" ~/WORKSPACE/PROJECTS/FirefoxOSXDictionaryLookUp/install.sh
```

`scripts/firefoxNightlyUpdate` does the same after fetching and resetting to the latest Nightly. Open the built application under `obj-*/dist/Nightly.app` and restart it after rebuilding. On another machine the `obj-*` directory name may differ.

The full Firefox source and downloaded artifacts are external dependencies. This package is not an offline Firefox build distribution.

## Fast frontend rebuilds

Changing Look Up itself needs no rebuild: edit `src/`, run `install.sh`, and restart Nightly with `-purgecaches`. After the checkout has a successful build and only Firefox frontend files have changed, use:

```bash
./mach build faster
~/WORKSPACE/PROJECTS/FirefoxOSXDictionaryLookUp/scripts/fix-macos-helpers.sh "$PWD"
FIREFOX_SRC="$PWD" ~/WORKSPACE/PROJECTS/FirefoxOSXDictionaryLookUp/install.sh
```

Use the normal `./mach build` after pulling a new revision or changing the native/build configuration so the artifacts and generated output match the checkout. The packaged updater does this automatically.

## macOS artifact helper fix

The existing local artifact build uses unofficial `Nightly` branding, while the downloaded native engine expects helper executable names beginning with `Firefox Nightly`. The existing updater already repaired this mismatch. The fix is preserved here and is applied after builds for these bundles:

- `gpu-helper.app`: `Nightly GPU Helper` → `Firefox Nightly GPU Helper`
- `media-plugin-helper.app`: `Nightly Media Plugin Helper` → `Firefox Nightly Media Plugin Helper`
- `security-module-helper.app`: `Nightly Security Module Helper` → `Firefox Nightly Security Module Helper`

The script creates a hard link, falling back to a copy, when the expected executable name is absent. It discovers `obj-*/dist/*.app` rather than hard-coding a macOS kernel version. This is the existing WebGL/GPU fix, not a new dictionary dependency.

After launch, check `about:support` → Graphics for a GPU process and hardware WebRender as appropriate for your hardware. Look Up should be at the top of the context menu for selected non-password text.

## Tests and limitations

`tests/smoke_test.py` checks the autoconfig module against the built app over Marionette: a selected word, a click on the item, blank space, and a password field. It passed against revision `050fc3708219` on November 26, 2026. There is no in-tree browser test, because the module lives outside the Firefox source. The patch-based version had one, covering selected text, 150% page zoom, a text field, an iframe, no selection and password exclusion. It is kept at `legacy/source/browser/base/content/test/contextMenu/browser_contextmenu_lookup_dictionary.js`, with its results in `legacy/logs/`. The child actor's lookup code is unchanged from that tested version. The menu wiring is new.

Upstream can still rename an internal the module reads. `check-compat.sh`, which the updater runs before every build, names the one that changed. The menu item then stays hidden instead of failing, and the update and build carry on regardless.
