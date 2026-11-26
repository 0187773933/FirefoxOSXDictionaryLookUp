/* Adds "Look Up “…”" to the top of the page context menu on macOS and opens
 * the native Dictionary popover for the selected word, like Safari does.
 *
 * Everything here hooks Firefox from outside its source, so nothing has to be
 * patched or rebuilt. Each Firefox internal it touches is wrapped so that a
 * change upstream only hides the menu item instead of breaking the menu.
 */

const ITEM_ID = "context-look-up-dictionary";
const SEPARATOR_ID = "context-sep-look-up-dictionary";
const ACTOR = "DictionaryLookup";
const MAX_LABEL_CHARS = 30;

// Where the menu was opened, captured when it shows: gContextMenu's data is
// cleared as the menu hides, which can happen before the command runs.
const lastContext = new WeakMap();

function label(text) {
  text = text.replace(/\s+/g, " ").trim();
  if (text.length > MAX_LABEL_CHARS) {
    text = text.slice(0, MAX_LABEL_CHARS) + "…";
  }
  return `Look Up “${text}”`;
}

export const DictionaryLookup = {
  _initialized: false,

  init() {
    if (this._initialized || Services.appinfo.OS != "Darwin") {
      return;
    }
    this._initialized = true;

    ChromeUtils.registerWindowActor(ACTOR, {
      parent: {
        esModuleURI:
          "resource://dictionary-lookup/DictionaryLookupParent.sys.mjs",
      },
      child: {
        esModuleURI:
          "resource://dictionary-lookup/DictionaryLookupChild.sys.mjs",
      },
      allFrames: true,
      messageManagerGroups: ["browsers"],
    });

    Services.obs.addObserver(this, "browser-delayed-startup-finished");
    // Windows that finished starting before this ran (e.g. a reload in dev).
    for (const win of Services.wm.getEnumerator("navigator:browser")) {
      if (win.gBrowserInit?.delayedStartupFinished) {
        this.attach(win);
      }
    }
  },

  observe(win, topic) {
    if (topic == "browser-delayed-startup-finished") {
      this.attach(win);
    }
  },

  attach(win) {
    try {
      const doc = win.document;
      const popup = doc.getElementById("contentAreaContextMenu");
      if (!popup || doc.getElementById(ITEM_ID)) {
        return;
      }
      const item = doc.createXULElement("menuitem");
      item.id = ITEM_ID;
      item.hidden = true;
      const separator = doc.createXULElement("menuseparator");
      separator.id = SEPARATOR_ID;
      separator.hidden = true;
      popup.prepend(item, separator);

      // Registered after Firefox's own listener, so gContextMenu is ready.
      popup.addEventListener("popupshowing", event => {
        if (event.target == popup) {
          this.update(win, popup, item, separator);
        }
      });
      item.addEventListener("command", () => this.lookUp(win));
    } catch (e) {
      console.error("DictionaryLookup: could not add the menu item", e);
    }
  },

  update(win, popup, item, separator) {
    let show = false;
    try {
      const menu = win.gContextMenu;
      show = !!menu && menu.isTextSelected && !menu.onPassword;
      if (show) {
        const { clientX, clientY } = menu.contentData.context;
        lastContext.set(win, {
          windowGlobal: menu.actor.manager,
          clientX,
          clientY,
        });
        item.setAttribute("label", label(menu.selectedText));
      }
    } catch (e) {
      show = false;
      console.error("DictionaryLookup: context menu internals changed", e);
    }
    item.hidden = !show;
    separator.hidden = !show;
    if (!show) {
      lastContext.delete(win);
    }
    try {
      // Re-run Firefox's tidy-up so our separator never doubles another one.
      if (popup.showHideSeparators) {
        popup.showHideSeparators();
      } else {
        win.gContextMenu?.showHideSeparators?.(popup);
      }
    } catch (e) {
      console.error(e);
    }
  },

  async lookUp(win) {
    const context = lastContext.get(win);
    if (!context) {
      return;
    }
    try {
      await context.windowGlobal
        .getActor(ACTOR)
        .sendQuery("DictionaryLookup:LookUp", {
          clientX: context.clientX,
          clientY: context.clientY,
        });
    } catch (e) {
      console.error("DictionaryLookup: lookup failed", e);
    }
  },
};
