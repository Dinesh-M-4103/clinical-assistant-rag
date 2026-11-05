/**
 * Dialogs here open from store state rather than a Radix trigger, so Radix has nothing to return
 * focus to when they close. The store remembers the opener and the dialog restores it.
 */
let opener: HTMLElement | null = null;

export function rememberOpener(): void {
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
}

/** Use as `onCloseAutoFocus`: puts focus back on the opener if it is still on the page. */
export function restoreOpener(event: Event): void {
  if (opener?.isConnected) {
    event.preventDefault();
    opener.focus();
  }
  opener = null;
}
