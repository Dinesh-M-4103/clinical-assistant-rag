import { describe, expect, it } from 'vitest';
import { formatBytes, formatMs, initials, pluralize } from './format';

describe('format helpers', () => {
  it('builds initials from first and last name, skipping honorifics', () => {
    expect(initials('Asha Verma')).toBe('AV');
    expect(initials('Dr. Rohan K. Mehta')).toBe('RM');
    expect(initials('Priya')).toBe('P');
  });

  it('formats byte sizes', () => {
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(48_213)).toBe('47 KB');
    expect(formatBytes(3.5 * 1024 * 1024)).toBe('3.5 MB');
  });

  it('formats durations', () => {
    expect(formatMs(212.4)).toBe('212 ms');
    expect(formatMs(1768)).toBe('1.8 s');
  });

  it('pluralizes counts', () => {
    expect(pluralize(1, 'report')).toBe('1 report');
    expect(pluralize(3, 'report')).toBe('3 reports');
  });
});
