# Artifact build setup and reconstruction

## What was needed

This feature uses native lookup code that was already present in Firefox's compiled macOS engine. The patch connects the context menu to `cmd_lookUpDictionary`, supplying the click coordinates in the correct frame. It changes JavaScript, XUL markup, Fluent strings, and tests. No C++, Rust, add-on, privileged-extension preferences, private signing certificate, or custom engine compilation was needed for the dictionary change.

The source was built at revision `1cf7c37cb9982` from September 12, 2026. The full revision and local application path are recorded in `config/build-info.json`.

## Configuration

The existing `mozconfig`, copied verbatim into this package, contains:

```text
ac_add_options --enable-artifact-builds
mk_add_options AUTOCLOBBER=1
```

Artifact mode downloads precompiled native components and combines them with the local frontend. `AUTOCLOBBER=1` permits a required build-output cleanup without an interactive stop. Neither option was invented specifically for Look Up; both were already part of the working build setup.

## Using a fresh compatible checkout

Obtain a Mozilla Firefox Git checkout containing the required revision. Use the recorded base revision to reproduce this patch; later revisions must pass the patch compatibility check. The automatic updater specifically expects `origin/bookmarks/central`, so a checkout from a different mirror needs its updater target adjusted.

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

Then run the package's build script:

```bash
~/FirefoxOSXDictionaryLookUp/scripts/build-patched-nightly.sh /path/to/firefox-source
```

The script applies the patch if needed, invokes `./mach build`, then repairs the macOS helper executable names. Open the built application under `obj-*/dist/Nightly.app` and restart it after rebuilding. On another machine the `obj-*` directory name may differ.

The full Firefox source and downloaded artifacts are external dependencies. This package is not an offline Firefox build distribution.

## Fast frontend rebuilds

After the checkout has a successful build and only frontend files have changed, the command used for this implementation was:

```bash
./mach build faster
~/FirefoxOSXDictionaryLookUp/scripts/fix-macos-helpers.sh "$PWD"
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

The patch includes a browser test covering selected text, 150% page zoom, a text field, an iframe, no selection, and password exclusion. From the patched source directory:

```bash
./mach mochitest --headless browser/base/content/test/contextMenu/browser_contextmenu_lookup_dictionary.js
./mach mochitest browser/base/content/test/contextMenu/browser_contextmenu_lookup_dictionary.js
```

Both modes passed during implementation. The full context-menu test encountered an image-link timeout; the complete suite is not verified. A full lint invocation also found that the installed Rust was too old for cargo-audit; the relevant JavaScript and Fluent checks passed, and no Rust files changed. Detailed records are in `logs/`.

The main source patch remains local and can conflict with future upstream changes. Both packaged and installed updaters stop on such a conflict before resetting the current source. Update the persistent patch used by the installed updater when revising the customization.
