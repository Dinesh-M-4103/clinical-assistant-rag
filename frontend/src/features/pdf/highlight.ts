const MIN_ANCHOR_CHARS = 6;

const normalise = (text: string) =>
  text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();

/**
 * Best-effort mapping from a cited chunk to the PDF.js text-layer items it covers. Items whose
 * whole (normalised) text appears in the chunk on word boundaries and is at least a few characters
 * long are anchors. Shorter cells such as "8.6 %" or "H" would match almost anywhere on their own,
 * so they are only highlighted when they continue an unbroken run of in-chunk items from an anchor,
 * which keeps table rows highlighted as a whole.
 */
export function findHighlightedItems(items: readonly string[], chunkText: string): Set<number> {
  const haystack = ` ${normalise(chunkText)} `;
  const needles = items.map(normalise);
  const inChunk = (needle: string) => haystack.includes(` ${needle} `);

  const matches = new Set<number>();
  needles.forEach((needle, index) => {
    if (needle.length >= MIN_ANCHOR_CHARS && inChunk(needle)) matches.add(index);
  });

  const anchors = [...matches];
  const extend = (from: number, step: 1 | -1) => {
    for (let i = from + step; i >= 0 && i < needles.length; i += step) {
      const needle = needles[i];
      if (!needle) continue;
      if (!inChunk(needle)) return;
      matches.add(i);
    }
  };
  anchors.forEach((index) => {
    extend(index, 1);
    extend(index, -1);
  });
  return matches;
}
