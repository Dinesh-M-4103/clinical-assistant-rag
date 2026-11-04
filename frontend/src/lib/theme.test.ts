import { afterEach, describe, expect, it, vi } from 'vitest';
import { applyTheme, readStoredTheme, storeTheme } from './theme';

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
  document.documentElement.classList.remove('dark');
});

describe('theme persistence', () => {
  it('round-trips an explicit choice and clears the key for "system"', () => {
    storeTheme('dark');
    expect(readStoredTheme()).toBe('dark');
    storeTheme('system');
    expect(localStorage.getItem('clinical-assistant:theme')).toBeNull();
    expect(readStoredTheme()).toBe('system');
  });

  it('ignores unknown stored values', () => {
    localStorage.setItem('clinical-assistant:theme', 'sepia');
    expect(readStoredTheme()).toBe('system');
  });

  it('survives blocked storage', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    expect(readStoredTheme()).toBe('system');
    expect(() => storeTheme('dark')).not.toThrow();
  });
});

describe('applyTheme', () => {
  it('toggles the dark class on <html>', () => {
    applyTheme('dark');
    expect(document.documentElement).toHaveClass('dark');
    applyTheme('light');
    expect(document.documentElement).not.toHaveClass('dark');
  });
});
