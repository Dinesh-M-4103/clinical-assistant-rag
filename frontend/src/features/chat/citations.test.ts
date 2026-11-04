import { describe, expect, it } from 'vitest';
import { citationIdFromHref, linkifyCitations } from './citations';

describe('linkifyCitations', () => {
  it('turns a [C1] marker into a cite: link', () => {
    expect(linkifyCitations('HbA1c is 7.8 % [C1].')).toBe('HbA1c is 7.8 % [C1](cite:C1).');
  });

  it('expands grouped markers into one link per id', () => {
    expect(linkifyCitations('See [C1, C3].')).toBe('See [C1](cite:C1) [C3](cite:C3).');
  });

  it('handles adjacent markers and multi-digit ids', () => {
    expect(linkifyCitations('x [C2][C10]')).toBe('x [C2](cite:C2)[C10](cite:C10)');
  });

  it('leaves ordinary brackets and markdown links alone', () => {
    const text = 'Range [normal] and [docs](https://example.com) and [Chapter 1].';
    expect(linkifyCitations(text)).toBe(text);
  });
});

describe('citationIdFromHref', () => {
  it('extracts the id from cite: links only', () => {
    expect(citationIdFromHref('cite:C4')).toBe('C4');
    expect(citationIdFromHref('https://example.com')).toBeNull();
    expect(citationIdFromHref(undefined)).toBeNull();
  });
});
