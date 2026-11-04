export type ThemePreference = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'clinical-assistant:theme';

export const THEME_ORDER: readonly ThemePreference[] = ['system', 'light', 'dark'];

export function readStoredTheme(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : 'system';
  } catch {
    return 'system';
  }
}

export function storeTheme(theme: ThemePreference): void {
  try {
    if (theme === 'system') localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Storage can be blocked (private mode); the preference then lasts for this session only.
  }
}

export function prefersDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/** Applies the theme to <html>; the inline script in index.html does the same before first paint. */
export function applyTheme(theme: ThemePreference): void {
  const dark = theme === 'dark' || (theme === 'system' && prefersDark());
  document.documentElement.classList.toggle('dark', dark);
}
