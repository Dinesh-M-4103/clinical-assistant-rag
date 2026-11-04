import { useSyncExternalStore } from 'react';

export type Breakpoint = 'mobile' | 'tablet' | 'desktop';

const TABLET_QUERY = '(min-width: 768px)';
const DESKTOP_QUERY = '(min-width: 1280px)';

function subscribe(onChange: () => void): () => void {
  const queries = [TABLET_QUERY, DESKTOP_QUERY].map((query) => window.matchMedia(query));
  queries.forEach((query) => query.addEventListener('change', onChange));
  return () => queries.forEach((query) => query.removeEventListener('change', onChange));
}

function snapshot(): Breakpoint {
  if (window.matchMedia(DESKTOP_QUERY).matches) return 'desktop';
  return window.matchMedia(TABLET_QUERY).matches ? 'tablet' : 'mobile';
}

/** Matches Tailwind's `md` (768px) and `xl` (1280px); used to pick one layout instead of hiding two. */
export function useBreakpoint(): Breakpoint {
  return useSyncExternalStore(subscribe, snapshot);
}
