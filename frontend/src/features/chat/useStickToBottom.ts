import { useCallback, useLayoutEffect, useRef, useState } from 'react';

const NEAR_BOTTOM_PX = 80;

/**
 * Keeps a scroll container pinned to the newest content while the user is at the bottom, and
 * stops following as soon as they scroll up to read — so streaming never fights the reader.
 */
export function useStickToBottom<T extends HTMLElement>(trigger: unknown) {
  const ref = useRef<T>(null);
  const stuck = useRef(true);
  const [away, setAway] = useState(false);

  const onScroll = useCallback(() => {
    const element = ref.current;
    if (!element) return;
    const nearBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight < NEAR_BOTTOM_PX;
    stuck.current = nearBottom;
    setAway(!nearBottom);
  }, []);

  useLayoutEffect(() => {
    const element = ref.current;
    if (element && stuck.current) element.scrollTop = element.scrollHeight;
  }, [trigger]);

  const scrollToBottom = useCallback(() => {
    stuck.current = true;
    setAway(false);
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' });
  }, []);

  return { ref, onScroll, away, scrollToBottom };
}
