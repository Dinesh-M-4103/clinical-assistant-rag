import { useCallback, useEffect, useSyncExternalStore } from 'react';
import { create } from 'zustand';
import {
  THEME_ORDER,
  applyTheme,
  readStoredTheme,
  storeTheme,
  type ThemePreference,
} from '@/lib/theme';

interface ThemeState {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
}

const useThemeStore = create<ThemeState>((set) => ({
  preference: readStoredTheme(),
  setPreference: (preference) => {
    storeTheme(preference);
    set({ preference });
  },
}));

function subscribeToSystemTheme(onChange: () => void): () => void {
  const query = window.matchMedia('(prefers-color-scheme: dark)');
  query.addEventListener('change', onChange);
  return () => query.removeEventListener('change', onChange);
}

const systemIsDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches;

export function useTheme() {
  const preference = useThemeStore((state) => state.preference);
  const setPreference = useThemeStore((state) => state.setPreference);
  const systemDark = useSyncExternalStore(subscribeToSystemTheme, systemIsDark);

  useEffect(() => {
    applyTheme(preference);
  }, [preference, systemDark]);

  const cycle = useCallback(() => {
    const next = THEME_ORDER[(THEME_ORDER.indexOf(preference) + 1) % THEME_ORDER.length];
    setPreference(next ?? 'system');
  }, [preference, setPreference]);

  const resolved = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference;
  return { preference, resolved, cycle };
}
