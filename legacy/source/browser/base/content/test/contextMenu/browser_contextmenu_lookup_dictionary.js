/* Any copyright is dedicated to the Public Domain.
 * https://creativecommons.org/publicdomain/zero/1.0/ */

"use strict";

add_task(async function test_native_dictionary_context_menu() {
  const page = `data:text/html,${encodeURIComponent(`<!DOCTYPE html>
    <style>body { padding: 40px; } span, input { font-size: 24px; }</style>
    <span id="word">dictionary</span>
    <input id="input" value="dictionary">
    <input id="password" type="password" value="dictionary">
    <iframe srcdoc='<span id="word" style="font-size:24px">dictionary</span>'></iframe>
  `)}`;

  await BrowserTestUtils.withNewTab(page, async browser => {
    const menu = document.getElementById("contentAreaContextMenu");
    const item = document.getElementById("context-look-up-dictionary");

    for (const scenario of [
      { selector: "#word", zoom: 1 },
      { selector: "#word", zoom: 1.5 },
      { selector: "#input", zoom: 1 },
      { selector: "#word", zoom: 1, frame: true },
      { selector: "#word", zoom: 1, collapsed: true },
      { selector: "#password", zoom: 1 },
    ]) {
      info(JSON.stringify(scenario));
      browser.fullZoom = scenario.zoom;
      const context = scenario.frame
        ? browser.browsingContext.children[0]
        : browser.browsingContext;
      await SpecialPowers.spawn(context, [scenario], options => {
        const element = content.document.querySelector(options.selector);
        if (content.HTMLInputElement.isInstance(element)) {
          element.focus();
          element.select();
        } else {
          content.document.activeElement.blur();
          const selection = content.getSelection();
          selection.removeAllRanges();
          if (!options.collapsed) {
            const range = content.document.createRange();
            range.selectNodeContents(element);
            selection.addRange(range);
          }
        }
      });

      const shown = BrowserTestUtils.waitForPopupEvent(menu, "shown");
      await BrowserTestUtils.synthesizeMouse(
        scenario.selector,
        12,
        12,
        { type: "contextmenu", button: 2 },
        context
      );
      await shown;

      const visible = !scenario.collapsed && scenario.selector != "#password";
      is(
        !item.hidden,
        visible,
        "Lookup is available for non-password selections"
      );
      const hidden = BrowserTestUtils.waitForPopupEvent(menu, "hidden");
      if (visible) {
        await document.l10n.translateElements([item]);
        is(
          item.label,
          "Look Up “dictionary”",
          "The menu names the selected text"
        );
        const firstItem = Array.from(menu.children).find(
          child => !child.hidden
        );
        is(firstItem, item, "Lookup is the first visible menu item");
        const original = gContextMenu.lookUpDictionary.bind(gContextMenu);
        const invocation = new Promise((resolve, reject) => {
          gContextMenu.lookUpDictionary = () => {
            ok(true, "Clicking the menu invokes native lookup");
            const result = original();
            result.then(resolve, reject);
            return result;
          };
        });
        menu.activateItem(item);
        await invocation;
        ok(true, "The content process executed the native dictionary command");
      } else {
        menu.hidePopup();
      }
      await hidden;
    }
  });
});
