import type { Category } from '@/api/schemas';

export const CATEGORY_LABELS: Record<Category, string> = {
  lab: 'Lab',
  imaging: 'Imaging',
  discharge: 'Discharge',
  prescription: 'Prescription',
  consultation: 'Consultation',
  other: 'Other',
};

/** Badge tint per category; every pair keeps AA contrast in both themes. */
export const CATEGORY_TONES: Record<Category, string> = {
  lab: 'bg-primary-soft text-primary-text',
  imaging: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
  discharge: 'bg-warning-soft text-warning',
  prescription: 'bg-success-soft text-success',
  consultation: 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300',
  other: 'bg-subtle text-muted',
};
