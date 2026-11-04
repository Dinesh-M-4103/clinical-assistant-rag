const MIN_ITEM_CHARS = 6;

const normalise = (text: string) =>
  text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();

/**
 * Best-effort mapping from a cited chunk to the PDF.js text-layer items it covers. A text item is
 * highlighted when its whole (normalised) text appears in the chunk on word boundaries; items
 * shorter than a few characters are skipped because they would match almost anywhere.
 */
export function findHighlightedItems(items: readonly string[], chunkText: string): Set<number> {
  const haystack = ` ${normalise(chunkText)} `;
  const matches = new Set<number>();
  items.forEach((item, index) => {
    const needle = normalise(item);
    if (needle.length >= MIN_ITEM_CHARS && haystack.includes(` ${needle} `)) matches.add(index);
  });
  return matches;
}
