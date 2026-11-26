/* Runs in the page's process and asks macOS to show the Dictionary popover
 * for the word at the point where the context menu was opened. */

export class DictionaryLookupChild extends JSWindowActorChild {
  receiveMessage(message) {
    if (message.name != "DictionaryLookup:LookUp") {
      return false;
    }
    const utils = this.contentWindow.windowUtils;
    const { clientX, clientY } = message.data;
    const topLevel = utils.toTopLevelWidgetRect(clientX, clientY, 1, 1);
    const point =
      Services.appinfo.processType == Ci.nsIXULRuntime.PROCESS_TYPE_CONTENT
        ? utils.convertFromParentProcessWidgetToLocal(
            topLevel.x,
            topLevel.y,
            1,
            1
          )
        : topLevel;
    const params = Cu.createCommandParams();
    params.setLongValue("x", Math.round(point.x));
    params.setLongValue("y", Math.round(point.y));
    this.docShell.doCommandWithParams("cmd_lookUpDictionary", params);
    return true;
  }
}
