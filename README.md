# Firefox macOS Dictionary Look Up

Everything used to add **select text → right-click → Look Up “…”** to your local Firefox Nightly artifact build, plus the updater changes that preserve it.

## On your current Mac

The browser is already built and your installed updater is already fixed. Restart Nightly to load the menu action. For future updates, keep using:

```bash
/usr/local/bin/firefoxNightlyUpdate
```

This folder is a self-contained copy of the customization and build support. Your installed updater continues using its persistent patch under `~/.local/share/firefox-nightly/patches/`.

## Contents

| Path | Purpose |
| --- | --- |
| `patches/native-lookup.patch` | Complete Firefox patch, including the browser test |
| `config/mozconfig` | Exact artifact-build configuration used on this Mac |
| `config/build-info.json` | Source revision, local paths, and patch hash |
| `scripts/build-patched-nightly.sh` | Apply the patch and build the current checkout |
| `scripts/firefoxNightlyUpdate` | Update upstream, validate/reapply the patch, build, and repair helper names |
| `scripts/fix-macos-helpers.sh` | The macOS helper-name fix for artifact builds |
| `source/` | Copies of all eight final files changed or added by the patch |
| `tests/test_updater.py` | Disposable-repository integration tests with bundled baseline fixtures |
| `snapshots/` | Exact installed updater and its original backup |
| `logs/` | Build, browser-test, lint, and updater-test results |
| `docs/` | Build instructions and the original implementation notes |

## Rebuild from this folder

For your existing source checkout:

```bash
~/FirefoxOSXDictionaryLookUp/scripts/build-patched-nightly.sh
```

For another checkout:

```bash
~/FirefoxOSXDictionaryLookUp/scripts/build-patched-nightly.sh /path/to/firefox-source
```

The build script recognizes an already-applied patch, preserves an existing `mozconfig`, and uses the bundled artifact configuration when none exists and `MOZCONFIG` is unset. It builds the current revision; it does not fetch or reset source.

To use this folder's updater with another compatible Git checkout:

```bash
FIREFOX_SRC=/path/to/firefox-source ~/FirefoxOSXDictionaryLookUp/scripts/firefoxNightlyUpdate
```

That updater expects the upstream ref `origin/bookmarks/central`, matching your existing workflow. It fetches upstream and checks patch compatibility before resetting. On success it **hard-resets tracked source changes**, restores the dictionary patch, builds, and runs the helper fix. Use it with a checkout dedicated to this build. A conflict stops before the reset; a fetch, build, or helper failure stops the script.

See [Artifact build setup](docs/BUILD.md) for prerequisites, the helper fix, and reconstruction steps.

## Verification

The dictionary patch built successfully. Its dedicated browser test passed in both headless mode and a normal macOS window, with 22 passing assertions and no unexpected results. JavaScript/localization lint passed. The broader context-menu suite timed out in an image-link test after 3,349 passing checks; it is not claimed to pass in full. See the logs and original notes for details.

Run the self-contained updater checks with Python 3 and Git installed:

```bash
python3 ~/FirefoxOSXDictionaryLookUp/tests/test_updater.py
```

These use temporary repositories and a mock build command. They do not update or rebuild your live browser.

The package contains the customization, configuration, scripts, and records. A Firefox source checkout and Mozilla's downloaded build dependencies/artifacts are still required to build; the large source tree, toolchain, and application binary are not bundled.

## Licensing

Firefox source snapshots and modifications retain their existing Mozilla Public License 2.0 notices; the browser test retains its public-domain notice. These files are a local customization, not an upstream Firefox release.
