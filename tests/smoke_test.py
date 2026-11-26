#!/usr/bin/env python3
"""Smoke test for native Look Up in the built Nightly.

Starts Nightly with a throwaway profile and Marionette, right-clicks a test
page in several ways, and checks the Look Up menu item. Your own profile is
never touched, and the test browser quits at the end.

    python3 tests/smoke_test.py [/path/to/Nightly.app]

Needs Nightly to be closed, or at least not using Marionette port 2828.
Look Up must already be installed (./install.sh). The macOS Dictionary popover
is drawn by the system, so this checks only that the click raised no errors.
"""
import glob
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time

SRC = os.environ.get("FIREFOX_SRC", "/Users/morpheous/APPLICATIONS_2/Firefox/mozilla-unified")
PORT = 2828
PAGE = """<!DOCTYPE html><meta charset=utf-8>
<p style="font-size:40px;padding:40px"><span id=w>serendipity</span> and more</p>
<input id=p type=password value=secret style="font-size:30px">"""

MENU_STATE = """
return (async () => {
  const popup = document.getElementById("contentAreaContextMenu");
  for (let i = 0; i < 50 && popup.state != "open"; i++) {
    await new Promise(r => setTimeout(r, 100));
  }
  const item = document.getElementById("context-look-up-dictionary");
  const sep = document.getElementById("context-sep-look-up-dictionary");
  return {
    open: popup.state == "open",
    exists: !!item,
    shown: !!item && !item.hidden,
    separatorShown: !!sep && !sep.hidden,
    label: item?.getAttribute("label"),
    firstVisible: [...popup.children].find(c => !c.hidden)?.id,
  };
})();
"""
CLICK_ITEM = """
return (async () => {
  const errors = [];
  const listener = {observe(m) {
    const text = String(m.message || m);
    if (text.includes("DictionaryLookup")) errors.push(text);
  }};
  Services.console.registerListener(listener);
  document.getElementById("context-look-up-dictionary").doCommand();
  await new Promise(r => setTimeout(r, 1500));
  Services.console.unregisterListener(listener);
  return errors;
})();
"""
# Sends the same query the menu item sends and returns what came back, so a
# failure that the module catches and logs still fails the test.
REACHES_PAGE = """
return (async () => {
  const context = gContextMenu.contentData.context;
  try {
    return await gContextMenu.actor.manager
      .getActor("DictionaryLookup")
      .sendQuery("DictionaryLookup:LookUp",
                 {clientX: context.clientX, clientY: context.clientY});
  } catch (e) {
    return String(e);
  }
})();
"""
HIDE_MENU ='document.getElementById("contentAreaContextMenu").hidePopup();'


class Marionette:
    def __init__(self, port):
        for _ in range(90):
            try:
                self.sock = socket.create_connection(("127.0.0.1", port))
                break
            except OSError:
                time.sleep(1)
        else:
            sys.exit("ERROR: Nightly did not open Marionette on port %d" % port)
        self.file = self.sock.makefile("rb")
        self.id = 0
        self._read()

    def _read(self):
        length = b""
        while (c := self.file.read(1)) != b":":
            if not c:
                raise ConnectionError("Marionette closed the connection")
            length += c
        return json.loads(self.file.read(int(length)))

    def __call__(self, name, params=None):
        self.id += 1
        body = json.dumps([0, self.id, name, params or {}]).encode()
        self.sock.sendall(str(len(body)).encode() + b":" + body)
        reply = self._read()
        if reply[2]:
            raise RuntimeError(f"{name}: {reply[2].get('message', reply[2])}")
        return reply[3]

    def script(self, source):
        return self("WebDriver:ExecuteScript", {"script": source, "args": []})["value"]

    def chrome(self, source):
        self("Marionette:SetContext", {"value": "chrome"})
        try:
            return self.script(source)
        finally:
            self("Marionette:SetContext", {"value": "content"})


def right_click(m, x, y):
    m("WebDriver:PerformActions", {"actions": [{
        "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
        "actions": [{"type": "pointerMove", "origin": "viewport", "x": x, "y": y},
                    {"type": "pointerDown", "button": 2},
                    {"type": "pointerUp", "button": 2}]}]})
    m("WebDriver:ReleaseActions")


def center(m, selector):
    element = m("WebDriver:FindElement", {"using": "css selector", "value": selector})["value"]
    rect = m("WebDriver:GetElementRect", {"id": next(iter(element.values()))})
    return int(rect["x"] + rect["width"] / 2), int(rect["y"] + rect["height"] / 2)


def main():
    if len(sys.argv) > 1:
        app = sys.argv[1]
    else:
        apps = glob.glob(f"{SRC}/obj-*/dist/*.app")
        if not apps:
            sys.exit(f"ERROR: No Nightly .app under {SRC}/obj-*/dist")
        app = apps[0]
    if not os.path.exists(f"{app}/Contents/Resources/dictionary-lookup.cfg"):
        sys.exit(f"ERROR: Look Up is not installed in {app}; run ./install.sh")

    failures = []

    def expect(case, condition, detail):
        print(("  ok    " if condition else "  FAIL  ") + f"{case}: {detail}")
        if not condition:
            failures.append(case)

    with tempfile.TemporaryDirectory(prefix="lookup-smoke-") as tmp:
        profile = pathlib.Path(tmp, "profile")
        profile.mkdir()
        page = pathlib.Path(tmp, "page.html")
        page.write_text(PAGE)
        env = dict(os.environ, MOZ_REMOTE_ALLOW_SYSTEM_ACCESS="1")
        browser = subprocess.Popen(
            [f"{app}/Contents/MacOS/firefox", "-marionette", "-no-remote",
             "-purgecaches", "-profile", str(profile)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"==> Testing Look Up in {app}")
        try:
            m = Marionette(PORT)
            m("WebDriver:NewSession", {"capabilities": {}})
            m("WebDriver:Navigate", {"url": page.as_uri()})
            word = center(m, "#w")

            # 1. Selected word: shown first, labelled, and clickable.
            m.script("const r = document.createRange();"
                     "r.selectNodeContents(document.getElementById('w'));"
                     "getSelection().removeAllRanges(); getSelection().addRange(r);")
            right_click(m, *word)
            state = m.chrome(MENU_STATE)
            expect("selected word", state["shown"] and state["separatorShown"],
                   f"item shown={state['shown']}, separator shown={state['separatorShown']}")
            expect("label", state["label"] == "Look Up “serendipity”", repr(state["label"]))
            expect("position", state["firstVisible"] == "context-look-up-dictionary",
                   f"first visible item is {state['firstVisible']}")
            reached = m.chrome(REACHES_PAGE)
            expect("lookup reaches page", reached is True,
                   "page ran the lookup" if reached is True else repr(reached))
            errors = m.chrome(CLICK_ITEM)
            expect("click", not errors, "no errors" if not errors else "; ".join(errors))
            m.chrome(HIDE_MENU)
            time.sleep(0.5)

            # 2. Blank space with nothing selected: hidden.
            m.script("getSelection().removeAllRanges(); document.activeElement.blur();")
            right_click(m, 600, 400)
            state = m.chrome(MENU_STATE)
            expect("blank space", state["open"] and not state["shown"] and not state["separatorShown"],
                   f"menu open={state['open']}, item shown={state['shown']}")
            m.chrome(HIDE_MENU)
            time.sleep(0.5)

            # 3. Password field: hidden.
            m.script("const p = document.getElementById('p'); p.focus(); p.select();")
            right_click(m, *center(m, "#p"))
            state = m.chrome(MENU_STATE)
            expect("password field", state["open"] and not state["shown"],
                   f"menu open={state['open']}, item shown={state['shown']}")
            m.chrome(HIDE_MENU)
            m("Marionette:Quit", {"flags": ["eForceQuit"]})
        finally:
            try:
                browser.wait(timeout=15)
            except subprocess.TimeoutExpired:
                browser.kill()

    if failures:
        print(f"==> FAILED: {', '.join(failures)}")
        return 1
    print("==> All Look Up checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
