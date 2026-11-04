import { describe, expect, it } from 'vitest';
import { findHighlightedItems } from './highlight';

const CHUNK =
  'Laboratory Results. HbA1c 7.8 % (reference 4.0 - 5.6 %) collected 12 Sep 2026. Fasting plasma glucose 148 mg/dL.';

describe('findHighlightedItems', () => {
  it('highlights text items that appear inside the cited chunk', () => {
    const items = [
      'Laboratory Report',
      'HbA1c 7.8 % (reference 4.0 - 5.6 %) collected 12 Sep 2026',
      'Fasting plasma glucose 148 mg/dL',
      'Lipid Profile',
    ];
    expect([...findHighlightedItems(items, CHUNK)]).toEqual([1, 2]);
  });

  it('ignores punctuation and case differences', () => {
    expect([...findHighlightedItems(['FASTING   plasma glucose, 148 mg/dL'], CHUNK)]).toEqual([0]);
  });

  it('skips short fragments that would match anywhere', () => {
    expect(findHighlightedItems(['148', 'mg', ' '], CHUNK).size).toBe(0);
  });

  it('only matches on whole-word boundaries', () => {
    expect(findHighlightedItems(['plasma gluc'], CHUNK).size).toBe(0);
  });
});
