# Native macOS Look Up for Firefox Nightly

Built September 15, 2026 into the user's local Nightly:

`/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified/obj-x86_64-apple-darwin24.6.0/dist/Nightly.app`

## Use

Restart Nightly, select a word or phrase, right-click the selection, and choose **Look Up “…”** at the top of the context menu. This invokes Firefox's existing native macOS dictionary popup. Password selections are excluded. The original browsing session was left running.

## Implementation

The macOS menu item sends the original click position to the relevant content frame. The content actor converts the position into local widget coordinates and invokes `cmd_lookUpDictionary` with explicit coordinates. The native implementation supplies the selected text, font information, and popup position to macOS.

The menu label shortens long selections to 30 characters; the native command still uses the selection. No add-on or preference changes are required.

Source repository: `/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified`

Base revision: `1cf7c37cb9982` (September 12, 2026).

## Verification

- `./mach build faster`: passed on the final implementation.
- Dedicated browser test: passed in both headless mode and a normal macOS window; 22 passing assertions and no unexpected results. Covers real menu activation, command execution, page zoom, text input, an iframe, empty selection, and password exclusion.
- JavaScript and Fluent localization lint: passed with zero errors or warnings.
- Broad context-menu test: 3,349 passing checks before an image-link test timed out with `TypeError: doc is null`, before menu initialization. The full broad suite is therefore not verified. This was not reproduced on an unmodified baseline.
- The full lint invocation reported that the environment's Rust 1.69 is too old for cargo-audit (requires 1.85). Targeted JavaScript/localization lint passed; no Rust files were changed.
- Saved patch validated with `git apply --reverse --check` against the edited source.

## Preserve or remove the change

`/usr/local/bin/firefoxNightlyUpdate` now automatically preserves this customization. It fetches upstream, validates the patch against that exact revision using a temporary Git index, then resets the source, restores all patch files, and builds. A patch conflict stops the updater before the source reset. Fetch, patch, build, and helper failures stop execution instead of reporting success. The existing GPU/WebGL helper fix remains in place.

The updater uses a persistent copy at `/Users/morpheous/.local/share/firefox-nightly/patches/native-lookup.patch`. It does not depend on keeping this ScratchPad folder. If the customization changes, update that persistent patch too.

The original updater is backed up at `/Users/morpheous/.local/share/firefox-nightly/firefoxNightlyUpdate.before-lookup`. Integration checks using the real patch in a disposable Git repository passed for first/repeated updates, missing patches, upstream patch conflicts, failed builds, and failed fetches. See `updater-tests.log` and `test_updater.py`. The actual live update/reset/build was not run during the updater change; the current browser was already built.

`native-lookup.patch` contains the source change and test. Keep it when resetting or replacing this checkout. Ordinary builds of the edited source retain the change; replacing the app with an official build will not.

To reapply to an unmodified compatible checkout, run `git apply --check` on the patch, then `git apply` and `./mach build faster` from the source repository. A newer checkout may require resolving changes to the affected files.

To remove it permanently, restore the original updater first so future updates no longer reapply it. To remove it from the current checkout, use `git apply --reverse --check` first, then `git apply --reverse` and `./mach build faster`. Restart Nightly after rebuilding.
