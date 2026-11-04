/**
 * The model cites sources as `[C1]` or `[C1, C2]`. Before rendering, those markers become
 * markdown links with a private `cite:` scheme, which the renderer swaps for citation chips.
 * Going through markdown (rather than raw HTML) keeps the output sanitised by construction.
 */

const MARKER = /\[(C\d+(?:\s*,\s*C\d+)*)\]/g;
const SCHEME = 'cite:';

export function linkifyCitations(markdown: string): string {
  return markdown.replace(MARKER, (_match, ids: string) =>
    ids
      .split(/\s*,\s*/)
      .map((id) => `[${id}](${SCHEME}${id})`)
      .join(' '),
  );
}

/** Returns the citation id (e.g. "C1") encoded in a link produced by `linkifyCitations`. */
export function citationIdFromHref(href: string | undefined): string | null {
  return href?.startsWith(SCHEME) ? href.slice(SCHEME.length) : null;
}

export function isCitationHref(href: string): boolean {
  return href.startsWith(SCHEME);
}
